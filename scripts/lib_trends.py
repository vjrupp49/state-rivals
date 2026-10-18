"""Shared estimation core for anchored Google Trends batches.

Each job = one interest_by_region request: for every state, 5 integer percent
shares (sum ~100). Terms 0 and 1 are anchors present in every batch. Within a
state, share ratios between terms are batch-invariant, so every other term is
expressed in 'units of anchor A1' via A1 directly and via A2 (scaled by the
A2/A1 ratio estimated across all batches of that window). Inverse-variance
combination uses rounding noise (+-0.5 on integer percents). Zeros are
censored (below detection), never treated as true zero (D-007).
"""
import json
import math
import os
import pathlib
import sqlite3
import csv
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
from paths import WORK
DB = WORK / "trends.sqlite"
WINDOW_AGE = {"W0": (0, 12), "W1": (12, 24), "W2": (24, 36), "W3": (36, 60)}
HALF_LIFE = 24.0


def window_weights():
    w = {}
    for k, (t0, t1) in WINDOW_AGE.items():
        w[k] = (HALF_LIFE / math.log(2)) * (2 ** (-t0 / HALF_LIFE) - 2 ** (-t1 / HALF_LIFE))
    s = sum(w.values())
    return {k: v / s for k, v in w.items()}


def state_map():
    m = {}
    with open(ROOT / "data" / "registries" / "states.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["is_contest_state"] == "TRUE":
                m[r["state_name"]] = r["state_id"]
    return m


SKIPPED = {"misaligned": 0, "anchor_dropped": 0}


def load_jobs(family=None, kind=None):
    """Load OK jobs, realigning payload columns to planned entities BY TERM (Google sometimes drops a
    term from the response). A batch that lost either anchor is skipped; a lost non-anchor term simply
    yields no estimate for that entity in that batch."""
    con = sqlite3.connect(DB, timeout=60)
    q = "SELECT family,kind,win,terms,columns,payload FROM jobs WHERE status='ok'"
    args = []
    if family:
        q += " AND family=?"
        args.append(family)
    out = []
    SKIPPED["misaligned"] = SKIPPED["anchor_dropped"] = 0
    for fam, kd, win, terms, cols, payload in con.execute(q, args):
        p = json.loads(payload)
        planned_terms = json.loads(terms)
        planned_ids = json.loads(cols)
        term_to_id = dict(zip(planned_terms, planned_ids))
        ret = p["columns"]
        names = [term_to_id.get(c) for c in ret]
        if ret != planned_terms:
            SKIPPED["misaligned"] += 1
        if None in names or len(names) < 2 or names[0] != planned_ids[0] or names[1] != planned_ids[1]:
            SKIPPED["anchor_dropped"] += 1
            continue
        out.append({"family": fam, "kind": kd, "win": win, "names": names, "rows": p["rows"]})
    con.close()
    return out


def _rvar(a, b):
    return max((0.5 / max(a, 0.5)) ** 2 + (0.5 / max(b, 0.5)) ** 2, 0.0025)


def estimate(jobs, smap):
    """Return est[(name, state_id, win)] = (ln_r, var, flag). r in units of A1."""
    est_lists = defaultdict(list)  # (name,state,win) -> [(lnr,var,flag)]
    by_win = defaultdict(list)
    for j in jobs:
        by_win[j["win"]].append(j)
    for win, js in by_win.items():
        for sname, sid in smap.items():
            # A2/A1 ratio for this state/window across batches
            num = den = 0.0
            for j in js:
                v = j["rows"].get(sname)
                if not v or v[0] < 3 or v[1] < 3:
                    continue
                var = _rvar(v[0], v[1])
                num += math.log(v[1] / v[0]) / var
                den += 1 / var
            ln_rho = num / den if den else None
            for j in js:
                v = j["rows"].get(sname)
                if not v:
                    continue
                n = j["names"]
                if (n[0], sid, win) not in est_lists:
                    est_lists[(n[0], sid, win)].append((0.0, 0.0025, "anchor"))
                if ln_rho is not None and (n[1], sid, win) not in est_lists:
                    est_lists[(n[1], sid, win)].append((ln_rho, 0.0025, "anchor"))
                for idx in range(2, len(n)):
                    x = v[idx]
                    cands = []
                    for a_idx, shift in ((0, 0.0), (1, ln_rho)):
                        a = v[a_idx]
                        if a < 1 or shift is None:
                            continue
                        if x >= 1:
                            cands.append((math.log(x / a) + shift, _rvar(x, a), "ok" if a >= 3 else "low_anchor"))
                        else:
                            cands.append((math.log(0.25 / a) + shift, 1.0, "below_detection"))
                    if not cands:
                        continue
                    est_lists[(n[idx], sid, win)].extend(cands)
    est = {}
    for key, lst in est_lists.items():
        good = [c for c in lst if c[2] in ("ok", "anchor")]
        use = lst            # censored candidates enter with their large variance (D-007: censored is information, not zero)
        sw = sum(1 / c[1] for c in use) if all(c[1] > 0 for c in use) else None
        if sw is None:
            est[key] = (0.0, 0.0025, "anchor")
            continue
        ln = sum(c[0] / c[1] for c in use) / sw
        flag = "anchor" if all(c[2] == "anchor" for c in use) else (
            "ok" if good else ("below_detection" if all(c[2] == "below_detection" for c in use) else "low_anchor"))
        est[key] = (ln, 1 / sw, flag)
    return est


def blend_windows(est, name, sid):
    """Return dict with G_C (W0 r), G_P (half-life blend of r), var_C, flag_C."""
    wts = window_weights()
    e0 = est.get((name, sid, "W0"))
    num = den = 0.0
    for win, w in wts.items():
        e = est.get((name, sid, win))
        if e:
            num += w * math.exp(e[0])
            den += w
    gp = num / den if den else None
    if gp is None or not any(est.get((name, sid, w)) for w in ("W1", "W2", "W3")):
        e5 = est.get((name, sid, "W5"))
        if e5:   # tier-B families: 5-year aggregate stands in for the recency-weighted baseline (approximation)
            gp = math.exp(e5[0])
    gc = math.exp(e0[0]) if e0 else None
    return {"G_C": gc, "G_P": gp, "var_C": e0[1] if e0 else None, "flag_C": e0[2] if e0 else "missing"}
