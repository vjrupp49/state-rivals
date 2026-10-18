"""Gravity-style calibration of the rivalry tier ladder from antipathy searches (design: docs/RIVALRY_WEIGHT_DESIGN.md, section 4).

Measured: v[s, j], interest in "<team j> suck" in state s, in units of the batch anchor in the SAME state, own-state teams
excluded (the model ignores in-state hostility). Model: residents of s feel hostility toward j through the teams they follow
that rival j. For each tier t of rivalry, X_t[s, j] = sum over teams i with a tier-t rivalry edge i -> j of A[s, i] (attention).
Estimated model (Poisson pseudo-maximum likelihood, keeps zeros out only where Trends reports "below detection"):

    E[v[s,j]] = exp(kappa_s + psi_j) * ( th0 + X_1 + th2 * X_2 + th3 * X_3 )

kappa_s absorbs each state's overall search level and anchor scale, psi_j each team's ambient unpopularity. th2 and th3 are the
weights of tier-2 and tier-3 rivalries relative to tier 1; th0 is a generic-dislike floor. The analyst prior (S times T per tier:
0.34, 0.13, 0.036) implies th2 = 0.38, th3 = 0.106. Confidence intervals: bootstrap over states (a cluster bootstrap).

Nothing here feeds the model. It reports whether the prior ladder is too steep or too flat.
Writes data/model/gravity_calibration.csv and docs/GRAVITY_CALIBRATION.md.

    python scripts/gravity_calibration.py [bootstrap_draws]
"""
import csv
import math
import pathlib
import sys

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import lib_model as LM  # noqa: E402
import lib_trends as L  # noqa: E402
import trends_worker as TW  # noqa: E402

ROOT = LM.ROOT
PRIOR = {2: 0.2 * 0.65 / (0.4 * 0.85), 3: 0.08 * 0.45 / (0.4 * 0.85)}


def fit(v, X1, X2, X3, w, ns, nt, si, tj):
    """v, X*, w: flat arrays over cells; si, tj: state and team index per cell. Returns (th0, th2, th3, converged)."""
    def unpack(p):
        return p[:ns], p[ns:ns + nt], np.exp(p[ns + nt:ns + nt + 3])

    def fun(p):
        kap, psi, th = unpack(p)
        g = th[0] + X1 + th[1] * X2 + th[2] * X3
        base = np.exp(kap[si] + psi[tj])
        mu = base * g
        loss = np.sum(w * (mu - v * np.log(np.maximum(mu, 1e-300)))) + 1e-4 * (np.sum(kap ** 2) + np.sum(psi ** 2))
        r = w * (mu - v)
        gk = np.bincount(si, weights=r, minlength=ns) + 2e-4 * kap
        gp = np.bincount(tj, weights=r, minlength=nt) + 2e-4 * psi
        gt = np.array([np.sum(r * th[0] / g), np.sum(r * th[1] * X2 / g), np.sum(r * th[2] * X3 / g)])
        return loss, np.concatenate([gk, gp, gt])

    p0 = np.concatenate([np.zeros(ns), np.zeros(nt), np.log([0.05, PRIOR[2], PRIOR[3]])])
    res = minimize(fun, p0, jac=True, method="L-BFGS-B", options={"maxiter": 400})
    th = np.exp(res.x[ns + nt:])
    return th, bool(res.success)


