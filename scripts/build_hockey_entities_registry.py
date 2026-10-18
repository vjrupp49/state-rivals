"""Phase 4B step 1 (registry side, continued): append men's and women's
Division I college ice hockey programs to data/registries/entities.csv.

Like basketball, this is a complete enumeration (docs/PROTOCOL.md section 5: "all
Division I varsity programs are automatic candidates"), not evidence-
bootstrapped -- and it matters here specifically because docs/PROTOCOL.md section 7
names Minnesota-North Dakota and Minnesota-Wisconsin men's/women's hockey as
explicit contemporary rivalries, and section 6 cites North Dakota (11,614
avg attendance), Wisconsin (10,461) and Minnesota (9,233) men's hockey as
evidence-forced regional inclusions. Unlike basketball, men's and women's
D-I hockey are NOT mirror images of the same ~365 schools -- each sex has
its own much smaller, genuinely different set of sponsoring conferences and
member schools, verified separately below.

Conference membership verified 2026-09-15, one conference at a time:
- Men's (63 programs): Big Ten, Hockey East, ECAC Hockey, NCHC, CCHA,
  Atlantic Hockey America, plus independents.
- Women's (43 programs): WCHA, ECAC Hockey, Hockey East, NEWHA, and the
  5 former College Hockey America (CHA) schools that moved into Atlantic
  Hockey America when CHA and Atlantic Hockey merged in 2024. Confirmed CHA
  itself no longer exists as a separate conference.

Run from the project root (after build_cbb_entities_registry.py):
    python scripts/build_hockey_entities_registry.py
"""
import csv
import pathlib
import re

ROOT = pathlib.Path(__file__).parent.parent
ENTITIES_PATH = ROOT / "data" / "registries" / "entities.csv"
RETRIEVED_AT = "2026-09-15"

FIELDNAMES = [
    "entity_id", "organization_id", "entity_name", "sport", "sex_category",
    "level", "professional_college", "league", "conference", "division",
    "home_city", "home_state", "stadium_or_campus", "active_from",
    "active_to", "current_status", "source", "notes",
]

SOURCE = (
    "Conference membership verified 2026-09-15 against Wikipedia pages for "
    "each hockey conference (Big Ten, Hockey East, ECAC Hockey, NCHC, CCHA, "
    "Atlantic Hockey America / former Atlantic Hockey + College Hockey "
    "America, WCHA, NEWHA), fetched individually and cross-checked for "
    "the 2024 CHA/Atlantic Hockey merger."
)

# school -> (city, state); shared across men's and women's lists
CITY_STATE = {
    "Michigan": ("Ann Arbor", "MI"), "Michigan State": ("East Lansing", "MI"),
    "Minnesota": ("Minneapolis", "MN"), "Ohio State": ("Columbus", "OH"),
    "Penn State": ("University Park", "PA"), "Notre Dame": ("Notre Dame", "IN"),
    "Wisconsin": ("Madison", "WI"), "Boston College": ("Chestnut Hill", "MA"),
    "Boston University": ("Boston", "MA"), "UConn": ("Storrs", "CT"),
    "Maine": ("Orono", "ME"), "UMass": ("Amherst", "MA"),
    "UMass Lowell": ("Lowell", "MA"), "Merrimack": ("North Andover", "MA"),
    "New Hampshire": ("Durham", "NH"), "Vermont": ("Burlington", "VT"),
    "Providence": ("Providence", "RI"), "Brown": ("Providence", "RI"),
    "Clarkson": ("Potsdam", "NY"), "Colgate": ("Hamilton", "NY"),
    "Cornell": ("Ithaca", "NY"), "Dartmouth": ("Hanover", "NH"),
    "Harvard": ("Cambridge", "MA"), "Princeton": ("Princeton", "NJ"),
    "RPI": ("Troy", "NY"), "St. Lawrence": ("Canton", "NY"),
    "Union": ("Schenectady", "NY"), "Yale": ("New Haven", "CT"),
    "Quinnipiac": ("Hamden", "CT"), "Arizona State": ("Tempe", "AZ"),
    "Colorado College": ("Colorado Springs", "CO"), "Denver": ("Denver", "CO"),
    "Miami (OH)": ("Oxford", "OH"), "Minnesota Duluth": ("Duluth", "MN"),
    "North Dakota": ("Grand Forks", "ND"), "St. Cloud State": ("St. Cloud", "MN"),
    "St. Thomas": ("St. Paul", "MN"), "Western Michigan": ("Kalamazoo", "MI"),
    "Nebraska Omaha": ("Omaha", "NE"), "Augustana (SD)": ("Sioux Falls", "SD"),
    "Bemidji State": ("Bemidji", "MN"), "Bowling Green": ("Bowling Green", "OH"),
    "Ferris State": ("Big Rapids", "MI"), "Lake Superior State": ("Sault Ste. Marie", "MI"),
    "Michigan Tech": ("Houghton", "MI"), "Minnesota State": ("Mankato", "MN"),
    "Northern Michigan": ("Marquette", "MI"), "Air Force": ("Colorado Springs", "CO"),
    "Army": ("West Point", "NY"), "Bentley": ("Waltham", "MA"),
    "Canisius": ("Buffalo", "NY"), "Holy Cross": ("Worcester", "MA"),
    "Niagara": ("Lewiston", "NY"), "Robert Morris": ("Moon Township", "PA"),
    "RIT": ("Rochester", "NY"), "Sacred Heart": ("Fairfield", "CT"),
    "Alaska Fairbanks": ("Fairbanks", "AK"), "Alaska Anchorage": ("Anchorage", "AK"),
    "Lindenwood": ("St. Charles", "MO"), "LIU": ("Brooklyn", "NY"),
    "Stonehill": ("Easton", "MA"), "Tennessee State": ("Nashville", "TN"),
    "Maryville": ("St. Louis", "MO"), "Assumption": ("Worcester", "MA"),
    "Franklin Pierce": ("Rindge", "NH"), "Post": ("Waterbury", "CT"),
    "Saint Anselm": ("Manchester", "NH"), "Saint Michael's": ("Colchester", "VT"),
    "Mercyhurst": ("Erie", "PA"), "Syracuse": ("Syracuse", "NY"),
}

