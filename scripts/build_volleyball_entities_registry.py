"""Registry step (M2): append NCAA Division I women's volleyball programs to data/registries/entities.csv.

docs/PROTOCOL.md section 6: Nebraska volleyball (8,713 avg, 92,003 stadium match) forces regional retention, so
volleyball is a core regional sport. Source: Wikipedia 'List of NCAA Division I women's volleyball programs'
(2026 season affiliations), fetched through the MediaWiki API and cached (git-ignored) in data/raw/_cache.
Schools are matched to the organization already in the registry (from the basketball enumeration) so that
home city/state and conference come from one place; every row notes the Wikipedia source.

Not covered (documented gaps, not guessed): men's volleyball (a separate, much smaller, mostly NCAA
Division I/II mix) and professional volleyball (PVF/MLV) -- see docs/LIMITATIONS.md.

Run from the project root:
    python scripts/build_volleyball_entities_registry.py
"""
import csv
import json
import pathlib
import re
import sys
import unicodedata

import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
ENTITIES = ROOT / "data" / "registries" / "entities.csv"
CACHE = ROOT / "data" / "raw" / "_cache" / "vbw_wikipedia.json"
RETRIEVED_AT = "2026-10-08"
PAGE = "List of NCAA Division I women's volleyball programs"
UA = {"User-Agent": "StateRivalsResearch/0.1 (academic research; contact via GitHub repo)"}
SOURCE = ("Wikipedia 'List of NCAA Division I women's volleyball programs' (2026 season), "
          f"fetched via MediaWiki API {RETRIEVED_AT}; school matched to registry organization")

# Wikipedia name -> registry organization_id, for schools whose names do not normalize to the registry's
MANUAL = {
    "Cal": "college_california", "Miami Florida": "college_miami_fl", "Miami Ohio": "college_miami_oh",
    "Queens University of Charlotte": "college_queens_charlotte", "Bakersfield": "college_csu_bakersfield",
    "IU Indy": "college_iu_indianapolis", "UNC Greensboro Spartans": "college_unc_greensboro",
    "Cal State Fullerton": "college_csu_fullerton", "Cal State Northridge": "college_csu_northridge",
    "North Carolina A&T": "college_nc_a_t", "Sam Houston State University": "college_sam_houston",
    "North Carolina Central University": "college_nc_central", "Central Connecticut State University": "college_central_connecticut",
    "LSU New Orleans": "college_new_orleans", "McNeese State University": "college_mcneese",
    "Nicholls State University": "college_nicholls", "Kansas City": "college_umkc",
}


def fetch():
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    r = requests.get("https://en.wikipedia.org/w/api.php", timeout=30, headers=UA, params={
        "action": "parse", "page": PAGE, "prop": "wikitext", "format": "json", "redirects": 1})
    w = r.json()["parse"]["wikitext"]["*"]
    main = w[w.index("==Programs=="):w.index("== Future programs")]
    out = []
    for blk in main.split("\n|-")[1:]:
        cells = [ln[2:].strip() for ln in blk.strip().split("\n") if ln.startswith("| ")]
        if len(cells) < 4:
            continue
        s, n, a, c = cells[:4]
        out.append({"school": _clean(s), "school_link": re.search(r"\[\[([^\]|]*)", s).group(1) if "[[" in s else s,
                    "nick": _clean(n), "arena": _clean(a), "conf": _clean(c)})
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(out, indent=0), encoding="utf-8")
    return out


def _clean(c):
    m = re.search(r"\{\{sort\|([^|]*)\|", c)
    if m:
        return m.group(1).strip()
    m = re.search(r"\[\[([^\]|]*)(\|([^\]]*))?\]\]", c)
    return (m.group(3) or m.group(1)).strip() if m else c


def base(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"[^a-z0-9& ]", " ", s)
    return " ".join(s.split())


def strip(s):
    s = re.sub(r"\bstate university\b", "state", base(s))
    s = re.sub(r"\b(the|university|college|of|at)\b", " ", s)
    s = re.sub(r"\band\b", "&", s)
    return " ".join(s.split())


def main():
    data = fetch()
    with open(ENTITIES, newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        fields = rd.fieldnames
        rows = [r for r in rd if not r["entity_id"].startswith("vbw_")]
    orgs = {r["organization_id"]: r for r in rows if r["entity_id"].startswith("cbb_w_")}
    names = {o: r["entity_name"].replace(" Women's Basketball", "") for o, r in orgs.items()}
    by_base, by_strip = {}, {}
    for o, n in names.items():
        by_base.setdefault(base(n), []).append(o)
        by_strip.setdefault(strip(n), []).append(o)
    new, unmatched, seen = [], [], set()
    for d in data:
        hit = MANUAL.get(d["school"])
        for key, idx, fn in ((d["school"], by_base, base), (d["school_link"], by_base, base),
                             (d["school"], by_strip, strip), (d["school_link"], by_strip, strip)):
            if hit:
                break
            c = idx.get(fn(key), [])
            if len(c) == 1:
                hit = c[0]
        if not hit or hit in seen:
            unmatched.append(d["school"] + " | " + d["school_link"])
            continue
        seen.add(hit)
        o = orgs[hit]
        new.append({
            "entity_id": "vbw_" + hit.replace("college_", ""), "organization_id": hit,
            "entity_name": f"{names[hit]} Women's Volleyball", "sport": "Volleyball", "sex_category": "women",
            "level": "D-I", "professional_college": "college", "league": "NCAA Division I",
            "conference": d["conf"], "division": "", "home_city": o["home_city"], "home_state": o["home_state"],
            "stadium_or_campus": d["arena"], "active_from": "", "active_to": "", "current_status": "active",
            "source": SOURCE, "notes": ""})
    if unmatched:
        print("UNMATCHED (add to MANUAL):")
        print("\n".join(unmatched))
        sys.exit(1)
    with open(ENTITIES, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows + new)
    print(f"appended {len(new)} women's volleyball programs; registry now {len(rows) + len(new)} rows")


if __name__ == "__main__":
    main()
