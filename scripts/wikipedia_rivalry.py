"""Independent second source: Wikipedia reading of rivalry articles versus the analyst rivalry tiers (open item 3 in output/verdict.json).

Nothing from Google is used here. For every curated pro rivalry that has a Wikipedia article ('Bears-Packers rivalry'), take the article's
page views (en.wikipedia, all access, user traffic, 2021-2025) and divide by the geometric mean of the two teams' own article views, which removes
team popularity: rivalry interest = views(rivalry) / sqrt(views(team i) * views(team j)). Then ask whether the analyst tier explains it:

    ln(rivalry interest) = league effect + b2 * [tier 2] + b3 * [tier 3] + error     (tier = the stronger of the two directed tiers)

exp(b2) and exp(b3) are the readers' version of the tier ladder (analyst salience times temperature: tier 2 = 0.38, tier 3 = 0.11 of tier 1;
Google antipathy fit for the NFL: 0.41 and 0.11). National only (no state detail), reading is not hostility, and only pairs that have an article are measured.
Raw API responses are cached under data/raw/_cache (git-ignored). Writes data/model/wikipedia_rivalry.csv and docs/WIKIPEDIA_RIVALRY.md.

    python scripts/wikipedia_rivalry.py
"""
import csv
import json
import math
import pathlib
import re
import sys
import time

import numpy as np
import requests
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import lib_model as LM  # noqa: E402

ROOT = LM.ROOT
CACHE = ROOT / "data" / "raw" / "_cache" / "wikipedia"
UA = {"User-Agent": "StateRivalsResearch/0.1 (academic research; contact via GitHub repo)"}
API = "https://en.wikipedia.org/w/api.php"
PV = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{t}/monthly/20210101/20251231"


def cached(key, fn):
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / (re.sub(r"[^A-Za-z0-9_.-]", "_", key)[:150] + ".json")
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    val = fn()
    if val is not None:                      # do not cache failures
        p.write_text(json.dumps(val), encoding="utf-8")
    time.sleep(0.3)                          # be polite to the Wikimedia APIs
    return val


def get_json(url, **kw):
    for attempt in range(5):
        r = requests.get(url, headers=UA, timeout=30, **kw)
        if r.status_code == 200:
            try:
                return r.json()
            except ValueError:
                pass
        if r.status_code == 404:
            return {}
        time.sleep(3 * (attempt + 1))        # throttled or transient: wait and retry, never hammer
    return None


def search(q):
    d = get_json(API, params={"action": "query", "list": "search", "srsearch": q, "srlimit": 5, "format": "json"})
    return None if d is None else [x["title"] for x in d.get("query", {}).get("search", [])]


def views(title):
    d = get_json(PV.format(t=requests.utils.quote(title.replace(" ", "_"), safe="")))
    if d is None:
        return None
    return sum(x["views"] for x in d.get("items", [])) or None


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def main():
    cur = yaml.safe_load(open(ROOT / "config/rivalry_curated.yaml", encoding="utf-8"))
    ents = LM.load_entities()
    rows = []
    for league, pairs in cur["pro"].items():
        if league not in ("nfl", "mlb", "nba", "nhl"):
            continue
        names = {e["entity_id"]: e["entity_name"] for e in ents if LM.fam_of(e["entity_id"]) == league}
        low = {i: n.lower() for i, n in names.items()}

        def find(spec):
            c = [i for i, n in low.items() if n.endswith(" " + spec) or n == spec or (" " + spec + " ") in n or n.startswith(spec + " ")]
            if len(c) > 1:
                c = [i for i in c if low[i].endswith(" " + spec)] or c
            return c[0] if len(c) == 1 else None

        for a, b, ta, tb in pairs:
            ia, ib = find(a), find(b)
            if not (ia and ib):
                continue
            na, nb = a.replace(" ", ""), b.replace(" ", "")
            res = cached(f"search_{league}_{a}_{b}", lambda: search(f"{a} {b} rivalry"))
            title = next((t for t in (res or []) if "rivalry" in t.lower() and na in norm(t) and nb in norm(t)), None)
            if not title:
                continue
            vr = cached("pv_" + title, lambda: views(title))
            va = cached("pv_" + names[ia], lambda: views(names[ia]))
            vb = cached("pv_" + names[ib], lambda: views(names[ib]))
            if not (vr and va and vb):
                continue
            rows.append({"league": league, "pair": f"{names[ia]} vs {names[ib]}", "article": title, "tier": min(ta, tb), "views_rivalry": vr, "views_team_a": va, "views_team_b": vb,
                         "interest": round(vr / math.sqrt(va * vb), 5)})
    if len(rows) < 20:
        print("too few rivalry articles resolved", len(rows))
        return
    with open(ROOT / "data/model/wikipedia_rivalry.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator=chr(10))
        w.writeheader()
        w.writerows(rows)
    leagues = sorted({r["league"] for r in rows})
    X = np.array([[1.0 if r["league"] == lg else 0.0 for lg in leagues] + [1.0 if r["tier"] == 2 else 0.0, 1.0 if r["tier"] == 3 else 0.0] for r in rows])
    y = np.log([r["interest"] for r in rows])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    dof = max(len(y) - X.shape[1], 1)
    cov = np.linalg.pinv(X.T @ X) * (resid @ resid / dof)
    se = np.sqrt(np.diag(cov))
    b2, b3 = beta[-2], beta[-1]
    n_t = {t: sum(1 for r in rows if r["tier"] == t) for t in (1, 2, 3)}
    rk = lambda v: np.argsort(np.argsort(v)).astype(float)
    rho = float(np.corrcoef(rk([r["interest"] for r in rows]), rk([-r["tier"] for r in rows]))[0, 1])
    ci = lambda b, s: (math.exp(b - 1.645 * s), math.exp(b + 1.645 * s))
    md = ["# Independent check: do Wikipedia readers see the same rivalry ladder?", "",
          "Auto-generated by `scripts/wikipedia_rivalry.py`. No Google data. For curated pro rivalries with a Wikipedia article: article page views (2021 to 2025) divided by the geometric mean of the two "
          "teams' own page views (removes team popularity), regressed on the analyst tier with a league effect. exp(coefficient) is the readers' ladder: tier-2 and tier-3 interest relative to tier 1.", "",
          f"Rivalries with an article: **{len(rows)}** (tier 1: {n_t[1]}, tier 2: {n_t[2]}, tier 3: {n_t[3]}). Rank correlation of reading interest with tier: **{rho:.2f}**.", "",
          "| | Wikipedia readers (90% interval) | Analyst prior | Google antipathy fit (NFL) |", "|---|---|---|---|",
          f"| Tier 2 relative to tier 1 | {math.exp(b2):.2f} ({ci(b2, se[-2])[0]:.2f} to {ci(b2, se[-2])[1]:.2f}) | 0.38 | 0.41 |",
          f"| Tier 3 relative to tier 1 | {math.exp(b3):.2f} ({ci(b3, se[-1])[0]:.2f} to {ci(b3, se[-1])[1]:.2f}) | 0.11 | 0.11 |", "",
          "Caveats: national reading, no state detail; reading is not hostility; only rivalries that have an article are included (a selection toward famous ones); the tier of a pair is the stronger of its two directed tiers. "
          "Pairs and article titles: `data/model/wikipedia_rivalry.csv`."]
    (ROOT / "docs/WIKIPEDIA_RIVALRY.md").write_text(chr(10).join(md) + chr(10), encoding="utf-8", newline=chr(10))
    print(chr(10).join(md[4:12]))


if __name__ == "__main__":
    main()
