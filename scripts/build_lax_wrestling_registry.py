"""Registry step (M2): NCAA Division I lacrosse (men's and women's) and men's wrestling programs.

docs/PROTOCOL.md section 6 benchmarks: Maryland men's lacrosse (4,011 avg), Iowa wrestling (13,640 avg). Families:
  lax  -> ids lax_m_<school>, lax_w_<school>   (one family: a state's lacrosse attention spans both sexes)
  wrs  -> ids wrs_<school>                      (men's wrestling)
Sources: Wikipedia 'List of NCAA Division I lacrosse programs' and 'List of NCAA Division I men's wrestling
programs' via the MediaWiki API (cached, git-ignored). Schools already in the registry reuse their
organization; schools outside the D-I basketball enumeration (e.g. Johns Hopkins) get a new organization row
from the list's city and state. Edges are not derived for these families (no curated rivalry list yet).

    python scripts/build_lax_wrestling_registry.py
"""
import csv
import json
import pathlib
import re
import sys

import requests

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import build_cfb_full_registry as CF  # noqa: E402  (STATES, strip_templates, txt, slug)
import build_volleyball_entities_registry as VB  # noqa: E402  (base, strip, MANUAL, UA)

ROOT = pathlib.Path(__file__).resolve().parent.parent
ENTITIES = ROOT / "data" / "registries" / "entities.csv"
CACHE = ROOT / "data" / "raw" / "_cache"
RETRIEVED_AT = "2026-10-08"
LAX = "List of NCAA Division I lacrosse programs"
WRS = "List of NCAA Division I men's wrestling programs"
SRC = "Wikipedia '{}' fetched via MediaWiki API " + RETRIEVED_AT


# school as printed on the Wikipedia lists (normalized with VB.base) -> existing organization
ALIAS = {
    "austin peay state university": "college_austin_peay", "california polytechnic state university": "college_cal_poly",
    "california state university bakersfield": "college_csu_bakersfield", "detroit": "college_detroit_mercy",
    "gardner webb university": "college_gardner_webb", "gardnerwebb university": "college_gardner_webb",
    "indiana university bloomington": "college_indiana", "little rock": "college_arkansas_little_rock",
    "long island university": "college_liu", "loyola university": "college_loyola_maryland",
    "north carolina state university": "college_nc_state", "oklahoma state university stillwater": "college_oklahoma_state",
    "oklahoma state university": "college_oklahoma_state", "oklahoma state universitystillwater": "college_oklahoma_state",
    "rutgers universitynew brunswick": "college_rutgers", "pennsylvania state university": "college_penn_state",
    "pitt": "college_pittsburgh", "rutgers university new brunswick": "college_rutgers",
    "rutgers university": "college_rutgers", "saint bona": "college_st_bonaventure",
    "saint bonaventure": "college_st_bonaventure", "saint john s": "college_st_john_s", "siu e": "college_siu_edwardsville",
    "virginia military institute": "college_vmi",
    "virginia polytechnic institute and state university": "college_virginia_tech",
}

def wikitext(page, key):
    p = CACHE / f"{key}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))["w"]
    r = requests.get("https://en.wikipedia.org/w/api.php", timeout=30, headers=VB.UA, params={
        "action": "parse", "page": page, "prop": "wikitext", "format": "json", "redirects": 1})
    w = r.json()["parse"]["wikitext"]["*"]
    CACHE.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"w": w}), encoding="utf-8")
    return w


def strip_non_sort(s):
    """Remove footnote-style templates but keep {{sort|key|display}} (it carries the school name)."""
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"\{\{(?!sort\|)[^{}]*\}\}", "", s)
    return re.sub(r"<ref[^>]*?/>|<ref.*?</ref>|<!--.*?-->", "", s, flags=re.S)


def table_rows(seg):
    body = seg[seg.index("{|"):]
    body = body[: body.index("\n|}")]
    out = []
    for blk in body.split("\n|-")[1:]:
        blk = strip_non_sort(blk).strip()
        if not blk or blk.startswith("!"):
            continue
        cells = [ln[1:].strip() for ln in blk.split("\n") if ln.startswith("|")]
        out.append(cells)
    return out


def school_cell(c):
    m = re.search(r"\{\{sort\|([^|]*)\|", c)
    return m.group(1).strip() if m else CF.txt(c)


def state_of(c):
    s = CF.txt(c)
    return CF.STATES.get(s) or (s if s in CF.STATES.values() else None)


