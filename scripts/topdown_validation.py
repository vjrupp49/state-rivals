"""Phase 9 (partial): independent top-down check. Uses state-vs-state 'X sucks' Google searches
(row = searching state, column = target state), reciprocal D_ab = sqrt(D_ab * D_ba), compared with the
bottom-up M by Spearman and top-20 overlap. Noisy and not purely sports (e.g. 'California sucks');
it is a sanity cross-check, never an input to M. Writes data/model/topdown.json.
"""
import csv, json, math, sqlite3, sys, pathlib
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import lib_trends as L

ROOT = L.ROOT


def main():
    smap = L.state_map()
    con = sqlite3.connect(L.DB)
    tot, ok = con.execute("SELECT count(*), sum(status='ok') FROM jobs WHERE family='TOPDOWN'").fetchone()
    ok = ok or 0
    out = {"completed": False, "batches_ok": ok, "batches_planned": tot}
    if not tot or ok / tot < 0.9:
        out["note"] = "top-down pulls incomplete; validation not claimed"
        (ROOT / "data" / "model" / "topdown.json").write_text(json.dumps(out, indent=1))
        print(out); return out
    est = L.estimate(L.load_jobs(family="TOPDOWN"), smap)
    states = sorted(smap.values()); n = len(states)
    name_of = {v: k for k, v in smap.items()}
    D = np.zeros((n, n))
    for i, s in enumerate(states):
        for j, b in enumerate(states):
            e = est.get((f"{name_of[b]} sucks", s, "W5"))
            D[i, j] = math.exp(e[0]) if e else float('nan')     # missing stays missing (D-007), never 0
    np.fill_diagonal(D, np.nan)
    iu = np.triu_indices(n, 1)
    d_all = np.sqrt(D[iu] * D.T[iu])               # NaN where either direction was not measured
    valid = ~np.isnan(d_all)
    d = np.where(valid, d_all, -1.0)               # missing pairs sort last and get no rank below
    ps = {(r["state_a"], r["state_b"]): float(r["M"]) for r in csv.DictReader(open(ROOT / "data" / "model" / "pair_scores.csv"))}
    m = np.array([ps.get((states[a], states[b]), ps.get((states[b], states[a]), 0.0)) for a, b in zip(*iu)])
    def rk(v): return np.argsort(np.argsort(-v)).astype(float)
    rho = float(np.corrcoef(rk(d[valid]), rk(m[valid]))[0, 1])
    t20d = set(np.argsort(-d)[:20]); t20m = set(np.argsort(-m)[:20])
    pr = np.array(iu).T
    rd_ = np.argsort(np.argsort(-d)) + 1      # rank in top-down (valid pairs first)
    rd_ = np.where(valid, rd_, 0)             # 0 = not measured in both directions (never counted as a low rank)
    rm_ = np.argsort(np.argsort(-m)) + 1      # rank in bottom-up
    pn = lambda k: "-".join((states[pr[k][0]], states[pr[k][1]]))
    with open(ROOT / "data" / "model" / "topdown_pairs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator=chr(10)); w.writerow(["state_a", "state_b", "topdown_D", "topdown_rank", "bottomup_M", "bottomup_rank"])
        for k in range(len(d)):
            w.writerow([states[pr[k][0]], states[pr[k][1]], f"{d[k]:.6g}", int(rd_[k]), f"{m[k]:.6g}", int(rm_[k])])
    out["topdown_top15_with_bottomup_rank"] = [[pn(k), int(rm_[k])] for k in np.argsort(-d)[:15]]
    out["bottomup_top10_with_topdown_rank"] = [[pn(k), int(rd_[k])] for k in np.argsort(-m)[:10]]
    out.update({"completed": True, "pairs_measured_both_directions": int(valid.sum()), "spearman_topdown_vs_bottomup": round(rho, 4), "top20_overlap": len(t20d & t20m),
                "topdown_top10": ["-".join((states[a], states[b])) for a, b in (np.array(iu).T[np.argsort(-d)[:10]])],
                "note": "noisy independent check; mixes sports and non-sports hostility"})
    (ROOT / "data" / "model" / "topdown.json").write_text(json.dumps(out, indent=1))
    print(out); return out


if __name__ == "__main__":
    main()