def main(n_boot=150, seed=3):
    states, ids, A, _ = LM.load_A()
    sidx = {s: k for k, s in enumerate(states)}
    eidx = {e: k for k, e in enumerate(ids)}
    reg = {e["entity_id"]: e for e in LM.load_entities()}
    ents = [reg[e] for e in ids]
    E, buckets = LM.build_E(ents, states)
    bidx = {b: k for k, b in enumerate(buckets)}
    edges = [e for e in LM.build_edges() if e[0] != "UNRESOLVED"]
    smap = L.state_map()
    rng = np.random.default_rng(seed)
    rows, md_rows = [], []
    for league in ("nfl", "mlb", "nba", "nhl"):
        jobs = L.load_jobs(family=f"HATE_{league}")
        if not jobs:
            continue
        est = L.estimate(jobs, smap)
        terms = TW._hate_terms(league)
        teams = sorted(terms)
        tix = {t: k for k, t in enumerate(teams)}
        # tier attention matrices: Xt[s, j] = sum_i A[s,i] * 1[edge i->j tier t]
        T = {1: np.zeros((len(states), len(teams))), 2: np.zeros((len(states), len(teams))), 3: np.zeros((len(states), len(teams)))}
        for i, j, fam, tier, _, _ in edges:
            if fam == league and j in tix and tier in T:
                T[tier][:, tix[j]] += A[:, eidx[i]]
        cells = []
        for t in teams:
            for sid in smap.values():
                e = est.get((terms[t], sid, "W5"))
                if e and e[2] in ("ok", "anchor", "low_anchor") and E[eidx[t], bidx[sid]] < 0.2:
                    cells.append((sidx[sid], tix[t], math.exp(e[0])))
        if len(cells) < 150:
            continue
        si = np.array([c[0] for c in cells]); tj = np.array([c[1] for c in cells]); v = np.array([c[2] for c in cells])
        # rescale v per state so the Poisson scale is O(1)
        v = v / np.median(v)
        X1 = T[1][si, tj]; X2 = T[2][si, tj]; X3 = T[3][si, tj]
        used_states = sorted(set(si))
        remap = {s: k for k, s in enumerate(used_states)}
        si2 = np.array([remap[s] for s in si])
        ns, nt = len(used_states), len(teams)
        th, ok = fit(v, X1, X2, X3, np.ones(len(v)), ns, nt, si2, tj)
        boots = []
        for _ in range(n_boot):
            draw = rng.integers(0, ns, ns)
            wts = np.bincount(draw, minlength=ns).astype(float)[si2]
            try:
                tb, okb = fit(v, X1, X2, X3, wts, ns, nt, si2, tj)
                if okb:
                    boots.append(tb)
            except Exception:
                pass
        boots = np.array(boots) if boots else np.full((1, 3), np.nan)
        lo, hi = np.nanpercentile(boots, [5, 95], axis=0)
        rows.append({"league": league, "cells": len(v), "states": ns, "teams": nt, "converged": ok,
                     "th0": round(th[0], 4), "th2": round(th[1], 4), "th2_lo": round(lo[1], 4), "th2_hi": round(hi[1], 4),
                     "th3": round(th[2], 4), "th3_lo": round(lo[2], 4), "th3_hi": round(hi[2], 4),
                     "prior_th2": round(PRIOR[2], 3), "prior_th3": round(PRIOR[3], 3)})
        md_rows.append(rows[-1])
        print(rows[-1])
    if not rows:
        print("no antipathy data")
        return
    with open(ROOT / "data/model/gravity_calibration.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator=chr(10))
        w.writeheader()
        w.writerows(rows)
    md = ["# Gravity calibration of the rivalry ladder", "",
          "Auto-generated by `scripts/gravity_calibration.py`. Nothing here feeds the model. Question: relative to a tier-1 rivalry, how much does a tier-2 or tier-3 rivalry "
          "raise a state's antipathy toward the team, after removing each state's overall search level and each team's ambient unpopularity? "
          f"The analyst prior implies tier 2 = {PRIOR[2]:.2f} and tier 3 = {PRIOR[3]:.2f} of tier 1. Intervals are 5th to 95th percentile of a cluster bootstrap over states.", "",
          "| League | Cells | States | Teams | Tier 2 (prior 0.38) | Tier 3 (prior 0.11) | Generic-dislike floor |", "|---|---|---|---|---|---|---|"]
    for r in md_rows:
        ident = (r["th2_hi"] / max(r["th2_lo"], 1e-6) < 20) and (r["th3_hi"] / max(r["th3_lo"], 1e-6) < 20)
        r["identified"] = ident
        tag = "" if ident else " **(not identified: interval spans more than 20x)**"
        md.append(f"| {r['league']} | {r['cells']} | {r['states']} | {r['teams']} | {r['th2']:.2f} ({r['th2_lo']:.2f} to {r['th2_hi']:.2f}) | {r['th3']:.2f} ({r['th3_lo']:.2f} to {r['th3_hi']:.2f}) | {r['th0']:.3f} |{tag}")
    md += ["", "Reading: a value above the prior means that tier matters *more* than the analyst ladder says (the ladder is too steep); below the prior, less. "
           "Wide intervals mean the data cannot tell. Caveats: search interest is not hostility (it includes ambient dislike, sarcasm and national narratives), "
           "small states report zeros that are excluded as below detection (a censoring bias), and tier labels are themselves the analyst's."]
    (ROOT / "docs/GRAVITY_CALIBRATION.md").write_text(chr(10).join(md) + chr(10), encoding="utf-8", newline=chr(10))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 150)
