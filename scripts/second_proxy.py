"""Second proxies for the dominance of the leading pair's biggest matchup (the verdict gate asks for a second proxy; see the design note, section 7).

For the model's lead pair (a, b) the question is: among the pro matchups that link a team standing for a with a team standing for b (for
Illinois-Wisconsin: Bears-Packers, Cubs-Brewers, Bulls-Bucks), what share does the biggest matchup carry, and does the model's share agree?

  1. Comparison searches (Google, "<team> vs <team>"; a different query type on the SAME platform, so labelled as such and NOT counted by the gate
     as independent). By state, on one scale via two-term bridge batches, with measurement noise and censoring bounded as in channel_decomposition.py.
  2. Wikipedia readership of the rivalry articles (an INDEPENDENT source, but national, so it can confirm direction and rough size, not geography).

Model share = A[a,i] R[i,j] E[j,b] F[a,j] for the matchup, over the same matchups (direction a->b), renormalised. A proxy "agrees" when the model share lies
inside the measured interval or within 15 points of the measured share (Google) or when both shares are on the same side of 50% and within 15 points
(Wikipedia, national). Nothing here feeds the model. Writes data/model/second_proxy.csv and docs/SECOND_PROXY.md.

    python scripts/second_proxy.py
"""
import csv
import math
import pathlib
import sys

import numpy as np
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import lib_model as LM  # noqa: E402
import lib_trends as L  # noqa: E402
import trends_worker as TW  # noqa: E402
from channel_decomposition import share_interval  # noqa: E402

ROOT = LM.ROOT
OKF = ("ok", "anchor", "low_anchor")
CENS = OKF + ("below_detection",)
TOL = 0.15


def matchups(a, b, ents, E, bidx, eidx):
    """Curated pro pairs (both directions of the pair list) linking a team that stands for a with one that stands for b."""
    cur = yaml.safe_load(open(ROOT / "config/rivalry_curated.yaml", encoding="utf-8"))
    out = []
    for league, pairs in cur["pro"].items():
        if league not in ("nfl", "mlb", "nba", "nhl"):
            continue
        low = {e["entity_id"]: e["entity_name"].lower() for e in ents if LM.fam_of(e["entity_id"]) == league}

        def find(spec):
            c = [i for i, n in low.items() if n.endswith(" " + spec) or n == spec or (" " + spec + " ") in n or n.startswith(spec + " ")]
            if len(c) > 1:
                c = [i for i in c if low[i].endswith(" " + spec)] or c
            return c[0] if len(c) == 1 else None
        for sa, sb, _, _ in pairs:
            ia, ib = find(sa), find(sb)
            if not (ia and ib):
                continue
            term = " ".join(TW._cap(x) for x in sa.split()) + " vs " + " ".join(TW._cap(x) for x in sb.split())
            for i, j in ((ia, ib), (ib, ia)):
                if E[eidx[i], bidx[a]] >= 0.2 and E[eidx[j], bidx[b]] >= 0.2:
                    out.append({"league": league, "i": i, "j": j, "term": term})
    return out


