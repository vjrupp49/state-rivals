"""Phase 4B steps 13, 15-17, 20: sport-level attention W_sk, then A = W x P.

W_sk: Trends sport-level terms (anchored NFL+MLB batches, recency-blended) combined
with national survey priors N_k as a weighted geometric ensemble (docs/PROTOCOL.md
section 8). beta weights are PROVISIONAL per D-012 (beta_G=0.7, beta_N=0.3);
sensitivity sweeps live in robustness.py. Where a source is missing for a sport
it is dropped and the remainder renormalized (never zero). Sports we measure but
have not registered (volleyball, wrestling, lacrosse) are the visible OTHER mass.
If no sport-level Trends data exists yet, W falls back to national priors and is
flagged 'fallback_national_prior' (Low confidence).

Outputs: data/model/attention_sport.csv, A_matrix.csv (wide, states x entities + OTHER),
         A_meta.csv (long: confidence / logsd / active flag), A_audit.json
"""
import csv
import json
import math
import sys
import pathlib
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import lib_trends as L

ROOT = L.ROOT
MODEL = ROOT / "data" / "model"
# Original literal-phrase terms (kept as a robustness variant): the independent review of 2026-10-16 found they gave college sports almost no weight
# (college basketball 0.002 vs NFL 0.37). The default now uses Google topic ids, which aggregate every phrasing people use.
SPORT_TERM_PHRASE = {"nfl": "NFL", "cfb": "college football", "mlb": "MLB", "nba": "NBA",
              "cbb_m": "men's college basketball", "cbb_w": "women's college basketball",
              "nhl": "NHL", "mls": "MLS", "wnba": "WNBA", "nwsl": "NWSL", "pwhl": "PWHL",
              "hky_m": "men's college hockey", "hky_w": "women's college hockey",
              "bsb": "college baseball", "sfb": "college softball", "vbw": "college volleyball",
              "lax": "lacrosse", "wrs": "college wrestling"}
SPORT_TERM_TOPIC = dict(SPORT_TERM_PHRASE, **{
    "cfb": "/m/01zff", "cbb_m": "/m/02jp2w", "cbb_w": "/g/11dxbvlspv", "bsb": "/m/04xc_d", "sfb": "/m/05v_4b", "vbw": "/m/0wxw0fp",
    "wrs": "/m/05gvj2", "lax": "/m/02qdfyt", "hky_m": "/g/11spflhcxj", "hky_w": "/m/02p5ty"})   # resolved with the suggestions endpoint, 2026-10-16
SPORT_TERM = SPORT_TERM_TOPIC
UNREG = {}   # every sport with a Trends term is now a registered family
N_PRIOR = {"nfl": 0.43, "mlb": 0.29, "nba": 0.24, "nhl": 0.17, "cfb": 0.43 * 0.55}
FALLBACK_DEFAULT = 0.04
BETA_G, BETA_N = 0.7, 0.3
MIN_COVERAGE = 0.5   # below this a family is treated as unmeasured: its W mass goes to OTHER, not a made-up split


def sport_G(smap):
    jobs = [j for j in L.load_jobs(family="SPORT")]
    if not jobs:
        return None
    est = L.estimate(jobs, smap)
    out = {}
    for sid in smap.values():
        for key, term in {**SPORT_TERM, **UNREG}.items():
            b = L.blend_windows(est, term, sid)
            out[(sid, key)] = b
    return out


def build_W(beta_g=BETA_G, beta_n=BETA_N, smap=None, G=None):
    smap = smap or L.state_map()
    G = G if G is not None else sport_G(smap)
    keys = list(SPORT_TERM) + list(UNREG)
    if G:
        have = [k for k in keys if any(G.get((s2, k)) and G[(s2, k)]["G_P"] is not None for s2 in smap.values())]
        missing_sports = [k for k in keys if k not in have]
        # a sport with no Trends data in any state (e.g. lacrosse if its batch never completed) is excluded
        # from the mix and reported; registered sports never reach this branch silently (fallback path catches them)
        if any(k in SPORT_TERM for k in missing_sports):
            G = None
        else:
            keys = have
            build_W.missing = missing_sports
    W, meta = {}, {}
    nsum = sum(N_PRIOR.values())
    for sid in smap.values():
        g = {}
        for k in keys:
            b = G.get((sid, k)) if G else None
            g[k] = b["G_P"] if b and b["G_P"] is not None else None
        # impute missing sport volume by across-state mean for that sport
        if G:
            for k in keys:
                if g[k] is None:
                    vals = [G[(s2, k)]["G_P"] for s2 in smap.values() if G.get((s2, k)) and G[(s2, k)]["G_P"] is not None]
                    g[k] = sum(vals) / len(vals) if vals else None
        if not G or any(v is None for v in g.values()):
            raw = {k: (N_PRIOR.get(k, FALLBACK_DEFAULT)) for k in keys}
            tot = sum(raw.values())
            W[sid] = {k: raw[k] / tot for k in keys}
            meta[sid] = "fallback_national_prior"
            continue
        tot = sum(g.values())
        gs = {k: g[k] / tot for k in keys}
        sub = [k for k in keys if k in N_PRIOR]
        m = sum(gs[k] for k in sub)
        comb = {k: (gs[k] ** beta_g) * ((N_PRIOR[k] / nsum) ** beta_n) for k in sub}
        ct = sum(comb.values())
        w = dict(gs)
        for k in sub:
            w[k] = m * comb[k] / ct
        tw = sum(w.values())
        W[sid] = {k: w[k] / tw for k in keys}
        meta[sid] = "trends+national_prior"
    return W, meta


