"""Does a team really stand for its state? A first measurement of the identity layer E (open item 2 in output/verdict.json).

The model assumes hostility toward a team becomes hostility toward its home state (E = 0.95 by default, with documented exceptions). If a team
embodies its state, then states that dislike the team should also dislike the state. Using only searches:

    team side   v[s, u]  : interest in '<team or school> suck' in observing state s (Cowboys-suck units per state)
    state side  D[s, b]  : interest in '<state> sucks' in observing state s (the independent top-down measurement)

Because each state has its own overall search level and its own anchor scale, both are demeaned within state across all teams (or all target
states) before comparing. The embodiment index of unit u with home state b is the correlation, across observing states s other than b, between
the demeaned team antipathy and the demeaned state antipathy. Near 1: hostility toward the team and toward its state move together (the team stands
for the state). Near 0: they are unrelated (a brand, or a team that stands for a city). Needs at least 10 observing states. Schools named exactly like their state (Texas, Michigan, Ohio ...) are skipped: their search term is identical to the state term, so the index would be 1 by construction.

This is a diagnostic: it does not change E. Writes data/model/embodiment_check.csv and docs/EMBODIMENT_CHECK.md.

    python scripts/embodiment_check.py
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
OKF = ("ok", "anchor", "low_anchor")
SUFFIXES = (" Men's Basketball", " Women's Basketball", " Men's Ice Hockey", " Women's Ice Hockey", " Baseball", " Softball",
            " Women's Volleyball", " Men's Lacrosse", " Women's Lacrosse", " Wrestling")


def main():
    states, ids, A, _ = LM.load_A()
    reg = {e["entity_id"]: e for e in LM.load_entities()}
    smap = L.state_map()
    name_of = {v: k for k, v in smap.items()}
    out = LMS.measurements(smap, reg)
    if out is None:
        print("bridges not ready")
        return
    v, unit_name, school_of_cfb = out
    est = L.estimate(L.load_jobs(family="TOPDOWN"), smap)
    sids = sorted(smap.values())
    D = {}
    for s in sids:
        for b in sids:
            e = est.get((f"{name_of[b]} sucks", s, "W5"))
            if s != b and e and e[2] in OKF:
                D[(s, b)] = e[0]
    # demean ln values within observing state
    lv = {k: math.log(x) for k, x in v.items()}
    mean_v = {s: np.mean([x for (ss, _), x in lv.items() if ss == s]) for s in sids if any(ss == s for ss, _ in lv)}
    mean_d = {s: np.mean([x for (ss, _), x in D.items() if ss == s]) for s in sids if any(ss == s for ss, _ in D)}
    homes = {}
    for eid in ids:
        e = reg[eid]
        if e["professional_college"] != "college":
            homes["pro:" + eid] = e["home_state"]
        elif eid.startswith("cfb_"):
            homes["sch:" + school_of_cfb.get(eid, "")] = e["home_state"]
    for k in set(u for _, u in v):
        if k.startswith("sch:") and k not in homes:
            ent = next((e for e in reg.values() if e["entity_name"].startswith(k[4:] + " ")), None)
            if ent:
                homes[k] = ent["home_state"]
    rows = []
    for u in sorted(set(u for _, u in v)):
        b = homes.get(u)
        if b not in sids:
            continue
        if u.startswith("sch:") and name_of.get(b) == u[4:]:
            continue                       # state-named school ('Texas sucks' is also the state term): identical by construction
        xs, ys = [], []
        for s in sids:
            if s == b or (s, u) not in lv or (s, b) not in D or s not in mean_v or s not in mean_d:
                continue
            xs.append(lv[(s, u)] - mean_v[s])
            ys.append(D[(s, b)] - mean_d[s])
        if len(xs) < 10:
            continue
        rho = float(np.corrcoef(xs, ys)[0, 1])
        rows.append({"unit": unit_name[u], "kind": "pro" if u.startswith("pro:") else "school", "home_state": b, "observing_states": len(xs), "embodiment_index": round(rho, 3)})
    rows.sort(key=lambda r: -r["embodiment_index"])
    with open(ROOT / "data/model/embodiment_check.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator=chr(10))
        w.writeheader()
        w.writerows(rows)
    pro = [r["embodiment_index"] for r in rows if r["kind"] == "pro"]
    sch = [r["embodiment_index"] for r in rows if r["kind"] == "school"]
    brands = ["Los Angeles Lakers", "Boston Celtics", "New York Yankees", "Dallas Cowboys", "Green Bay Packers", "Chicago Bears", "New England Patriots", "Minnesota Vikings",
              "Pittsburgh Steelers", "Seattle Seahawks", "Philadelphia Eagles", "Golden State Warriors"]
    pick = [r for r in rows if r["unit"] in brands]
    missing = [b for b in brands if b not in {r["unit"] for r in rows}]
    md = ["# Does a team stand for its state? (first measurement of the identity layer)", "",
          "Auto-generated by `scripts/embodiment_check.py`. Embodiment index = correlation, across observing states, between antipathy toward a team or school "
          "and antipathy toward its home state ('<state> sucks'), after removing each state's overall level. Near 1: the team stands for the state; near 0: they are unrelated "
          "(a brand, or a team that stands for a city). The model currently assumes 0.95 for nearly every team. This is a diagnostic; it does not change the model.", "",
          f"Pro teams: median **{np.median(pro):.2f}** (n={len(pro)}). College schools: median **{np.median(sch):.2f}** (n={len(sch)}).", "",
          "| Team or school | Home state | Observing states | Embodiment index |", "|---|---|---|---|"]
    for r in pick:
        md.append(f"| {r['unit']} | {r['home_state']} | {r['observing_states']} | {r['embodiment_index']:+.2f} |")
    md += ["", "Not enough observing states to compute (fewer than 10 states with usable data for both the team and its state): " + (", ".join(missing) or "none") + "."]
    md += ["", "Highest and lowest among all units:", "", "| | Unit | Home | Index |", "|---|---|---|---|"]
    for lab, grp in (("Highest", rows[:8]), ("Lowest", rows[-8:])):
        for r in grp:
            md.append(f"| {lab} | {r['unit']} | {r['home_state']} | {r['embodiment_index']:+.2f} |")
    md += ["", "Caveats: neighboring states dislike both a team and its state for shared reasons (regional rivalry), which is part of what identity means here; "
           "'<state> sucks' is not only about sports ('New York', 'Washington' are ambiguous); the index is noisy for small teams; the full table is in `data/model/embodiment_check.csv`."]
    (ROOT / "docs/EMBODIMENT_CHECK.md").write_text(chr(10).join(md) + chr(10), encoding="utf-8", newline=chr(10))
    print(chr(10).join(md[5:30]))


if __name__ == "__main__":
    main()
