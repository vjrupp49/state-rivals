"""Registry step (M2): complete the college football enumeration to every FBS and FCS program.

The earlier registry held only the 168 programs that won a county plurality in the Vivid Seats map
(evidence-bootstrapped). docs/PROTOCOL.md section 5 requires all Division I programs as candidates, so this
adds every FBS and FCS program missing from the registry. Sources: Wikipedia 'List of NCAA Division I
FBS football programs' and '... FCS football programs' via the MediaWiki API (cached, git-ignored).

Existing rows are left untouched; level/conference disagreements with the lists are printed for review
(realignment changes fast). New rows use the same id scheme: cfb_<school>_<nickname>.

    python scripts/build_cfb_full_registry.py
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
CACHE = ROOT / "data" / "raw" / "_cache"
UA = {"User-Agent": "StateRivalsResearch/0.1 (academic research; contact via GitHub repo)"}
# list entries that are the SAME program as an existing registry row under a different name
DUPLICATES = {'cfb_sam_houston_bearkats', 'cfb_lamar_cardinals', 'cfb_army_black_knights', 'cfb_texas_state_bobcats', 'cfb_delaware_fightin_blue_hens', 'cfb_samford_bulldogs', 'cfb_ulm_warhawks', 'cfb_miami_fl_hurricanes', 'cfb_air_force_falcons', 'cfb_nc_state_wolfpack', 'cfb_william_mary_tribe'}
RETRIEVED_AT = "2026-10-08"
PAGES = {"FBS": "List of NCAA Division I FBS football programs", "FCS": "List of NCAA Division I FCS football programs"}
STATES = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA", "Colorado": "CO",
    "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA",
    "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY", "North Carolina": "NC",
    "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA",
    "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX",
    "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY", "Washington, D.C.": "DC", "District of Columbia": "DC",
}


def fetch(level):
    p = CACHE / f"cfb_{level}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))["wikitext"]
    j = requests.get("https://en.wikipedia.org/w/api.php", timeout=30, headers=UA, params={
        "action": "parse", "page": PAGES[level], "prop": "wikitext", "format": "json", "redirects": 1}).json()
    w = j["parse"]["wikitext"]["*"]
    CACHE.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"wikitext": w}), encoding="utf-8")
    return w


def strip_templates(s):
    prev = None
    while prev != s:
        prev, s = s, re.sub(r"\{\{[^{}]*\}\}", "", s)
    s = re.sub(r"<ref[^>]*?/>|<ref.*?</ref>|<!--.*?-->", "", s, flags=re.S)
    return s


def txt(c):
    c = strip_templates(c)
    m = re.search(r"\[\[([^\]|]*)(?:\|([^\]]*))?\]\]", c)
    out = (m.group(2) or m.group(1)) if m else c
    return re.sub(r"<[^>]+>|'''|''", "", out).strip()


def rows_of(w, level):
    body = w[w.index("{|"):]
    body = body[: body.index("\n|}")]
    out = []
    for blk in body.split("\n|-")[1:]:
        blk = strip_templates(blk).strip()
        if blk.startswith("!") or not blk:
            continue
        if "||" in blk and level == "FCS":
            cells = [c.strip() for c in blk.lstrip("| \n").replace("\n", " ").split("||")]
        else:
            cells = [ln[1:].strip() for ln in blk.split("\n") if ln.startswith("|")]
        out.append(cells)
    return out


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def parse(level):
    res = []
    for c in rows_of(fetch(level), level):
        if level == "FBS":
            if len(c) < 6:
                continue
            school, nick, city, state, _, conf = (txt(x) for x in c[:6])
        else:
            if len(c) < 8:
                continue
            school, nick, _, city, state, _, _, conf = (txt(x) for x in c[:8])
        st = STATES.get(state) or (state if state in STATES.values() else None)
        if not school or not nick or not st:
            print("SKIP row:", level, c[:5], file=sys.stderr)
            continue
        res.append({"school": school, "nick": nick, "city": city, "state": st, "conf": conf, "level": level})
    return res


def main():
    with open(ENTITIES, newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        fields = rd.fieldnames
        rows = list(rd)
    have = {r["entity_id"]: r for r in rows if r["entity_id"].startswith("cfb_")}
    have_slug_school = {}
    for eid, r in have.items():
        have_slug_school[slug(r["entity_name"].replace(" Football", ""))] = eid
    new, diffs = [], []
    for level in ("FBS", "FCS"):
        for p in parse(level):
            eid = f"cfb_{slug(p['school'])}_{slug(p['nick'])}"
            full = slug(f"{p['school']} {p['nick']}")
            hit = eid if eid in have else have_slug_school.get(full)
            if eid in DUPLICATES:
                continue
            if hit:
                r = have[hit]
                if r["level"] != level or (p["conf"] and r["conference"] != p["conf"]):
                    diffs.append(f"{hit}: registry {r['level']}/{r['conference']} vs list {level}/{p['conf']}")
                continue
            if eid in {n["entity_id"] for n in new}:
                continue
            new.append({
                "entity_id": eid, "organization_id": eid, "entity_name": f"{p['school']} {p['nick']} Football",
                "sport": "American football", "sex_category": "men", "level": level,
                "professional_college": "college", "league": f"NCAA Division I {level}", "conference": p["conf"],
                "division": "", "home_city": p["city"], "home_state": p["state"], "stadium_or_campus": "",
                "active_from": "", "active_to": "", "current_status": "active",
                "source": f"Wikipedia list of NCAA Division I {level} football programs, fetched via MediaWiki API {RETRIEVED_AT}",
                "notes": "added by full FBS/FCS enumeration (no county-plurality evidence needed for candidacy)"})
    with open(ENTITIES, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows + new)
    print(f"existing cfb: {len(have)}; added {len(new)}; registry now {len(rows) + len(new)} rows")
    print(f"{len(diffs)} level/conference disagreements for review (first 15):")
    print("\n".join(diffs[:15]))


if __name__ == "__main__":
    main()
