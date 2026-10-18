"""Evaluate the M3 co-search pilot: do "A vs B" searches measure rivalry salience usefully?

For every curated pro rivalry pair with a completed co-search batch it reports, in units of the league's
first anchor pair: the population-weighted national interest, the interest in each team's home state, and
how many states show any signal. It then checks against the analyst tiers (Spearman) and the shape we expect
(interest should concentrate in the two teams' home states). Output: data/model/cosearch_pilot.csv and
docs/COSEARCH_PILOT.md. Nothing here feeds the model yet; this decides whether and how it should.

    python scripts/cosearch_pilot.py
"""
import csv
import math
import pathlib
import sys

import numpy as np
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import lib_trends as L  # noqa: E402
import lib_model as LM  # noqa: E402
import trends_worker as TW  # noqa: E402

ROOT = L.ROOT


def spearman(a, b):
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    return float(np.corrcoef(ra, rb)[0, 1]) if len(a) > 2 else float("nan")


def main():
    smap = L.state_map()
    cur = yaml.safe_load(open(ROOT / "config/rivalry_curated.yaml", encoding="utf-8"))
    ents = LM.load_entities()
    rows, summary = [], []
    for league in ("nfl", "mlb", "nba", "nhl"):
        jobs = L.load_jobs(family=f"COS_{league}")
        if not jobs:
            continue
        est = L.estimate(jobs, smap)
        names = {e["entity_id"]: e for e in ents if LM.fam_of(e["entity_id"]) == league}
        low = {i: e["entity_name"].lower() for i, e in names.items()}

        def find(spec):
            c = [i for i, n in low.items() if n.endswith(" " + spec) or n == spec or (" " + spec + " ") in n or n.startswith(spec + " ")]
            if len(c) > 1:
                c = [i for i in c if low[i].endswith(" " + spec)] or c
            return c[0] if len(c) == 1 else None

        # Values are in units of the batch anchor IN THE SAME STATE, so they are only comparable across terms within
        # one state (the anchor cancels in ratios). The usable question is therefore: in a team's home state, how do
        # its rivals rank by co-search interest, and does that agree with the analyst tier?
        rivals = {}
        for a, b, ta, tb in cur["pro"][league]:
            term = " ".join(TW._cap(x) for x in a.split()) + " vs " + " ".join(TW._cap(x) for x in b.split())
            ia, ib = find(a), find(b)
            if ia and ib:
                rivals.setdefault(ia, []).append((ib, term, ta))
                rivals.setdefault(ib, []).append((ia, term, tb))
        rhos, top_agree, n_teams = [], 0, 0
        for i, lst in rivals.items():
            st = names[i]["home_state"]
            vals = []
            for j, term, tier in lst:
                e = est.get((term, st, "W5"))
                if e and e[2] in ("ok", "anchor", "low_anchor"):
                    vals.append((j, term, tier, math.exp(e[0])))
            if len(vals) < 2:
                continue
            tot = sum(v[3] for v in vals)
            for j, term, tier, v in vals:
                rows.append({"league": league, "team": names[i]["entity_name"], "home_state": st, "rival": names[j]["entity_name"],
                             "analyst_tier": tier, "measured_value": round(v, 4), "measured_share_among_rivals": round(v / tot, 4)})
            if len({v[2] for v in vals}) > 1:
                rhos.append(spearman([v[3] for v in vals], [-v[2] for v in vals]))
                n_teams += 1
                best_tier = min(v[2] for v in vals)
                top_agree += int(max(vals, key=lambda v: v[3])[2] == best_tier)
        summary.append((league, n_teams, float(np.nanmean(rhos)) if rhos else float("nan"), top_agree / n_teams if n_teams else float("nan")))
    # college: school-level pairs; analyst tier = football tier in each direction (school's home state from the basketball registry)
    jobs = L.load_jobs(family="COS_col")
    if jobs:
        est = L.estimate(jobs, smap)
        home = {}
        for e in ents:
            if e["entity_id"].startswith("cbb_m_"):
                home[e["entity_name"].replace(" Men's Basketball", "")] = e["home_state"]
        riv = {}
        for a_, b_, fa, fb, bb, _ in cur["college"]:
            term = f"{a_} vs {b_}"
            if a_ in home and b_ in home:
                riv.setdefault(a_, []).append((b_, term, min(fa, bb)))
                riv.setdefault(b_, []).append((a_, term, min(fb, bb)))
        rhos, top_agree, n_teams = [], 0, 0
        for sch, lst in riv.items():
            vals = []
            for r_, term, tier in lst:
                e = est.get((term, home[sch], "W5"))
                if e and e[2] in ("ok", "anchor", "low_anchor"):
                    vals.append((r_, term, tier, math.exp(e[0])))
            if len(vals) < 2:
                continue
            tot = sum(v[3] for v in vals)
            for r_, term, tier, v in vals:
                rows.append({"league": "col", "team": sch, "home_state": home[sch], "rival": r_, "analyst_tier": tier,
                             "measured_value": round(v, 4), "measured_share_among_rivals": round(v / tot, 4)})
            if len({v[2] for v in vals}) > 1:
                rhos.append(spearman([v[3] for v in vals], [-v[2] for v in vals]))
                n_teams += 1
                top_agree += int(max(vals, key=lambda v: v[3])[2] == min(v[2] for v in vals))
        summary.append(("col", n_teams, float(np.nanmean(rhos)) if rhos else float("nan"), top_agree / n_teams if n_teams else float("nan")))
    if not rows:
        print("no co-search jobs completed yet")
        return
    with open(ROOT / "data/model/cosearch_pilot.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator=chr(10))
        w.writeheader()
        w.writerows(rows)
    md = ["# Co-search pilot", "",
          "Auto-generated by `scripts/cosearch_pilot.py`. Question: do 'A vs B' searches measure *which rival matters most* to a team's fans, well enough to inform the rivalry layer? "
          "The model uses it only for the *split* of each team's rivalry salience among its rivals (`cosearch_blend`, one weight per league, capped at 0.4, set to 0 for the NHL where the pilot did not support it); row totals and temperatures are untouched.", "",
          "**Design note.** Trends returns each term as a share of the batch in the same state, so values are in units of a reference matchup *in that state* and are comparable only across terms within one state, "
          "not across states. The pilot therefore tests the within-team ranking of rivals in the team's home state (the anchor cancels in ratios). Measuring the *total* rivalry mass of a team would need a different design.", "",
          "| League | Teams tested | Mean within-team Spearman (measured vs analyst tier) | Top measured rival is a top-tier rival |", "|---|---|---|---|"]
    for lg, n, rho, top in summary:
        md.append(f"| {lg} | {n} | {rho:.2f} | {top:.0%} |")
    md += ["", "A positive Spearman means that, within a team, the rival people search for most with the team is also the rival the analyst tier ranks highest. "
           "Per-team detail: `data/model/cosearch_pilot.csv`."]
    (ROOT / "docs/COSEARCH_PILOT.md").write_text(chr(10).join(md) + chr(10), encoding="utf-8", newline=chr(10))
    print(chr(10).join(md[8:]))


if __name__ == "__main__":
    main()
