"""Phases 5-7: rivalry edges (K,S,T,R), E, H = A(S.T)E, M = sqrt(H_ab H_ba), channel ledger.

Writes: data/registries/rivalry_edges.csv, data/model/E_matrix.csv, R_matrix.csv (sparse long),
        H_matrix.csv, pair_scores.csv, channel_ledger.csv, model_run.json
All S/T/E values are analyst priors (see lib_model.py header) -- never presented as survey data.
"""
import csv
import json
import sys
import pathlib
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import lib_model as LM

ROOT = LM.ROOT
MODEL = LM.MODEL


def main(top_ledger=40):
    states, ents_ids, A, other = LM.load_A()
    reg = {e["entity_id"]: e for e in LM.load_entities()}
    ents = [reg[e] for e in ents_ids]
    edges = LM.build_edges()
    unresolved = [e for e in edges if e[0] == "UNRESOLVED"]
    good = [e for e in edges if e[0] != "UNRESOLVED"]
    R = LM.build_R(ents_ids, good)
    E, buckets = LM.build_E(ents, states)
    F = LM.place_matrix(states, ents_ids, ents)
    H = LM.compute_H(A, R, E, F)
    Hs, M = LM.pair_scores(H, states)
    # original (no place factor) ranking, kept for the side-by-side comparison
    H0 = LM.compute_H(A, R, E)
    _, M0 = LM.pair_scores(H0, states)
    iu0 = np.triu_indices(len(states), 1)
    order0 = np.argsort(-M0[iu0])
    with open(MODEL / "pair_scores_original.csv", "w", newline="", encoding="utf-8") as f0:
        w0 = csv.writer(f0, lineterminator=chr(10))
        w0.writerow(["rank", "state_a", "state_b", "M"])
        for r0, k0 in enumerate(order0, 1):
            w0.writerow([r0, states[iu0[0][k0]], states[iu0[1][k0]], f"{M0[iu0][k0]:.6g}"])

    # registry of edges (schema from docs/PROTOCOL.md section 7, plus analyst tier columns)
    with open(ROOT / "data" / "registries" / "rivalry_edges.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["entity_i", "entity_j", "sport", "direction", "discovery_class", "source", "source_date",
                    "first_known", "last_current_evidence", "lifecycle_status", "survey_rivalry_points",
                    "sample_quality", "notes", "analyst_tier", "S_prior", "T_prior"])
        for i, j, fam, tier, s, t in good:
            w.writerow([i, j, fam, f"{i}->{j}", {1: "R2", 2: "R2", 3: "R3"}[tier] if fam not in ("pwhl", "wnba") else "R4",
                        "analyst_prior (named/documented rivalry; no survey points retrieved)", "2026-10-08", "", "", "current-active",
                        "", "analyst_prior", "tier 1=premier, 2=major, 3=regional/secondary", tier, round(s, 4), round(t, 4)])
    n = len(states)
    with open(MODEL / "E_matrix.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["entity_id"] + buckets)
        for k, e in enumerate(ents_ids):
            w.writerow([e] + [f"{x:.4g}" for x in E[k]])
    idx = np.argwhere(R > 0)
    with open(MODEL / "R_matrix.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["entity_i", "entity_j", "R"])
        for i, j in idx:
            w.writerow([ents_ids[i], ents_ids[j], f"{R[i, j]:.5g}"])
    with open(MODEL / "H_matrix.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["state_id"] + buckets)
        for k, s in enumerate(states):
            w.writerow([s] + [f"{x:.6g}" for x in H[k]])
    pairs = []
    for a in range(n):
        for b in range(a + 1, n):
            pairs.append((M[a, b], a, b))
    pairs.sort(reverse=True)
    rank = {(a, b): r + 1 for r, (_, a, b) in enumerate(pairs)}
    with open(MODEL / "pair_scores.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rank", "state_a", "state_b", "M", "H_a_to_b", "H_b_to_a", "reciprocity_ratio"])
        for m, a, b in pairs:
            lo, hi = sorted([Hs[a, b], Hs[b, a]])
            w.writerow([rank[(a, b)], states[a], states[b], f"{m:.6g}", f"{Hs[a, b]:.6g}", f"{Hs[b, a]:.6g}",
                        f"{(lo / hi) if hi > 0 else 0:.4f}"])
    # channel ledger for top pairs
    names = [e["entity_name"] for e in ents]
    bi = {b: k for k, b in enumerate(buckets)}
    with open(MODEL / "channel_ledger.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pair_rank", "direction", "source_state", "supported_entity", "rival_entity", "sport_family",
                    "embodied_target_state", "contribution", "share_of_directed_H"])
        for m, a, b in pairs[:top_ledger]:
            for src, dst, direc in ((a, b, "a->b"), (b, a, "b->a")):
                C = A[src][:, None] * R * E[:, bi[states[dst]]][None, :] * F[src][None, :]
                tot = C.sum()
                flat = np.argsort(C, axis=None)[::-1][:8]
                for fl in flat:
                    i, j = divmod(int(fl), C.shape[1])
                    if C[i, j] <= 0:
                        continue
                    w.writerow([rank[(a, b)], f"{states[src]}->{states[dst]}", states[src], names[i], names[j],
                                LM.fam_of(ents_ids[i]), states[dst], f"{C[i, j]:.6g}", f"{C[i, j] / tot:.4f}"])
    info = {"n_edges_directed": len(good), "n_unresolved": len(unresolved),
            "unresolved_samples": [u[1] for u in unresolved[:25]],
            "top10": [(states[a], states[b], round(m, 5)) for m, a, b in pairs[:10]],
            "E_rowsum_max": float(E.sum(1).max()), "E_rowsum_min": float(E.sum(1).min())}
    (MODEL / "model_run.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    print(json.dumps(info))


if __name__ == "__main__":
    main()
