"""Measured channel decomposition for the top pairs (design: docs/RIVALRY_WEIGHT_DESIGN.md, sections 2, 4 and 7).

Question: for state a's hostility toward state b, what share is aimed at each *unit* that embodies b (a pro team or a college school)?
Terms like "Michigan sucks" are school-level, so the measured side is by school and the model side is summed over all of that school's sports.

    v[a, u]    interest in state a for unit u, in Cowboys-suck units per state (two-term bridge batches), with its estimated variance
    censored   cells below detection are NOT dropped and NOT set to zero: they enter at the estimator's floor (an upper bound on the true
               interest), and the share of the top unit is bounded: lower bound = censored cells at their floor, upper bound = censored cells at zero
    interval   5th percentile of the share with censored cells at their floor, to 95th percentile with censored cells at zero, over 400
               draws of the measurement noise (cell variance plus bridge variance)
    raw        shares of v;  excess = shares after dividing each unit by its typical level in other states (removes ambient unpopularity)
    model      the model's contribution via each unit (A R F E, summed over the unit's sports), over the same units, renormalised

Supported (rule from the design note, applied to BOTH the raw and the excess measure; the stricter of the two decides): the model's share
lies inside the measured interval or within 15 points of the central measured share. A direction is *testable* only with at least 3 measured
units covering at least 80% of the model's mass for that direction; otherwise the result is "inconclusive", never "supported".
The share compared is the share carried by the target UNIT (for IL->WI the Packers, whatever rival supplies the hostility), which is the
same quantity on both sides. Nothing here feeds the model.
Writes data/model/channel_decomposition.csv and docs/CHANNEL_DECOMPOSITION.md.

    python scripts/channel_decomposition.py [top_n_pairs]
"""
import csv
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import lib_measured as LMS  # noqa: E402
import lib_model as LM  # noqa: E402
import lib_trends as L  # noqa: E402

ROOT = LM.ROOT
SUFFIXES = (" Men's Basketball", " Women's Basketball", " Men's Ice Hockey", " Women's Ice Hockey", " Baseball", " Softball",
            " Women's Volleyball", " Men's Lacrosse", " Women's Lacrosse", " Wrestling")
TOL = 0.15
N_DRAW = 400


def share_interval(units, vals, var, cens, top, ambient, rng):
    """(central, lo, hi) of the share of unit `top` among `units`.
    A censored (below-detection) cell carries the estimator's floor, the midpoint of the detection cell, so its true value lies in [0, 2 x floor].
    Lower bound of the top unit's share: the top unit at 0 if censored, every other censored unit at 2 x floor. Upper bound: the top unit at 2 x floor if
    censored, every other censored unit at 0. Detected cells get measurement noise (their estimated variance); censored cells are bounded, not perturbed."""
    x = np.array([vals[u] for u in units])
    if ambient is not None:
        x = x / np.array([ambient[u] for u in units])
    c = np.array([cens[u] for u in units])
    sd = np.sqrt(np.array([var[u] for u in units]))
    k = units.index(top)
    central = x[k] / x.sum()
    d = x[None, :] * np.where(c[None, :], 1.0, np.exp(rng.standard_normal((N_DRAW, len(units))) * sd[None, :]))
    lo_v = d.copy()
    lo_v[:, c] = 2.0 * x[c][None, :]
    hi_v = d.copy()
    hi_v[:, c] = 0.0
    if c[k]:
        lo_v[:, k] = 0.0
        hi_v[:, k] = 2.0 * x[k]
    lo = np.divide(lo_v[:, k], lo_v.sum(1), out=np.zeros(N_DRAW), where=lo_v.sum(1) > 0)
    hi = np.divide(hi_v[:, k], hi_v.sum(1), out=np.zeros(N_DRAW), where=hi_v.sum(1) > 0)
    return float(central), float(np.percentile(lo, 5)), float(np.percentile(hi, 95))


