"""A measured pair score, built only from antipathy searches, compared with the model (design: docs/RIVALRY_WEIGHT_DESIGN.md).

For every ordered pair (a, b): Hmeas[a, b] = sum over units u that embody b of E[u, b] * v[a, u], where v is the measured
'<team or school> suck' interest in state a on one scale (Cowboys-suck units per state). Pair score
Mmeas = sqrt(Hmeas[a,b] * Hmeas[b,a]). This uses the model's identity layer E (who stands for which state) but NONE of the
analyst rivalry tiers, the attention matrix A, or the temperature, so agreement with the model's M tests those layers.
Own-state units are excluded by construction. Cells are kept only where the measured units cover at least 60% of the
model's mass for that direction (so censored small-state data do not masquerade as low hostility).

Also reports the effective number of channels (exp of the entropy of channel shares): 1 means all of a direction runs through
one matchup. Nothing here feeds the model. Writes data/model/measured_hostility.csv and docs/MEASURED_HOSTILITY.md.

    python scripts/measured_hostility.py
"""
import csv
import math
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


def rank(v):
    return np.argsort(np.argsort(-np.asarray(v))) + 1


def main():
    states, ids, A, _ = LM.load_A()
    n = len(states)
    sidx = {s: k for k, s in enumerate(states)}
    eidx = {e: k for k, e in enumerate(ids)}
    reg = {e["entity_id"]: e for e in LM.load_entities()}
    E, buckets = LM.build_E([reg[e] for e in ids], states)
    bidx = {b: k for k, b in enumerate(buckets)}
    R = LM.build_R(ids, [e for e in LM.build_edges() if e[0] != "UNRESOLVED"])
    smap = L.state_map()
    out = LMS.measurements(smap, reg)
    if out is None:
        print("bridges not finished")
        return
    v, unit_name, school_of_cfb = out

    def unit_of(eid):
        e = reg[eid]
        if e["professional_college"] != "college":
            return "pro:" + eid
        if eid.startswith("cfb_"):
            return "sch:" + school_of_cfb.get(eid, "")
        for suf in SUFFIXES:
            if e["entity_name"].endswith(suf):
                return "sch:" + e["entity_name"][:-len(suf)]
        return None

    members = {}
    for eid in ids:
        u = unit_of(eid)
        if u:
            members.setdefault(u, []).append(eid)
    unit_E = {u: np.max([E[eidx[m]] for m in mem], axis=0) for u, mem in members.items()}      # unit embodiment per bucket
    measured_units = {u for _, u in v}
    Hm = A @ R                                                                                   # model hostility toward each entity
    Hmeas = np.zeros((n, n))
    Hmod = np.zeros((n, n))
    ok = np.zeros((n, n), bool)
    neff_mod = np.full((n, n), np.nan)
    neff_meas = np.full((n, n), np.nan)
    for a in states:
        for b in states:
            if a == b:
                continue
            tot = cov = 0.0
            mvals, wvals, cvals = [], [], []
            for u, mem in members.items():
                eb = unit_E[u][bidx[b]]
                if eb < 0.2:
                    continue
                contrib = sum(float(Hm[sidx[a], eidx[m]] * E[eidx[m], bidx[b]]) for m in mem)
                tot += contrib
                cvals.append(contrib)
                if u in measured_units and (a, u) in v:
                    cov += contrib
                    mvals.append(eb * v[(a, u)])
                    wvals.append(contrib)
            Hmod[sidx[a], sidx[b]] = tot
            if tot > 0 and cov / tot >= 0.6 and mvals:
                ok[sidx[a], sidx[b]] = True
                Hmeas[sidx[a], sidx[b]] = sum(mvals)
                p = np.array(mvals) / sum(mvals)
                neff_meas[sidx[a], sidx[b]] = math.exp(-np.sum(p[p > 0] * np.log(p[p > 0])))
            if tot > 0:
                p = np.array(cvals) / tot
                neff_mod[sidx[a], sidx[b]] = math.exp(-np.sum(p[p > 0] * np.log(p[p > 0])))
    iu = np.triu_indices(n, 1)
    both = ok[iu] & ok.T[iu]
    pairs = [(states[i], states[j]) for i, j in zip(*iu)]
    mm = np.sqrt(Hmeas[iu] * Hmeas.T[iu])
    ps = {(r["state_a"], r["state_b"]): (int(r["rank"]), float(r["M"])) for r in csv.DictReader(open(ROOT / "data/model/pair_scores.csv", encoding="utf-8"))}
    mod_rank = np.array([ps[p][0] for p in pairs])
    mod_m = np.array([ps[p][1] for p in pairs])
    idx = np.where(both & (mm > 0))[0]
    meas_rank = np.empty(len(pairs), int)
    meas_rank[:] = 0
    meas_rank[idx] = rank(mm[idx])
    rho = float(np.corrcoef(np.argsort(np.argsort(-mm[idx])), np.argsort(np.argsort(-mod_m[idx])))[0, 1])
    rows = []
    for k in np.argsort(-mm):
        if k in set(idx):
            a, b = pairs[k]
            rows.append({"pair": f"{a}-{b}", "measured_rank": int(meas_rank[k]), "model_rank": int(mod_rank[k]), "measured_M": round(float(mm[k]), 4), "model_M": round(float(mod_m[k]), 5),
                         "neff_model_a_to_b": round(float(neff_mod[sidx[a], sidx[b]]), 2), "neff_model_b_to_a": round(float(neff_mod[sidx[b], sidx[a]]), 2),
                         "neff_measured_a_to_b": round(float(neff_meas[sidx[a], sidx[b]]), 2), "neff_measured_b_to_a": round(float(neff_meas[sidx[b], sidx[a]]), 2)})
    with open(ROOT / "data/model/measured_hostility.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator=chr(10))
        w.writeheader()
        w.writerows(rows)
    top_model = sorted(rows, key=lambda r: r["model_rank"])[:12]
    md = ["# A measured pair score (searches only) versus the model", "",
          "Auto-generated by `scripts/measured_hostility.py`. Built from '<team or school> suck' searches by state (one scale via bridge batches), "
          "weighted only by which state each team or school embodies. No rivalry tiers, attention weights or temperature are used, so it independently tests those layers. "
          f"Pairs scored: {len(idx)} of 1,225 (both directions measured, at least 60% model coverage). Rank correlation with the model's M across those pairs: **{rho:.2f}**.", "",
          "## Top 15 by measured score", "", "| Measured rank | Pair | Model rank | N_eff measured (a to b / b to a) | N_eff model |", "|---|---|---|---|---|"]
    for r in rows[:15]:
        md.append(f"| {r['measured_rank']} | {r['pair']} | {r['model_rank']} | {r['neff_measured_a_to_b']:.1f} / {r['neff_measured_b_to_a']:.1f} | {r['neff_model_a_to_b']:.1f} / {r['neff_model_b_to_a']:.1f} |")
    md += ["", "## The model's top pairs, as ranked by the measurement", "", "| Model rank | Pair | Measured rank (of pairs scored) | N_eff measured | N_eff model |", "|---|---|---|---|---|"]
    for r in top_model:
        md.append(f"| {r['model_rank']} | {r['pair']} | {r['measured_rank']} | {r['neff_measured_a_to_b']:.1f} / {r['neff_measured_b_to_a']:.1f} | {r['neff_model_a_to_b']:.1f} / {r['neff_model_b_to_a']:.1f} |")
    md += ["", "N_eff is the effective number of channels (exp of the entropy of channel shares): about 1 means a direction runs through a single matchup. "
           "Caveats: search is not hostility; scale is Cowboys-suck units per state (assumes that anchor is similarly disliked everywhere); school terms cannot separate sports; small states are censored."]
    (ROOT / "docs/MEASURED_HOSTILITY.md").write_text(chr(10).join(md) + chr(10), encoding="utf-8", newline=chr(10))
    print(chr(10).join(md[3:30]))


if __name__ == "__main__":
    main()
