"""Validate the model's directed hostility against measured team-level antipathy searches ("<team> suck").

Measured: Google Trends co-batch values per state, in units of the batch anchor in the SAME state, so they are
comparable across teams within a state (the anchor cancels) but not across states for one team directly. We
therefore use rank-based and within-state-normalised comparisons only.

Model: hostility toward team j from state s, Hm[s, j] = sum_i A[s, i] * R[i, j] (what the model says residents of s
feel toward j through the rivals they support).

Own-state teams are excluded cell by cell (a team that carries >= 20% of a state's identity in E): the model ignores in-state
hostility, and '<own team> suck' is mostly fans complaining about their own team.

Two questions, both reported with Spearman correlations:
  1. Within a state, do the teams people search "suck" for most match the teams the model says that state is most
     hostile to?  (across teams, per state, then averaged)
  2. Pooled over states, after removing each team's overall (national) level, does the geography of antipathy match the
     model's geography?  (a team that is hated everywhere, like the Cowboys, is not a test of local rivalry)

Nothing here feeds the model. It is a validation (M4) and a source for later calibration of S and T totals.
Writes data/model/hate_validation.csv and docs/HATE_VALIDATION.md.

    python scripts/hate_validation.py
"""
import csv
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import lib_model as LM  # noqa: E402
import lib_trends as L  # noqa: E402
import trends_worker as TW  # noqa: E402

ROOT = LM.ROOT


def rank(v):
    return np.argsort(np.argsort(v)).astype(float)


def spear(a, b):
    if len(a) < 4:
        return float("nan")
    ra, rb = rank(np.asarray(a)), rank(np.asarray(b))
    if ra.std() == 0 or rb.std() == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def main():
    states, ids, A, _ = LM.load_A()
    sidx = {s: k for k, s in enumerate(states)}
    reg = {e["entity_id"]: e for e in LM.load_entities()}
    ents = [reg[e] for e in ids]
    R = LM.build_R(ids, [e for e in LM.build_edges() if e[0] != "UNRESOLVED"])
    Hm = A @ R                                   # state x entity: hostility toward each entity
    E, buckets = LM.build_E(ents, states)
    bidx = {b: k for k, b in enumerate(buckets)}

    def own(sid, eid):
        """True if team eid substantially embodies state sid (own-state teams: the model ignores in-state hostility,
        and '<own team> suck' is mostly fans complaining, so these cells are not comparable)."""
        return E[eidx[eid], bidx[sid]] >= 0.2
    eidx = {e: k for k, e in enumerate(ids)}
    smap = L.state_map()
    rows, summ = [], []
    for league in ("nfl", "mlb", "nba", "nhl"):
        jobs = L.load_jobs(family=f"HATE_{league}")
        if not jobs:
            continue
        est = L.estimate(jobs, smap)
        terms = TW._hate_terms(league)
        meas = {}                               # (state, entity) -> value
        for eid, term in terms.items():
            for sid in smap.values():
                e = est.get((term, sid, "W5"))
                if e and e[2] in ("ok", "anchor", "low_anchor") and not own(sid, eid):
                    meas[(sid, eid)] = math.exp(e[0])
        teams = sorted({eid for _, eid in meas})
        if len(teams) < 6:
            continue
        # 1. within state across teams
        per_state = []
        for sid in smap.values():
            tt = [t for t in teams if (sid, t) in meas]
            if len(tt) >= 8:
                per_state.append(spear([meas[(sid, t)] for t in tt], [Hm[sidx[sid], eidx[t]] for t in tt]))
        # 2. pooled geography after removing each team's mean log level (measured) and mean log level (model)
        xs, ys = [], []
        for t in teams:
            ss = [sid for sid in smap.values() if (sid, t) in meas and Hm[sidx[sid], eidx[t]] > 0]
            if len(ss) < 10:
                continue
            lm = np.log([meas[(sid, t)] for sid in ss])
            lh = np.log([Hm[sidx[sid], eidx[t]] for sid in ss])
            xs += list(lm - lm.mean())
            ys += list(lh - lh.mean())
            rows.append({"league": league, "team": reg[t]["entity_name"], "states": len(ss),
                         "within_team_geography_spearman": round(spear(lm, lh), 3)})
        pooled = spear(xs, ys) if xs else float("nan")
        within_team = [r["within_team_geography_spearman"] for r in rows if r["league"] == league and not math.isnan(r["within_team_geography_spearman"])]
        summ.append((league, len(teams), len(per_state), float(np.nanmean(per_state)) if per_state else float("nan"),
                     pooled, float(np.nanmean(within_team)) if within_team else float("nan")))
    if not summ:
        print("no hate-search jobs completed yet")
        return
    with open(ROOT / "data/model/hate_validation.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["league", "team", "states", "within_team_geography_spearman"], lineterminator=chr(10))
        w.writeheader()
        w.writerows(rows)
    md = ["# Antipathy-search validation", "",
          "Auto-generated by `scripts/hate_validation.py`. Measured: state-level interest in '<team> suck' (Google Trends, 5-year window), compared with the hostility "
          "the model assigns to each team from each state. Nothing here feeds the model.", "",
          "| League | Teams measured | States tested | Mean within-state Spearman (teams) | Pooled geography Spearman | Mean within-team Spearman (states) |", "|---|---|---|---|---|---|"]
    for lg, nt, ns, ps, pooled, wt in summ:
        md.append(f"| {lg} | {nt} | {ns} | {ps:.2f} | {pooled:.2f} | {wt:.2f} |")
    md += ["", "Reading: a positive within-state Spearman means that, in a typical state, the teams people most often call out as bad are the teams the model says that state is most hostile to. "
           "The pooled and within-team columns remove each team's national level (a team hated everywhere, like the Cowboys, is not a test of local rivalry) and ask whether the *geography* of antipathy matches the model's. "
           "Antipathy searches also capture non-rivalry dislike (winning, arrogance, fan behavior), so perfect agreement is not expected; a clearly positive value supports the structure, a near-zero value is a finding about the model.",
           "", "Per-team detail: `data/model/hate_validation.csv`."]
    (ROOT / "docs/HATE_VALIDATION.md").write_text(chr(10).join(md) + chr(10), encoding="utf-8", newline=chr(10))
    print(chr(10).join(md[4:]))


if __name__ == "__main__":
    main()
