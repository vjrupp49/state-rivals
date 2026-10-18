"""Registry step (M2): close the deferred gaps in college baseball and softball (Pac-12 and UAC, among others).

The earlier registries were built conference by conference and explicitly deferred the Pac-12 and United
Athletic Conference programs. Wikipedia's complete 'List of NCAA Division I baseball/softball programs'
(MediaWiki API, cached, git-ignored) lets us check every program against the registry and add what is
missing. Existing rows are never changed; rows for programs the list does not show are only reported.

    python scripts/build_bsb_sfb_completion.py
"""
import csv
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import build_cfb_full_registry as CF  # noqa: E402
import build_lax_wrestling_registry as LW  # noqa: E402
import build_volleyball_entities_registry as VB  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
ENTITIES = ROOT / "data" / "registries" / "entities.csv"
RETRIEVED_AT = "2026-10-08"
SPECS = {
    "bsb": dict(page="List of NCAA Division I baseball programs", section="== Division I programs ==", end="=== Future programs ===",
                conf_col=4, label="Baseball", sport="Baseball", sex="men"),
    "sfb": dict(page="List of NCAA Division I softball programs", section=None, end="==Future programs==",
                conf_col=5, label="Softball", sport="Softball", sex="women"),
}


def rows(fam):
    sp = SPECS[fam]
    w = LW.wikitext(sp["page"], "list_" + fam)
    seg = w[w.index(sp["section"]):] if sp["section"] else w
    seg = seg[: seg.index(sp["end"])]
    out = []
    for c in LW.table_rows(seg):
        if len(c) <= sp["conf_col"]:
            continue
        school, st, conf = LW.school_cell(c[0]), LW.state_of(c[2]), CF.txt(c[sp["conf_col"]])
        if school and st:
            out.append({"school": school, "state": st, "conf": conf})
    return out


def main():
    with open(ENTITIES, newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        fields = rd.fieldnames
        data = list(rd)
    orgs = {r["organization_id"]: r for r in data if r["entity_id"].startswith(("cbb_m_", "cbb_w_"))}
    names = {o: re.sub(r" (Men's|Women's) Basketball$", "", r["entity_name"]) for o, r in orgs.items()}
    by_base, by_strip = {}, {}
    for o, n in names.items():
        by_base.setdefault(VB.base(n), []).append(o)
        by_strip.setdefault(VB.strip(n), []).append(o)

    def find_org(school):
        if VB.base(school) in LW.ALIAS:
            return LW.ALIAS[VB.base(school)]
        if school in VB.MANUAL:
            return VB.MANUAL[school]
        for idx, fn in ((by_base, VB.base), (by_strip, VB.strip)):
            c = idx.get(fn(school), [])
            if len(c) == 1:
                return c[0]
        return None

    new, unmatched, report = [], [], {}
    for fam, sp in SPECS.items():
        have_orgs = {r["organization_id"] for r in data if r["entity_id"].startswith(fam + "_")}
        listed = rows(fam)
        report[fam] = {"listed": len(listed), "registered": len(have_orgs), "added": 0, "not_in_list": 0}
        seen = set()
        for r in listed:
            org = find_org(r["school"])
            if not org:
                unmatched.append(f"{fam}: {r['school']} ({r['state']})")
                continue
            seen.add(org)
            if org in have_orgs:
                continue
            o = orgs[org]
            new.append({
                "entity_id": f"{fam}_{org.replace('college_', '')}", "organization_id": org,
                "entity_name": f"{names[org]} {sp['label']}", "sport": sp["sport"], "sex_category": sp["sex"],
                "level": "D-I", "professional_college": "college", "league": "NCAA Division I", "conference": r["conf"],
                "division": "", "home_city": o["home_city"], "home_state": o["home_state"], "stadium_or_campus": "",
                "active_from": "", "active_to": "", "current_status": "active",
                "source": f"Wikipedia '{sp['page']}' fetched via MediaWiki API {RETRIEVED_AT}",
                "notes": "added by completion pass (previously deferred conference or missed program)"})
            report[fam]["added"] += 1
        report[fam]["not_in_list"] = len(have_orgs - seen)
    with open(ENTITIES, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(data + new)
    print(json.dumps(report))
    print("unmatched (add aliases or review):", unmatched)


if __name__ == "__main__":
    main()