def main(seed=23):
    states, ids, A, _ = LM.load_A()
    sidx = {s: k for k, s in enumerate(states)}
    eidx = {e: k for k, e in enumerate(ids)}
    reg = {e["entity_id"]: e for e in LM.load_entities()}
    ents = [reg[e] for e in ids]
    E, buckets = LM.build_E(ents, states)
    bidx = {b: k for k, b in enumerate(buckets)}
    R = LM.build_R(ids, [e for e in LM.build_edges() if e[0] != "UNRESOLVED"])
    F = LM.place_matrix(states, ids, ents)
    smap = L.state_map()
    lead = max(csv.DictReader(open(ROOT / "data/model/pair_uncertainty.csv", encoding="utf-8")), key=lambda r: float(r["P_rank1"]))
    a0, b0 = lead["state_a"], lead["state_b"]
    pair = f"{a0}-{b0}"
    rng = np.random.default_rng(seed)
    # comparison-search estimates per league on the NFL scale
    est, bridge = {}, {}
    for lg in ("nfl", "mlb", "nba", "nhl"):
        jobs = L.load_jobs(family=f"COS_{lg}")
        est[lg] = L.estimate(jobs, smap) if jobs else None
        if lg != "nfl":
            bj = L.load_jobs(family=f"COSB_{lg}")
            bridge[lg] = L.estimate(bj, smap) if bj else None
    rows = []
    wiki = {}
    wp = ROOT / "data/model/wikipedia_rivalry.csv"
    if wp.exists():
        for r in csv.DictReader(open(wp, encoding="utf-8")):
            wiki[r["pair"]] = int(r["views_rivalry"])
    for a, b in ((a0, b0), (b0, a0)):
        ms = matchups(a, b, ents, E, bidx, eidx)
        if len(ms) < 2:
            continue
        # unique matchups (by term) with model contributions summed over the supported-team direction a -> b
        by = {}
        for m in ms:
            c = float(A[sidx[a], eidx[m["i"]]] * R[eidx[m["i"]], eidx[m["j"]]] * E[eidx[m["j"]], bidx[b]] * F[sidx[a], eidx[m["j"]]])
            by.setdefault(m["term"], {"league": m["league"], "model": 0.0, "pair": (reg[m["i"]]["entity_name"], reg[m["j"]]["entity_name"])})["model"] += c
        tot = sum(v["model"] for v in by.values())
        if tot <= 0:
            continue
        top = max(by, key=lambda t: by[t]["model"])
        c_model = by[top]["model"] / tot
        # --- proxy 1: comparison searches in state a
        vals, var, cens = {}, {}, {}
        for t, v in by.items():
            lg = v["league"]
            if est[lg] is None or (lg != "nfl" and bridge.get(lg) is None):
                continue
            e = est[lg].get((t, a, "W5"))
            if not (e and e[2] in CENS):
                continue
            scale, svar = 1.0, 0.0
            if lg != "nfl":
                bb = bridge[lg].get((TW.COS_ANCHORS[lg][0], a, "W5"))
                if not (bb and bb[2] in OKF):
                    continue
                scale, svar = math.exp(bb[0]), bb[1]
            vals[t], var[t], cens[t] = math.exp(e[0]) * scale, e[1] + svar, e[2] == "below_detection"
        if len(vals) >= 2 and top in vals:
            units = sorted(vals)
            iv = share_interval(units, vals, var, cens, top, None, rng)
            agrees = (iv[1] <= c_model <= iv[2]) or abs(iv[0] - c_model) <= TOL
            rows.append({"pair": pair, "direction": f"{a}->{b}", "proxy": "Google comparison searches ('A vs B')", "independence": "same platform, different query type (not counted as independent)",
                         "matchups": len(units), "model_top": by[top]["pair"][0] + " vs " + by[top]["pair"][1], "model_share": round(c_model, 3),
                         "measured_share": round(iv[0], 3), "lo": round(iv[1], 3), "hi": round(iv[2], 3), "agrees": agrees})
        # --- proxy 2: Wikipedia readership (national)
        wv = {}
        for t, v in by.items():
            n1, n2 = v["pair"]
            key = next((k for k in wiki if (n1 in k and n2 in k)), None)
            if key:
                wv[t] = wiki[key]
        if len(wv) >= 2 and top in wv:
            sh = wv[top] / sum(wv.values())
            msh = by[top]["model"] / sum(by[t]["model"] for t in wv)
            agrees = (sh >= 0.5) == (msh >= 0.5) and abs(sh - msh) <= TOL
            rows.append({"pair": pair, "direction": f"{a}->{b} (national readership)", "proxy": "Wikipedia rivalry-article readership, 2021 to 2025",
                         "independence": "independent source (national, no geography)", "matchups": len(wv), "model_top": by[top]["pair"][0] + " vs " + by[top]["pair"][1],
                         "model_share": round(msh, 3), "measured_share": round(sh, 3), "lo": "", "hi": "", "agrees": agrees})
    if not rows:
        print("nothing computable yet")
        return
    with open(ROOT / "data/model/second_proxy.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator=chr(10))
        w.writeheader()
        w.writerows(rows)
    md = ["# Second proxies for the dominance of the lead pair's biggest matchup", "",
          f"Auto-generated by `scripts/second_proxy.py` for the lead pair **{pair}**. Among the pro matchups linking a team standing for each state, the share carried by the biggest matchup, "
          "model versus measurement. A Google comparison-search proxy (same platform, different query type; not counted as independent) and a Wikipedia readership proxy "
          "(independent source, national, no geography).", "",
          "| Direction | Proxy | Independence | Matchups | Model's biggest matchup | Model share | Measured share (interval) | Agrees |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        iv = f" ({float(r['lo']):.0%} to {float(r['hi']):.0%})" if r["lo"] != "" else ""
        md.append(f"| {r['direction']} | {r['proxy']} | {r['independence']} | {r['matchups']} | {r['model_top']} | {r['model_share']:.0%} | {r['measured_share']:.0%}{iv} | {'yes' if r['agrees'] else 'no'} |")
    md += ["", "Caveats: the matchup set is the curated pro list (college matchups are not included); Wikipedia readership is national and reflects reading, not hostility; "
           "shares are within the matchups listed; censored comparison-search cells are bounded, never zero."]
    (ROOT / "docs/SECOND_PROXY.md").write_text(chr(10).join(md) + chr(10), encoding="utf-8", newline=chr(10))
    print(chr(10).join(md[5:]))


if __name__ == "__main__":
    main()