MENS_HOCKEY = {
    "Big Ten": ["Michigan", "Michigan State", "Minnesota", "Ohio State", "Penn State", "Notre Dame", "Wisconsin"],
    "Hockey East": ["Boston College", "Boston University", "UConn", "Maine", "UMass", "UMass Lowell", "Merrimack", "New Hampshire", "Vermont", "Providence"],
    "ECAC Hockey": ["Brown", "Clarkson", "Colgate", "Cornell", "Dartmouth", "Harvard", "Princeton", "RPI", "St. Lawrence", "Union", "Yale", "Quinnipiac"],
    "NCHC": ["Arizona State", "Colorado College", "Denver", "Miami (OH)", "Minnesota Duluth", "North Dakota", "St. Cloud State", "St. Thomas", "Western Michigan", "Nebraska Omaha"],
    "CCHA": ["Augustana (SD)", "Bemidji State", "Bowling Green", "Ferris State", "Lake Superior State", "Michigan Tech", "Minnesota State", "Northern Michigan"],
    "Atlantic Hockey America": ["Air Force", "Army", "Bentley", "Canisius", "Holy Cross", "Niagara", "Robert Morris", "RIT", "Sacred Heart"],
    "Independent": ["Alaska Fairbanks", "Alaska Anchorage", "Lindenwood", "LIU", "Stonehill", "Tennessee State", "Maryville"],
}

WOMENS_HOCKEY = {
    "WCHA": ["Bemidji State", "Minnesota", "Minnesota Duluth", "Minnesota State", "Ohio State", "St. Cloud State", "St. Thomas", "Wisconsin"],
    "ECAC Hockey": ["Brown", "Clarkson", "Colgate", "Cornell", "Dartmouth", "Harvard", "Princeton", "Quinnipiac", "RPI", "St. Lawrence", "Union", "Yale"],
    "Hockey East": ["Boston College", "Boston University", "UConn", "Holy Cross", "Maine", "Merrimack", "New Hampshire", "Northeastern", "Providence", "Vermont"],
    "NEWHA": ["Assumption", "Franklin Pierce", "LIU", "Post", "Sacred Heart", "Saint Anselm", "Saint Michael's", "Stonehill"],
    "Atlantic Hockey America": ["Mercyhurst", "Penn State", "Robert Morris", "Syracuse", "RIT"],
}

CITY_STATE["Northeastern"] = ("Boston", "MA")


def slugify(school_name):
    return re.sub(r"[^A-Za-z0-9]+", "_", school_name).strip("_").lower()


def main():
    with open(ENTITIES_PATH, newline="", encoding="utf-8") as f:
        existing = list(csv.DictReader(f))
    existing_ids = {r["entity_id"] for r in existing}

    new_rows = []
    seen_ids = set()
    counts = {"men": 0, "women": 0}
    for sex, conf_map, label in [("men", MENS_HOCKEY, "Men's Ice Hockey"),
                                  ("women", WOMENS_HOCKEY, "Women's Ice Hockey")]:
        for conference, schools in conf_map.items():
            for school in schools:
                city, state = CITY_STATE[school]
                slug = slugify(school)
                entity_id = f"hky_{sex[0]}_{slug}"
                if entity_id in existing_ids or entity_id in seen_ids:
                    raise ValueError(f"duplicate entity_id: {entity_id} ({school})")
                seen_ids.add(entity_id)
                counts[sex] += 1
                new_rows.append({
                    "entity_id": entity_id,
                    "organization_id": f"college_{slug}",
                    "entity_name": f"{school} {label}",
                    "sport": "Ice hockey",
                    "sex_category": sex,
                    "level": "D-I",
                    "professional_college": "college",
                    "league": "NCAA Division I",
                    "conference": conference,
                    "division": "",
                    "home_city": city,
                    "home_state": state,
                    "stadium_or_campus": "",
                    "active_from": "",
                    "active_to": "",
                    "current_status": "active",
                    "source": SOURCE,
                    "notes": "",
                })

    all_rows = existing + new_rows
    with open(ENTITIES_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Appended {len(new_rows)} hockey entities: {counts['men']} men's, {counts['women']} women's")
    print(f"Total registry size: {len(all_rows)}")


if __name__ == "__main__":
    main()