def main(beta_g=BETA_G, beta_n=BETA_N, p_path=None, model=None, quiet=False, flat_w=False, term_set="topic"):
    global SPORT_TERM
    SPORT_TERM = SPORT_TERM_PHRASE if term_set == "phrase" else SPORT_TERM_TOPIC
    MODEL_D = model or MODEL
    smap = L.state_map()
    W, wmeta = build_W(beta_g, beta_n, smap=smap)
    if flat_w:
        W = {sid: {k: 1.0 / len(d) for k in d} for sid, d in W.items()}
    MODEL_D.mkdir(parents=True, exist_ok=True)
    with open(MODEL_D / "attention_sport.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["state_id", "sport", "W", "method"])
        for sid, d in W.items():
            for k, v in d.items():
                w.writerow([sid, k, f"{v:.6f}", wmeta[sid]])
    # A = W x P
    P = {}
    meta_rows = []
    with open(p_path or (MODEL / "attention_team.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            P[(r["state_id"], r["entity_id"])] = r
    ents = list(dict.fromkeys(e for (_, e) in P))
    fam_of = {e: r['family'] for (_, e), r in P.items()}
    states = sorted(smap.values())
    # family measured-ness: share of entity-state cells with real (non-imputed) Trends/county signal
    tot_c, meas_c = defaultdict(int), defaultdict(int)
    for (sid_, e_), r_ in P.items():
        tot_c[r_["family"]] += 1
        meas_c[r_["family"]] += 0 if r_["flag"] == "imputed" else 1
    tr_c = defaultdict(int)
    for (sid_, e_), r_ in P.items():
        tr_c[r_['family']] += 0 if r_['flag'] in ('imputed', 'county_only') else 1
    det_c = defaultdict(int)
    for (sid_, e_), r_ in P.items():
        det_c[r_['family']] += 1 if r_['flag'] in ('ok', 'anchor', 'low_anchor') else 0     # detected (not censored) cells only
    fam_ok = {f_: meas_c[f_] / tot_c[f_] >= MIN_COVERAGE for f_ in tot_c}
    audit_cov = {f_: round(meas_c[f_] / tot_c[f_], 3) for f_ in tot_c}
    A = {}
    maxA = defaultdict(float)
    for sid in states:
        row = {}
        for e in ents:
            r = P[(sid, e)]
            a = W[sid][r["family"]] * float(r["P"]) if fam_ok[r["family"]] else 0.0
            row[e] = a
            maxA[e] = max(maxA[e], a)
            meta_rows.append((sid, e, r["family"], a, r["confidence"], r["logsd"], r["flag"]))
        row["OTHER"] = sum(W[sid][k] for k in UNREG) + sum(W[sid][f_] for f_ in fam_ok if not fam_ok[f_])
        A[sid] = row
    audit = {"states": len(states), "entities": len(ents), "row_sum_max_err": 0.0,
             "states_other_gt_2pct": [], "w_method_counts": {}, "family_coverage": audit_cov,
             "families_unmeasured_to_OTHER": [f_ for f_ in fam_ok if not fam_ok[f_]],
             "family_trends_coverage": {f_: round(tr_c[f_] / tot_c[f_], 3) for f_ in tot_c},
             "family_detected_coverage": {f_: round(det_c[f_] / tot_c[f_], 3) for f_ in tot_c}}
    for sid in states:
        s = sum(A[sid].values())
        audit["row_sum_max_err"] = max(audit["row_sum_max_err"], abs(s - 1))
        if A[sid]["OTHER"] > 0.02:
            audit["states_other_gt_2pct"].append(sid)
    for m in wmeta.values():
        audit["w_method_counts"][m] = audit["w_method_counts"].get(m, 0) + 1
    with open(MODEL_D / "A_matrix.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["state_id"] + ents + ["OTHER"])
        for sid in states:
            w.writerow([sid] + [f"{A[sid][e]:.14g}" for e in ents] + [f"{A[sid]['OTHER']:.14g}"])
    with open(MODEL_D / "A_meta.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["state_id", "entity_id", "family", "A", "confidence", "logsd", "flag", "active_entity"])
        for sid, e, fam, a, conf, sd, flag in meta_rows:
            w.writerow([sid, e, fam, f"{a:.8g}", conf, sd, flag, int(maxA[e] >= 0.0025)])
    (MODEL_D / "A_audit.json").write_text(json.dumps(audit, indent=1), encoding="utf-8")
    if not quiet:
        print(json.dumps(audit))
    return audit


if __name__ == "__main__":
    main()
