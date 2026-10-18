"""Phases 8-9: structural robustness + Monte Carlo uncertainty.

Deterministic variants: reciprocity (harmonic/min/arithmetic), salience-only (T=1), flat-tier prior
('structure only'), leave-one-sport-out, strongest-edge removal, and data-side variants (gamma, window,
beta, flat W). Monte Carlo: lognormal noise on A (per-cell logsd from A_meta, renormalized within
state-sport), uncertainty on sport mix W (sd 0.2 lognormal), systematic per-sport multipliers and per-edge noise on S, noise on T, noise on E.
Outputs: data/model/pair_uncertainty.csv, robustness_variants.csv, removal_tests.csv, robustness.json
"""
import csv
import math
import json
import sys
import time
import pathlib
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import lib_model as LM
import build_P_from_trends as BP
import build_W_A as BW

ROOT, MODEL = LM.ROOT, LM.MODEL
from paths import WORK as _WORK
WORKV = _WORK / "variants"
GROUPS = {
    "football": {"nfl", "cfb"}, "baseball": {"mlb", "bsb"}, "basketball": {"nba", "wnba", "cbb_m", "cbb_w"},
    "hockey": {"nhl", "pwhl", "hky_m", "hky_w"}, "soccer": {"mls", "nwsl"}, "softball": {"sfb"},
    "college_all": {"cfb", "cbb_m", "cbb_w", "hky_m", "hky_w", "bsb", "sfb", "vbw", "lax", "wrs"},
    "pro_all": {"nfl", "mlb", "nba", "nhl", "mls", "wnba", "nwsl", "pwhl"},
}
FAMS = ["nfl", "mlb", "nba", "nhl", "mls", "wnba", "nwsl", "pwhl", "cfb", "cbb_m", "cbb_w", "hky_m", "hky_w", "bsb", "sfb", "vbw", "lax", "wrs"]


def load_noise():
    """MC noise magnitudes: config/mc_noise.yaml (derived from data by scripts/derive_noise.py), analyst defaults if absent."""
    import yaml
    d = {"s_edge_sd": 0.35, "t_sd": 0.25, "e_sd": 0.15, "w_mix_sd": 0.20, "sport_mult_sd": 0.30, "gamma_sd": 0.06}
    f = LM.CONFIG / "mc_noise.yaml"
    if f.exists():
        d.update(yaml.safe_load(f.read_text(encoding="utf-8")) or {})
    return d


def rankvec(v):
    o = np.argsort(-v)
    r = np.empty(len(v), int)
    r[o] = np.arange(1, len(v) + 1)
    return r


def spearman(a, b):
    ra, rb = rankvec(a).astype(float), rankvec(b).astype(float)
    return float(np.corrcoef(ra, rb)[0, 1])


PLACE = None      # place-factor matrix, set by main(); None means the original model


_DEFAULT = object()


def Mvec(A, R, E, states, how="geo", F=_DEFAULT):
    H = LM.compute_H(A, R, E, PLACE if F is _DEFAULT else F)
    n = len(states)
    Hs = H[:, :n].copy()
    np.fill_diagonal(Hs, 0)
    iu = np.triu_indices(n, 1)
    a, b = Hs[iu], Hs.T[iu]
    if how == "geo":
        return np.sqrt(np.maximum(a, 0) * np.maximum(b, 0)), Hs
    if how == "harm":
        return np.where(a + b > 0, 2 * a * b / np.maximum(a + b, 1e-30), 0), Hs
    if how == "min":
        return np.minimum(a, b), Hs
    return (a + b) / 2, Hs