def main(top_n=30, seed=17):
    states, ids, A, _ = LM.load_A()
    sidx = {s: k for k, s in enumerate(states)}
    eidx = {e: k for k, e in enumerate(ids)}
    reg = {e["entity_id"]: e for e in LM.load_entities()}
    ents = [reg[e] for e in ids]
    E, buckets = LM.build_E(ents, states)
    bidx = {b: k for k, b in enumerate(buckets)}
    R = LM.build_R(ids, [e for e in LM.build_edges() if e[0] != "UNRESOLVED"])
    F = LM.place_matrix(states, ids, ents)
    AR = (A @ R) * F
    smap = L.state_map()
    out = LMS.measurements_full(smap, reg)
    if out is None:
        print("bridges not finished yet")
        return
    full, unit_name, school_of_cfb = out
    if not full:
        print("no measurements")
        return
    rng = np.random.default_rng(seed)

    def unit_of(eid):
        e = reg[eid]
        if e["professional_college"] != "college":
            return "pro:" + eid
        if eid.startswith("cfb_"):
            return "sch:" + school_of_cfb.get(eid, "")
        n = e["entity_name"]
        for suf in SUFFIXES:
            if n.endswith(suf):
                return "sch:" + n[:-len(suf)]
        return None

    members = {}
    for eid in ids:
        u = unit_of(eid)
        if u:
            members.setdefault(u, []).append(eid)
    by_u = {}
    for (sid, u), (x, _, c) in full.items():
        if not c:
            by_u.setdefault(u, []).append(x)
    amb = {u: float(np.median(xs)) for u, xs in by_u.items() if len(xs) >= 10}

    ps = list(csv.DictReader(open(ROOT / "data/model/pair_scores.csv", encoding="utf-8")))[:top_n]
    rows = []
    for p in ps:
        for a, b in ((p["state_a"], p["state_b"]), (p["state_b"], p["state_a"])):
            vals, var, cens, model_meas, model_all = {}, {}, {}, {}, {}
            for u, mem in members.items():
                if not any(E[eidx[m], bidx[b]] >= 0.2 for m in mem):
                    continue
                contrib = sum(float(AR[sidx[a], eidx[m]] * E[eidx[m], bidx[b]]) for m in mem)
                model_all[u] = contrib
                if (a, u) in full:
                    vals[u], var[u], cens[u] = full[(a, u)]
                    model_meas[u] = contrib
            if len(vals) < 2 or sum(model_meas.values()) <= 0:
                continue
            units = sorted(vals)
            tot_m = sum(model_meas.values())
            top = max(model_meas, key=model_meas.get)
            c = model_meas[top] / tot_m
            tot_all = sum(model_all.values()) or 1.0
            cov = tot_m / tot_all
            det_units = [u for u in units if not cens[u]]
            det_cov = sum(model_meas[u] for u in det_units) / tot_all
            raw = share_interval(units, vals, var, cens, top, None, rng)
            # excess measure: only units with an ambient level; the MODEL share is recomputed over exactly those units (same denominator on both sides)
            ex_units = [u for u in units if u in amb]
            ex_ok = top in amb and len(ex_units) >= 2 and sum(model_meas[u] for u in ex_units) / tot_m >= 0.8
            exc = share_interval(ex_units, vals, var, cens, top, amb, rng) if ex_ok else None
            c_ex = model_meas[top] / sum(model_meas[u] for u in ex_units) if ex_ok else None
            testable = len(det_units) >= 3 and det_cov >= 0.8
            ok = lambda r, cc: (r is not None) and ((r[1] <= cc <= r[2]) or abs(r[0] - cc) <= TOL)
            sup_raw, sup_exc = ok(raw, c), (ok(exc, c_ex) if exc else False)
            if not testable:
                verdict = "inconclusive (too few detected units or low detected coverage)"
            elif exc is None:
                verdict = "inconclusive (corrected measure lacks comparable units)"
            else:
                verdict = "supported" if (sup_raw and sup_exc) else ("supported on raw only" if sup_raw else ("model too high" if c > raw[0] else "model too low"))
            rows.append({"pair_rank": p["rank"], "direction": f"{a}->{b}", "units_measured": len(units),
                         "censored_units": sum(cens.values()), "model_coverage": round(cov, 2), "detected_units": len(det_units), "detected_coverage": round(det_cov, 2), "testable": testable,
                         "model_top_unit": unit_name.get(top, top), "model_top_share": round(c, 3),
                         "measured_share_of_that_unit": round(raw[0], 3), "raw_lo": round(raw[1], 3), "raw_hi": round(raw[2], 3),
                         "model_share_excess_basis": round(c_ex, 3) if exc else "", "excess_share_of_that_unit": round(exc[0], 3) if exc else "", "excess_lo": round(exc[1], 3) if exc else "", "excess_hi": round(exc[2], 3) if exc else "",
                         "supported_raw": sup_raw, "supported_excess": sup_exc, "verdict": verdict,
                         "measured_top_unit": unit_name.get(max(vals, key=vals.get), ""), "measured_top_share": round(max(vals.values()) / sum(vals.values()), 3)})
    with open(ROOT / "data/model/channel_decomposition.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator=chr(10))
        w.writeheader()
        w.writerows(rows)
    n_t = sum(1 for r in rows if r["testable"])
    n_ok = sum(1 for r in rows if r["verdict"] == "supported")
    md = ["# Measured channel decomposition (top pairs)", "",
          "Auto-generated by `scripts/channel_decomposition.py`. For each direction of the top pairs: the model's biggest channel (a pro team or a college school, summed over all of its sports) "
          "and its share of the direction's hostility, versus the share of measured antipathy ('<team> suck' searches) that the same unit receives among the units embodying the target state. "
          "Censored (below-detection) cells are kept at their floor and bounded, never dropped or set to zero; intervals include measurement noise.", "",
          f"**Rule:** supported if the model share lies inside the measured interval or within 15 points of the central measured share, on both the raw and the ambient-corrected measure; "
          f"testable only with at least 3 DETECTED (not censored) units covering at least 80% of the model's mass. The ambient-corrected comparison is made against the model share over exactly the same units. **{n_ok} of {n_t} testable directions are supported** ({len(rows)} directions computed).", "",
          "| Pair rank | Direction | Model's top channel | Model share (corrected basis) | Raw measured (interval) | Excess measured (interval) | Verdict | Units (censored) | Detected coverage |", "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        ex = (f"{r['excess_share_of_that_unit']:.0%} ({r['excess_lo']:.0%} to {r['excess_hi']:.0%})") if r['excess_share_of_that_unit'] != '' else 'n/a'
        md.append(f"| {r['pair_rank']} | {r['direction']} | {r['model_top_unit']} | {r['model_top_share']:.0%}{(' (' + format(r['model_share_excess_basis'], '.0%') + ')') if r['model_share_excess_basis'] != '' else ''} | {r['measured_share_of_that_unit']:.0%} ({r['raw_lo']:.0%} to {r['raw_hi']:.0%}) | {ex} | {r['verdict']} | {r['units_measured']} ({r['censored_units']}) | {r['detected_coverage']:.0%} |")
    md += ["", "Caveats: search is not hostility; the censored-cell bound is wide for small states (that is why some directions are inconclusive); school-level terms cannot separate sports within a school; "
           "the ambient correction assumes a unit is hated about equally in other states; the compared share is the share carried by the target unit, not by one rival edge."]
    (ROOT / "docs/CHANNEL_DECOMPOSITION.md").write_text(chr(10).join(md) + chr(10), encoding="utf-8", newline=chr(10))
    print(chr(10).join(md[4:9]))
    for r in rows[:2]:
        print(r["direction"], r["model_top_share"], r["measured_share_of_that_unit"], r["raw_lo"], r["raw_hi"], r["excess_share_of_that_unit"], r["excess_lo"], r["excess_hi"], r["verdict"], r["units_measured"], r["censored_units"], r["model_coverage"])


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 30)
