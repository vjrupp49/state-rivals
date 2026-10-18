"""Does it matter how often two teams actually play? (my question: 13 baseball games vs 2 football games can push either way.)

Gravity model with distance (gravity_distance.py) plus an exposure elasticity eta:

    X_t[s, j] = sum over rivals i of team j at tier t:  A[s, i] * (meetings_per_season_ij / league mean) ** eta
    E[v[s,j]] = exp(kappa_s + psi_j - gamma * distance) * ( th0 + X_1 + th2 * X_2 + th3 * X_3 )

eta > 0: more meetings raise antipathy; eta < 0: fatigue (more meetings dilute it); eta near 0: how often they play does not matter.
Team-level quantities that do not vary by state (a team's overall success or unpopularity) are absorbed by the team effect psi_j,
so no separate success control is needed in this specification. Meetings per season: 2021-2025 regular season (data/raw/pair_exposure.csv).
Cluster bootstrap over states. Nothing here feeds the model.
Writes data/model/gravity_exposure.csv and docs/GRAVITY_EXPOSURE.md.

    python scripts/gravity_exposure.py [bootstrap_draws]
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
from gravity_distance import haversine  # noqa: E402

ROOT = LM.ROOT
PRIOR = {2: 0.2 * 0.65 / (0.4 * 0.85), 3: 0.08 * 0.45 / (0.4 * 0.85)}


def main(n_boot=80, seed=9):
    states, ids, A, _ = LM.load_A()
    sidx = {s: k for k, s in enumerate(states)}
    eidx = {e: k for k, e in enumerate(ids)}
    reg = {e["entity_id"]: e for e in LM.load_entities()}
    E, buckets = LM.build_E([reg[e] for e in ids], states)
    bidx = {b: k for k, b in enumerate(buckets)}
    cen = {r["state_id"]: (float(r["lat"]), float(r["lon"])) for r in csv.DictReader(open(ROOT / "config/state_centroids.csv", encoding="utf-8"))}
    edges = [e for e in LM.build_edges() if e[0] != "UNRESOLVED"]
    expo = {}
    for r in csv.DictReader(open(ROOT / "data/raw/pair_exposure.csv", encoding="utf-8")):
        expo[(r["entity_a"], r["entity_b"])] = expo[(r["entity_b"], r["entity_a"])] = float(r["meetings_per_season"])
    smap = L.state_map()
    rng = np.random.default_rng(seed)
    rows = []
    for league in ("nfl", "mlb"):
        jobs = L.load_jobs(family=f"HATE_{league}")
        est = L.estimate(jobs, smap)
        terms = TW._hate_terms(league)
        teams = [t for t in sorted(terms) if reg[t]["home_state"] in cen]
        tix = {t: k for k, t in enumerate(teams)}
        ledge = [(i, j, tier) for i, j, fam, tier, _, _ in edges if fam == league and j in tix and tier in (1, 2, 3)]
        mean_ex = np.mean([expo.get((i, j), 0.05) for i, j, _ in ledge])
        # M_t[i, j] = normalised exposure of edge i->j at tier t (0 if no such edge); logM likewise
        M = {t: np.zeros((len(ids), len(teams))) for t in (1, 2, 3)}
        for i, j, tier in ledge:
            M[tier][eidx[i], tix[j]] = max(expo.get((i, j), 0.05), 0.05) / mean_ex
        mask = {t: M[t] > 0 for t in M}
        logM = {t: np.where(mask[t], np.log(np.where(mask[t], M[t], 1.0)), 0.0) for t in M}
        cells = []
        for t in teams:
            for sid in smap.values():
                e = est.get((terms[t], sid, "W5"))
                if e and e[2] in ("ok", "anchor", "low_anchor") and E[eidx[t], bidx[sid]] < 0.2:
                    cells.append((sidx[sid], tix[t], math.exp(e[0]), haversine(cen[sid], cen[reg[t]["home_state"]]) / 1000.0))
        if len(cells) < 150:
            continue
        si = np.array([c[0] for c in cells]); tj = np.array([c[1] for c in cells]); v = np.array([c[2] for c in cells]); d = np.array([c[3] for c in cells])
        v = v / np.median(v)
        used = sorted(set(si)); remap = {s: k for k, s in enumerate(used)}; si2 = np.array([remap[s] for s in si]); ns, nt = len(used), len(teams)

        def xs(eta):
            X, dX = {}, {}
            for t in (1, 2, 3):
                Mt = np.where(mask[t], np.power(np.where(mask[t], M[t], 1.0), eta), 0.0)
                X[t] = (A @ Mt)[si, tj]
                dX[t] = (A @ (Mt * logM[t]))[si, tj]
            return X, dX

        def fit(w, start=None):
            def fun(p):
                kap, psi = p[:ns], p[ns:ns + nt]
                th = np.exp(p[ns + nt:ns + nt + 3])
                gam, eta = p[ns + nt + 3], p[ns + nt + 4]
                X, dX = xs(eta)
                g = th[0] + X[1] + th[1] * X[2] + th[2] * X[3]
                base = np.exp(kap[si2] + psi[tj] - gam * d)
                mu = base * g
                loss = np.sum(w * (mu - v * np.log(np.maximum(mu, 1e-300)))) + 1e-4 * (np.sum(kap ** 2) + np.sum(psi ** 2))
                r = w * (mu - v)
                gk = np.bincount(si2, weights=r, minlength=ns) + 2e-4 * kap
                gp = np.bincount(tj, weights=r, minlength=nt) + 2e-4 * psi
                gt = np.array([np.sum(r * th[0] / g), np.sum(r * th[1] * X[2] / g), np.sum(r * th[2] * X[3] / g)])
                gg = np.sum(-r * d)
                ge = np.sum(w * (1 - v / np.maximum(mu, 1e-300)) * base * (dX[1] + th[1] * dX[2] + th[2] * dX[3]))
                return loss, np.concatenate([gk, gp, gt, [gg, ge]])
            p0 = np.concatenate([np.zeros(ns + nt), np.log([0.05, PRIOR[2], PRIOR[3]]), [0.3, 0.0]]) if start is None else start
            res = minimize(fun, p0, jac=True, method="L-BFGS-B", options={"maxiter": 500})
            return res.x[-2], res.x[-1], bool(res.success), res.x

        gam, eta, ok, px = fit(np.ones(len(v)))
        boots = []
        for _ in range(n_boot):
            w = np.bincount(rng.integers(0, ns, ns), minlength=ns).astype(float)[si2]
            try:
                gb, eb, okb, _ = fit(w, px)
                if okb:
                    boots.append((gb, eb))
            except Exception:
                pass
        b = np.array(boots) if boots else np.full((1, 2), np.nan)
        elo, ehi = np.percentile(b[:, 1], [5, 95]); glo, ghi = np.percentile(b[:, 0], [5, 95])
        rows.append({"league": league, "cells": len(v), "eta": round(float(eta), 3), "eta_lo": round(float(elo), 3), "eta_hi": round(float(ehi), 3),
                     "gamma_per_1000mi": round(float(gam), 3), "gamma_lo": round(float(glo), 3), "gamma_hi": round(float(ghi), 3), "converged": ok})
        print(rows[-1])
    if not rows:
        return
    with open(ROOT / "data/model/gravity_exposure.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator=chr(10))
        w.writeheader()
        w.writerows(rows)
    md = ["# Does it matter how often two teams meet?", "",
          "Auto-generated by `scripts/gravity_exposure.py`. Elasticity of antipathy with respect to meetings per season (regular season, 2021-2025), "
          "holding the model's rivalry structure and distance fixed. Positive: more meetings raise antipathy; negative: fatigue; near zero: scheduling does not matter. "
          "Team-wide effects (success, general unpopularity) are absorbed by the team effect.", "",
          "| League | Cells | Exposure elasticity eta (90% interval) | Distance factor per 1,000 mi (gamma, 90% interval) |", "|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['league']} | {r['cells']} | {r['eta']:+.2f} ({r['eta_lo']:+.2f} to {r['eta_hi']:+.2f}) | {math.exp(-r['gamma_per_1000mi']):.2f} ({math.exp(-r['gamma_hi']):.2f} to {math.exp(-r['gamma_lo']):.2f}) |")
    md += ["", "Caveats: exposure is regular-season meetings only (no postseason, no non-conference college games); NBA, NHL and college lack a clean free schedule source here; "
           "search is not hostility; intervals are a cluster bootstrap over states."]
    (ROOT / "docs/GRAVITY_EXPOSURE.md").write_text(chr(10).join(md) + chr(10), encoding="utf-8", newline=chr(10))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 80)