def main(n_mc=600, seed=7):
    t0 = time.time()
    states, ids, A, other = LM.load_A()
    n, I = A.shape
    reg = {e["entity_id"]: e for e in LM.load_entities()}
    ents = [reg[e] for e in ids]
    fam = np.array([FAMS.index(LM.fam_of(e)) for e in ids])
    E, buckets = LM.build_E(ents, states)
    edges = [e for e in LM.build_edges() if e[0] != "UNRESOLVED"]
    R0 = LM.build_R(ids, edges)
    global PLACE
    PLACE = LM.place_matrix(states, ids, ents)
    M0, Hs0 = Mvec(A, R0, E, states)
    iu = np.triu_indices(n, 1)
    pair_names = [(states[a], states[b]) for a, b in zip(*iu)]
    order0 = np.argsort(-M0)
    top1 = int(order0[0])
    variants = []

    def record(name, M, note=""):
        o = np.argsort(-M)
        rk_top1 = int(rankvec(M)[top1])
        variants.append({"variant": name, "top5": ";".join("-".join(pair_names[k]) for k in o[:5]),
                         "base_top1_rank": rk_top1, "spearman_vs_base": round(spearman(M0, M), 4), "note": note})

    record("base", M0)
    for how in ("harm", "min", "arith"):
        record(f"reciprocity_{how}", Mvec(A, R0, E, states, how)[0])
    edges_s = [(i, j, f, t, s, 1.0) for (i, j, f, t, s, _) in edges]
    record("salience_only_T=1", Mvec(A, LM.build_R(ids, edges_s), E, states)[0])
    edges_f = [e for e in LM.build_edges(flat=True) if e[0] != "UNRESOLVED"]
    record("flat_tier_prior(structure_only)", Mvec(A, LM.build_R(ids, edges_f), E, states)[0],
           "all edges get identical S,T: tests how much the answer depends on my tier judgments")
    # independent reader-based ladder (docs/WIKIPEDIA_RIVALRY.md): tier 3 at 0.27 of tier 1 instead of 0.11; S and T scaled equally so S*T hits the target
    scale3 = math.sqrt(0.27 / (LM.TIER_S[3] * LM.TIER_T[3] / (LM.TIER_S[1] * LM.TIER_T[1])))
    edges_r = [(i, j, f, t, s * (scale3 if t == 3 else 1.0), tt * (scale3 if t == 3 else 1.0)) for (i, j, f, t, s, tt) in edges]
    record("tier3_reader_ladder(0.27)", Mvec(A, LM.build_R(ids, edges_r), E, states)[0], "tier-3 rivalries weighted as Wikipedia readers see them")
    record("no_place_factor(original)", Mvec(A, R0, E, states, F=None)[0], "the model without the distance factor (protocol revision D-016)")
    edges_nm = [e for e in LM.build_edges(measured=False) if e[0] != "UNRESOLVED"]
    record("no_measured_split", Mvec(A, LM.build_R(ids, edges_nm), E, states)[0], "tier-based salience split only, without the co-search blend")
    for g, fs in GROUPS.items():
        mask = np.array([LM.fam_of(e) not in fs for e in ids], float)
        record(f"leave_out_{g}", Mvec(A * mask[None, :], R0, E, states)[0])
    # data-side variants
    WORKV.mkdir(parents=True, exist_ok=True)
    for name, kw in {"gamma_c_0(google_only)": dict(g=0.0), "gamma_c_x2": dict(g=2.0), "window_current_only": dict(w="C"),
                     "beta_equal_0.5": dict(b=(0.5, 0.5)), "beta_no_survey_prior": dict(b=(1.0, 0.0)),
                     "flat_sport_weights": dict(flat=True), "sport_terms_phrase(original)": dict(terms="phrase")}.items():
        try:
            d = WORKV / name.split("(")[0]
            d.mkdir(exist_ok=True)
            BP.main(gamma_c_scale=kw.get("g", 1.0), out=d / "P.csv", window=kw.get("w", "P"), quiet=True)
            b = kw.get("b", (BW.BETA_G, BW.BETA_N))
            BW.main(b[0], b[1], p_path=d / "P.csv", model=d, quiet=True, flat_w=kw.get("flat", False), term_set=kw.get("terms", "topic"))
            _, ids2, A2, _ = LM.load_A(d)
            record(name, Mvec(A2, R0, E, states)[0])
        except Exception as ex:
            variants.append({"variant": name, "top5": "", "base_top1_rank": -1, "spearman_vs_base": 0, "note": f"FAILED {ex}"})
    # strongest-edge removal for top 30 pairs
    removal = []
    ib = {b: k for k, b in enumerate(buckets)}
    sidx = {s: k for k, s in enumerate(states)}
    for k in order0[:30]:
        a, b = sidx[pair_names[k][0]], sidx[pair_names[k][1]]
        Cab = A[a][:, None] * R0 * E[:, ib[states[b]]][None, :] * PLACE[a][None, :]
        Cba = A[b][:, None] * R0 * E[:, ib[states[a]]][None, :] * PLACE[b][None, :]
        tot = Cab + Cba.T
        i, j = np.unravel_index(np.argmax(tot), tot.shape)
        hab = Hs0[a, b] - Cab[i, j] - Cab[j, i]
        hba = Hs0[b, a] - Cba[i, j] - Cba[j, i]
        m_new = float(np.sqrt(max(hab, 0) * max(hba, 0)))
        removal.append({"pair": "-".join(pair_names[k]), "rank_base": int(np.where(order0 == k)[0][0]) + 1, "M_base": float(M0[k]),
                        "removed_edge": f"{ents[i]['entity_name']} <-> {ents[j]['entity_name']}", "M_after": m_new,
                        "retained_share": m_new / M0[k] if M0[k] else 0,
                        "approx_rank_after": int((M0 > m_new).sum()) + 1})
    # Monte Carlo
    sd = np.zeros((n, I))
    with open(MODEL / "A_meta.csv", newline="", encoding="utf-8") as f:
        idx = {e: k for k, e in enumerate(ids)}
        for r in csv.DictReader(f):
            sd[sidx[r["state_id"]], idx[r["entity_id"]]] = float(r["logsd"])
    F = np.zeros((I, len(FAMS)))
    F[np.arange(I), fam] = 1
    tgt = A @ F
    ei = np.array([ids.index(e[0]) for e in edges]); ej = np.array([ids.index(e[1]) for e in edges])
    ef = np.array([FAMS.index(e[2]) for e in edges]); es = np.array([e[4] for e in edges]); et = np.array([e[5] for e in edges])
    rng = np.random.default_rng(seed)
    NZ = load_noise()
    DMAT = LM.place_distance(states, ids, ents)      # for the per-draw place factor
    allM = np.zeros((n_mc, len(M0)), np.float32)
    for d in range(n_mc):
        Ad = A * np.exp(sd * rng.standard_normal((n, I)) - 0.5 * sd ** 2)
        fs = Ad @ F
        wn = np.exp(NZ["w_mix_sd"] * rng.standard_normal(tgt.shape) - 0.5 * NZ["w_mix_sd"] ** 2)      # uncertainty on sport mix W (beta unfrozen, D-012)
        tgt_d = tgt * wn
        tsum = tgt_d.sum(1, keepdims=True)
        tgt_d = tgt_d * np.divide(tgt.sum(1, keepdims=True), tsum, out=np.ones_like(tsum), where=tsum > 0)
        sc = np.divide(tgt_d, fs, out=np.ones_like(fs), where=fs > 0)
        Ad = Ad * (sc @ F.T)
        fm = np.exp(NZ["sport_mult_sd"] * rng.standard_normal(len(FAMS)) - 0.5 * NZ["sport_mult_sd"] ** 2)
        S = np.zeros((I, I))
        S[ei, ej] = es * fm[ef] * np.exp(NZ["s_edge_sd"] * rng.standard_normal(len(es)) - 0.5 * NZ["s_edge_sd"] ** 2)
        T = np.zeros((I, I))
        T[ei, ej] = np.minimum(1.0, et * np.exp(NZ["t_sd"] * rng.standard_normal(len(et)) - 0.5 * NZ["t_sd"] ** 2))
        rs = S.sum(1)
        S *= np.minimum(1.0, LM.ROW_CAP / np.maximum(rs, 1e-12))[:, None]
        Ed = E * np.exp(NZ["e_sd"] * rng.standard_normal(E.shape) * (E > 0))
        Ed /= Ed.sum(1, keepdims=True)
        g_d = max(0.0, LM.PLACE_GAMMA + NZ["gamma_sd"] * rng.standard_normal()) if LM.PLACE_GAMMA > 0 else 0.0   # place-factor uncertainty
        allM[d] = Mvec(Ad, S * T, Ed, states, F=np.exp(-g_d * DMAT) if g_d > 0 else None)[0]
    ranks = np.argsort(np.argsort(-allM, axis=1), axis=1) + 1
    unc = []
    for k in range(len(M0)):
        r = ranks[:, k]
        unc.append({"state_a": pair_names[k][0], "state_b": pair_names[k][1], "M_base": float(M0[k]),
                    "M_p05": float(np.percentile(allM[:, k], 5)), "M_p50": float(np.percentile(allM[:, k], 50)),
                    "M_p95": float(np.percentile(allM[:, k], 95)), "P_rank1": float((r == 1).mean()),
                    "P_top3": float((r <= 3).mean()), "P_top10": float((r <= 10).mean()), "median_rank": float(np.median(r))})
    unc.sort(key=lambda x: (-x["P_top3"], -x["P_rank1"], -x["M_base"]))
    with open(MODEL / "pair_uncertainty.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(unc[0].keys())); w.writeheader(); w.writerows(unc)
    with open(MODEL / "robustness_variants.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(variants[0].keys())); w.writeheader(); w.writerows(variants)
    with open(MODEL / "removal_tests.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(removal[0].keys())); w.writeheader(); w.writerows(removal)
    summ = {"n_mc": n_mc, "seconds": round(time.time() - t0), "base_top1": "-".join(pair_names[top1]),
            "mc_top_by_P_rank1": [(u["state_a"] + "-" + u["state_b"], round(u["P_rank1"], 3), round(u["P_top3"], 3)) for u in sorted(unc, key=lambda x: -x["P_rank1"])[:8]],
            "variants_with_top1_rank_le_3": sum(1 for v in variants if 0 < v["base_top1_rank"] <= 3), "n_variants": len(variants),
            "removal_top1_retained_share": removal[0]["retained_share"], "removal_top1_rank_after": removal[0]["approx_rank_after"]}
    (MODEL / "robustness.json").write_text(json.dumps(summ, indent=1), encoding="utf-8")
    print(json.dumps(summ))


if __name__ == "__main__":
    main(n_mc=int(sys.argv[1]) if len(sys.argv) > 1 else 600)
