"""Does hostility fall with distance beyond what the model already predicts? (my Celtics-Lakers gut check)

Same Poisson pseudo-likelihood as gravity_calibration.py, with one more term:

    E[v[s,j]] = exp(kappa_s + psi_j) * g[s,j] * exp(-gamma * d[s,j] / 1000 mi)
    g[s,j]    = th0 + X1 + th2*X2 + th3*X3       (model-implied rivalry hostility from state s toward team j)

d is the distance between the centroids of state s and team j's home state. gamma > 0 means that, for the same model-implied
rivalry hostility, far-away states show less antipathy than near ones: distant brand rivalries (a Californian's feelings about
the Celtics) are weaker than the model's team-level structure implies. gamma near 0 means the model's structure already explains
the geography. exp(-gamma) is the factor by which hostility shrinks per 1,000 miles.
Cluster bootstrap over states for intervals. Nothing here feeds the model; it estimates a candidate place-anchoring factor.
Writes data/model/gravity_distance.csv and docs/GRAVITY_DISTANCE.md.

    python scripts/gravity_distance.py [bootstrap_draws]
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


def haversine(a, b):
    r = 3958.8
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dphi, dl = p2 - p1, math.radians(b[1] - a[1])
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def fit(v, X1, X2, X3, d, w, ns, nt, si, tj):
    def fun(p):
        kap, psi = p[:ns], p[ns:ns + nt]
        th = np.exp(p[ns + nt:ns + nt + 3])
        gam = p[ns + nt + 3]
        g = th[0] + X1 + th[1] * X2 + th[2] * X3
        mu = np.exp(kap[si] + psi[tj] - gam * d) * g
        loss = np.sum(w * (mu - v * np.log(np.maximum(mu, 1e-300)))) + 1e-4 * (np.sum(kap ** 2) + np.sum(psi ** 2))
        r = w * (mu - v)
        gk = np.bincount(si, weights=r, minlength=ns) + 2e-4 * kap
        gp = np.bincount(tj, weights=r, minlength=nt) + 2e-4 * psi
        gt = np.array([np.sum(r * th[0] / g), np.sum(r * th[1] * X2 / g), np.sum(r * th[2] * X3 / g)])
        gg = np.sum(-r * d)
        return loss, np.concatenate([gk, gp, gt, [gg]])
    p0 = np.concatenate([np.zeros(ns + nt), np.log([0.05, PRIOR[2], PRIOR[3]]), [0.0]])
    res = minimize(fun, p0, jac=True, method="L-BFGS-B", options={"maxiter": 500})
    return float(res.x[-1]), bool(res.success), res.x


def main(n_boot=100, seed=5):
    states, ids, A, _ = LM.load_A()
    sidx = {s: k for k, s in enumerate(states)}
    eidx = {e: k for k, e in enumerate(ids)}
    reg = {e["entity_id"]: e for e in LM.load_entities()}
    E, buckets = LM.build_E([reg[e] for e in ids], states)
    bidx = {b: k for k, b in enumerate(buckets)}
    cen = {r["state_id"]: (float(r["lat"]), float(r["lon"])) for r in csv.DictReader(open(ROOT / "config/state_centroids.csv", encoding="utf-8"))}
    edges = [e for e in LM.build_edges() if e[0] != "UNRESOLVED"]
    smap = L.state_map()
    rng = np.random.default_rng(seed)
    rows = []
    for league in ("nfl", "mlb", "nba", "nhl"):
        jobs = L.load_jobs(family=f"HATE_{league}")
        if not jobs:
            continue
        est = L.estimate(jobs, smap)
        terms = TW._hate_terms(league)
        teams = [t for t in sorted(terms) if reg[t]["home_state"] in cen]
        tix = {t: k for k, t in enumerate(teams)}
        T = {k: np.zeros((len(states), len(teams))) for k in (1, 2, 3)}
        for i, j, fam, tier, _, _ in edges:
            if fam == league and j in tix and tier in T:
                T[tier][:, tix[j]] += A[:, eidx[i]]
        cells = []
        for t in teams:
            for sid in smap.values():
                e = est.get((terms[t], sid, "W5"))
                if e and e[2] in ("ok", "anchor", "low_anchor") and E[eidx[t], bidx[sid]] < 0.2:
                    cells.append((sidx[sid], tix[t], math.exp(e[0]), haversine(cen[sid], cen[reg[t]["home_state"]]) / 1000.0, e[1]))
        if len(cells) < 150:
            continue
        si = np.array([c[0] for c in cells]); tj = np.array([c[1] for c in cells]); v = np.array([c[2] for c in cells]); d = np.array([c[3] for c in cells]); mvar = np.array([c[4] for c in cells])
        v = v / np.median(v)
        used = sorted(set(si)); remap = {s: k for k, s in enumerate(used)}; si2 = np.array([remap[s] for s in si]); ns, nt = len(used), len(teams)
        X1, X2, X3 = T[1][si, tj], T[2][si, tj], T[3][si, tj]
        gam, ok, px = fit(v, X1, X2, X3, d, np.ones(len(v)), ns, nt, si2, tj)
        kap, psi = px[:ns], px[ns:ns + nt]
        th = np.exp(px[ns + nt:ns + nt + 3])
        mu = np.exp(kap[si2] + psi[tj] - px[-1] * d) * (th[0] + X1 + th[1] * X2 + th[2] * X3)
        resid = np.log(v) - np.log(np.maximum(mu, 1e-12))
        resid_sd = float(np.std(resid)); meas_sd = float(math.sqrt(np.mean(mvar))); model_sd = math.sqrt(max(resid_sd ** 2 - meas_sd ** 2, 0.0))
        boots = []
        for _ in range(n_boot):
            w = np.bincount(rng.integers(0, ns, ns), minlength=ns).astype(float)[si2]
            try:
                g_b, ok_b, _ = fit(v, X1, X2, X3, d, w, ns, nt, si2, tj)
                if ok_b:
                    boots.append(g_b)
            except Exception:
                pass
        lo, hi = np.percentile(boots, [5, 95]) if boots else (float("nan"), float("nan"))
        rows.append({"league": league, "cells": len(v), "median_distance_miles": round(float(np.median(d)) * 1000), "gamma_per_1000mi": round(gam, 3), "resid_sd_log": round(resid_sd, 3), "meas_sd_log": round(meas_sd, 3), "model_error_sd_log": round(model_sd, 3),
                     "gamma_lo": round(float(lo), 3), "gamma_hi": round(float(hi), 3),
                     "shrink_per_1000mi": round(math.exp(-gam), 3), "shrink_lo": round(math.exp(-hi), 3), "shrink_hi": round(math.exp(-lo), 3), "converged": ok})
        print(rows[-1])
    if not rows:
        print("no data")
        return
    with open(ROOT / "data/model/gravity_distance.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator=chr(10))
        w.writeheader()
        w.writerows(rows)
    md = ["# Does hostility fall with distance? (beyond the model)", "",
          "Auto-generated by `scripts/gravity_distance.py`. Same fit as the gravity calibration, with a distance term between the searching state and the team's home state. "
          "The factor is how much antipathy shrinks per 1,000 miles, *holding the model's predicted rivalry hostility fixed*. 1.00 means distance adds nothing the model has not already captured; "
          "below 1 means the model overstates far-away (brand) rivalries relative to near (place) ones.", "",
          "| League | Cells | Median distance (mi) | Shrink per 1,000 mi (90% interval) | Optimizer converged |", "|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['league']} | {r['cells']} | {r['median_distance_miles']} | {r['shrink_per_1000mi']:.2f} ({r['shrink_lo']:.2f} to {r['shrink_hi']:.2f}) | {'yes' if r['converged'] else 'NO (treat as indicative)'} |")
    md += ["", "Caveats: distance is between state centroids; the target's home state is used even for teams with a regional fan base; search is not hostility; small-state zeros are censored."]
    (ROOT / "docs/GRAVITY_DISTANCE.md").write_text(chr(10).join(md) + chr(10), encoding="utf-8", newline=chr(10))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 100)