def lax_rows():
    w = wikitext(LAX, "lax")
    men = w[w.index("\n==Men=="): w.index("\n==Women==")]
    women = w[w.index("\n==Women=="): w.index("\n==Footnotes")]
    # restrict men's to current programs: stop before 'Future men's teams'
    if "===Future men's teams===" in men:
        men = men[: men.index("===Future men's teams===")]
    res = []
    for sex, seg in (("m", men), ("w", women)):
        for c in table_rows(seg):
            if len(c) < 5:
                continue
            school, team, city, state, conf = school_cell(c[0]), CF.txt(c[1]), CF.txt(c[2]), state_of(c[3]), CF.txt(c[4])
            if not state and len(c) >= 5:       # women's table order may differ: City/State swapped
                state = state_of(c[2])
                city = CF.txt(c[3])
            if school and state:
                res.append({"sex": sex, "school": school, "team": team, "city": city, "state": state, "conf": conf})
            else:
                print("SKIP lax row:", sex, c[:5], file=sys.stderr)
    return res


def wrs_rows():
    w = wikitext(WRS, "wrs")
    seg = w[w.index("==Current Division I schools=="): w.index("==In transition==")]
    res = []
    for c in table_rows(seg):
        if len(c) < 6:
            continue
        school, city, state, nick, conf = school_cell(c[0]), CF.txt(c[1]), state_of(c[2]), CF.txt(c[3]), CF.txt(c[5])
        if school and state:
            res.append({"sex": "m", "school": school, "team": nick, "city": city, "state": state, "conf": conf})
        else:
            print("SKIP wrs row:", c[:4], file=sys.stderr)
    return res


def main():
    with open(ENTITIES, newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        fields = rd.fieldnames
        rows = [r for r in rd if not r["entity_id"].startswith(("lax_", "wrs_"))]
    orgs = {}
    for r in rows:
        if r["entity_id"].startswith(("cbb_m_", "cbb_w_")):
            orgs[r["organization_id"]] = r
    names = {o: re.sub(r" (Men's|Women's) Basketball$", "", r["entity_name"]) for o, r in orgs.items()}
    by_base, by_strip = {}, {}
    for o, n in names.items():
        by_base.setdefault(VB.base(n), []).append(o)
        by_strip.setdefault(VB.strip(n), []).append(o)

    def find_org(school):
        if VB.base(school) in ALIAS:
            return ALIAS[VB.base(school)]
        if school in VB.MANUAL:
            return VB.MANUAL[school]
        for idx, fn in ((by_base, VB.base), (by_strip, VB.strip)):
            c = idx.get(fn(school), [])
            if len(c) == 1:
                return c[0]
        return None

    new, newly_created = [], set()
    todo = [("lax_" + r["sex"], "Lacrosse", r, LAX) for r in lax_rows()] + [("wrs", "Wrestling", r, WRS) for r in wrs_rows()]
    for fam, sport, r, page in todo:
        org = find_org(r["school"])
        if org:
            o = orgs[org]
            city, st, oname = o["home_city"], o["home_state"], names[org]
        else:
            org = "college_" + CF.slug(r["school"])
            city, st, oname = r["city"], r["state"], r["school"]
            newly_created.add(oname)
        sex = "men" if fam in ("lax_m", "wrs") else "women"
        label = {"lax_m": "Men's Lacrosse", "lax_w": "Women's Lacrosse", "wrs": "Wrestling"}[fam]
        eid = f"{fam}_{org.replace('college_', '')}"
        if any(n["entity_id"] == eid for n in new):
            continue
        new.append({
            "entity_id": eid, "organization_id": org, "entity_name": f"{oname} {label}", "sport": sport, "sex_category": sex,
            "level": "D-I", "professional_college": "college", "league": "NCAA Division I", "conference": r["conf"],
            "division": "", "home_city": city, "home_state": st, "stadium_or_campus": "", "active_from": "",
            "active_to": "", "current_status": "active", "source": SRC.format(page),
            "notes": "" if org in orgs else "school not in D-I basketball enumeration; city/state from this list"})
    with open(ENTITIES, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows + new)
    by = {}
    for n in new:
        by[n["entity_id"].split("_")[0] + "_" + n["entity_id"].split("_")[1] if n["entity_id"].startswith("lax") else "wrs"] = \
            by.get(n["entity_id"].split("_")[0] + "_" + n["entity_id"].split("_")[1] if n["entity_id"].startswith("lax") else "wrs", 0) + 1
    print("appended", by, "| new organizations:", sorted(newly_created)[:20])


if __name__ == "__main__":
    main()
