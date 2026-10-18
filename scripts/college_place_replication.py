"""Replication of the place (distance-decay) factor on college programs (open item 4 in output/verdict.json).

The distance factor was estimated on pro teams (NFL, MLB, NBA). Here the same idea is tested on a different population:
college schools (FBS programs plus the few other schools with meaningful attention), measured at the school level
('<School> sucks' searches, one scale via the bridge batches).

    E[v[s,u]] = exp(kappa_s + psi_u - gamma * miles(s, school u's home state) / 1000) * (th0 + Hm[s,u])
    Hm[s,u]   = model-implied hostility from state s toward school u, summed over all of the school's sports (A R)

kappa_s absorbs state search levels, psi_u each school's baseline unpopularity. Own-state schools (embodiment >= 0.2) are excluded.
Cluster bootstrap over states. Nothing here feeds the model.
Writes data/model/college_place_replication.csv and docs/COLLEGE_PLACE_REPLICATION.md.

    python scripts/college_place_replication.py [bootstrap_draws]
"""
import csv
import math
import pathlib
import sys

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import lib_measured as LMS  # noqa: E402
import lib_model as LM  # noqa: E402
import lib_trends as L  # noqa: E402
from gravity_distance import haversine  # noqa: E402

ROOT = LM.ROOT
SUFFIXES = (" Men's Basketball", " Women's Basketball", " Men's Ice Hockey", " Women's Ice Hockey", " Baseball", " Softball",
            " Women's Volleyball", " Men's Lacrosse", " Women's Lacrosse", " Wrestling")


def fit(v, Hm, d, w, ns, nu, si, uj):
    def fun(p):
        kap, psi = p[:ns], p[ns:ns + nu]
        th0, gam = math.exp(p[ns + nu]), p[ns + nu + 1]
        g = th0 + Hm
        base = np.exp(kap[si] + psi[uj] - gam * d)
        mu = base * g
        loss = np.sum(w * (mu - v * np.log(np.maximum(mu, 1e-300)))) + 1e-4 * (np.sum(kap ** 2) + np.sum(psi ** 2))
        r = w * (mu - v)
        gk = np.bincount(si, weights=r, minlength=ns) + 2e-4 * kap
        gp = np.bincount(uj, weights=r, minlength=nu) + 2e-4 * psi
        return loss, np.concatenate([gk, gp, [np.sum(r * th0 / g), np.sum(-r * d)]])
    p0 = np.concatenate([np.zeros(ns + nu), [math.log(np.median(Hm[Hm > 0]) if (Hm > 0).any() else 0.01), 0.0]])
    res = minimize(fun, p0, jac=True, method="L-BFGS-B", options={"maxiter": 500})
    return float(res.x[-1]), bool(res.success)


def main(n_boot=100, seed=11):
    states, ids, A, _ = LM.load_A()
    sidx = {s: k for k, s in enumerate(states)}
    eidx = {e: k for k, e in enumerate(ids)}
    reg = {e["entity_id"]: e for e in LM.load_entities()}
    ents = [reg[e] for e in ids]
    E, buckets = LM.build_E(ents, states)
    bidx = {b: k for k, b in enumerate(buckets)}
    R = LM.build_R(ids, [e for e in LM.build_edges() if e[0] != "UNRESOLVED"])
    smap = L.state_map()
    out = LMS.measurements(smap, reg)
    if out is None:
        print("bridges not ready")
        return
    v, unit_name, school_of_cfb = out
    cen = {r["state_id"]: (float(r["lat"]), float(r["lon"])) for r in csv.DictReader(open(ROOT / "config/state_centroids.csv", encoding="utf-8"))}
    members = {}
    for eid in ids:
        e = reg[eid]
        if e["professional_college"] != "college":
            continue
        if eid.startswith("cfb_"):
            u = "sch:" + school_of_cfb.get(eid, "")
        else:
            u = next(("sch:" + e["entity_name"][:-len(s)] for s in SUFFIXES if e["entity_name"].endswith(s)), None)
        if u:
            members.setdefault(u, []).append(eid)
    AR = A @ R
    units = sorted(u for u in members if u.startswith("sch:") and any((s, u) in v for s in smap.values()))
    uix = {u: k for k, u in enumerate(units)}
    cells = []
    for u in units:
        mem = members[u]
        hs = reg[mem[0]]["home_state"]
        if hs not in cen:
            continue
        for sid in smap.values():
            if (sid, u) not in v or max(E[eidx[m], bidx[sid]] for m in mem) >= 0.2:
                continue
            hm = float(sum(AR[sidx[sid], eidx[m]] for m in mem))
            cells.append((sidx[sid], uix[u], v[(sid, u)], hm, haversine(cen[sid], cen[hs]) / 1000.0))
    si = np.array([c[0] for c in cells]); uj = np.array([c[1] for c in cells]); vv = np.array([c[2] for c in cells])
    Hm = np.array([c[3] for c in cells]); d = np.array([c[4] for c in cells])
    vv = vv / np.median(vv)
    Hm = Hm / np.median(Hm[Hm > 0])
    used = sorted(set(si)); remap = {s: k for k, s in enumerate(used)}; si2 = np.array([remap[s] for s in si]); ns, nu = len(used), len(units)
    gam, ok = fit(vv, Hm, d, np.ones(len(vv)), ns, nu, si2, uj)
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_boot):
        w = np.bincount(rng.integers(0, ns, ns), minlength=ns).astype(float)[si2]
        try:
            g_b, ok_b = fit(vv, Hm, d, w, ns, nu, si2, uj)
            if ok_b:
                boots.append(g_b)
        except Exception:
            pass
    lo, hi = np.percentile(boots, [5, 95])
    row = {"population": "college schools (school-level)", "cells": len(vv), "schools": nu, "gamma_per_1000mi": round(gam, 3), "gamma_lo": round(float(lo), 3), "gamma_hi": round(float(hi), 3),
           "shrink_per_1000mi": round(math.exp(-gam), 3), "shrink_lo": round(math.exp(-hi), 3), "shrink_hi": round(math.exp(-lo), 3), "converged": ok}
    print(row)
    with open(ROOT / "data/model/college_place_replication.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(row), lineterminator=chr(10))
        w.writeheader()
        w.writerow(row)
    md = ["# Replication of the distance factor on college programs", "",
          "Auto-generated by `scripts/college_place_replication.py`. The distance factor was estimated on pro teams (NFL 0.70, MLB 0.73, NBA 0.89 per 1,000 miles). "
          "Here it is re-estimated on a different population: college schools, measured at the school level, with the model's hostility summed over each school's sports.", "",
          f"**College schools: antipathy shrinks to {row['shrink_per_1000mi']:.2f} per 1,000 miles (90% interval {row['shrink_lo']:.2f} to {row['shrink_hi']:.2f}); {row['cells']} cells, {row['schools']} schools.**", "",
          "Replication standard (fixed in advance): the interval excludes 1.00 (no decay) and overlaps the pro-team range (0.63 to 0.96 across leagues). "
          "Caveats: distance uses state centroids and the school's home state; school-level terms ('Michigan sucks') cannot separate sports; small-state zeros are censored."]
    (ROOT / "docs/COLLEGE_PLACE_REPLICATION.md").write_text(chr(10).join(md) + chr(10), encoding="utf-8", newline=chr(10))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 100)
