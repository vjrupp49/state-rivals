"""Phase 4B step 1 (registry side, continued): append Division I college
softball programs to data/registries/entities.csv.

docs/PROTOCOL.md section 6 names Oklahoma softball (3,717/game; 107,813 total,
2025) as an evidence-forced regional inclusion -- this is a complete
enumeration of D-I softball-sponsoring programs, not just Oklahoma.

Like baseball, softball sponsorship is school-by-school, not a simple
function of conference membership, and it does NOT track baseball
sponsorship at the same schools -- confirmed multiple genuine divergences,
not measurement noise:
- Wisconsin has softball but not baseball; USC has baseball but not
  softball (opposite of Wisconsin, same Big Ten).
- Georgetown and Syracuse have softball despite not sponsoring baseball.
- MEAC sponsors softball for all 8 members despite sponsoring ZERO
  baseball -- the conferences that skip a sport differ by sport, not just
  by conference.
- Big Sky sponsors softball (7 of 11 members) despite sponsoring no
  baseball at all (dropped baseball in 1974, but never dropped softball).

Verification notes / known gaps (2026-09-15):
- Two conferences are DEFERRED, not guessed, matching the same two
  conferences deferred for baseball: Pac-12 and the United Athletic
  Conference (formerly WAC). Wikipedia's sponsored-sports tables for both
  repeatedly failed to resolve on fetch across multiple attempts.
- Ivy League is included at all 8 members based on a partial fetch (4 of
  8 visible: Brown, Columbia, Cornell, Dartmouth) that then truncated
  mid-word at "Har[vard]" -- i.e. the underlying table almost certainly
  continues through the alphabet and was cut off by fetch size, not by an
  actual "No" for the remaining schools. This is corroborated by general
  knowledge that Ivy League softball has run as a full 8-team round robin
  for decades. Flagged as moderate- rather than high-confidence in notes.
- Everything else reflects a direct "women's sponsored sports by school"
  table fetch, per conference.

Run from the project root (after build_baseball_entities_registry.py):
    python scripts/build_softball_entities_registry.py
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
    "Wikipedia 'Women's sponsored sports by school' tables, fetched per "
    "conference 2026-09-15. See script docstring for the Ivy League "
    "confidence note and the two deferred conferences (Pac-12, UAC)."
)

CONFERENCES = {
    "ACC": [
        ("Boston College", "Chestnut Hill", "MA"), ("California", "Berkeley", "CA"),
        ("Clemson", "Clemson", "SC"), ("Duke", "Durham", "NC"),
        ("Florida State", "Tallahassee", "FL"), ("Georgia Tech", "Atlanta", "GA"),
        ("Louisville", "Louisville", "KY"), ("North Carolina", "Chapel Hill", "NC"),
        ("NC State", "Raleigh", "NC"), ("Notre Dame", "Notre Dame", "IN"),
        ("Pittsburgh", "Pittsburgh", "PA"), ("Stanford", "Stanford", "CA"),
        ("Syracuse", "Syracuse", "NY"), ("Virginia", "Charlottesville", "VA"),
        ("Virginia Tech", "Blacksburg", "VA"),
    ],
    "Big Ten": [
        ("Illinois", "Champaign", "IL"), ("Indiana", "Bloomington", "IN"),
        ("Iowa", "Iowa City", "IA"), ("Maryland", "College Park", "MD"),
        ("Michigan", "Ann Arbor", "MI"), ("Michigan State", "East Lansing", "MI"),
        ("Minnesota", "Minneapolis", "MN"), ("Nebraska", "Lincoln", "NE"),
        ("Northwestern", "Evanston", "IL"), ("Ohio State", "Columbus", "OH"),
        ("Oregon", "Eugene", "OR"), ("Penn State", "University Park", "PA"),
        ("Purdue", "West Lafayette", "IN"), ("Rutgers", "Piscataway", "NJ"),
        ("UCLA", "Los Angeles", "CA"), ("Washington", "Seattle", "WA"),
        ("Wisconsin", "Madison", "WI"),
    ],
    "Big 12": [
        ("Arizona", "Tucson", "AZ"), ("Arizona State", "Tempe", "AZ"),
        ("Baylor", "Waco", "TX"), ("BYU", "Provo", "UT"),
        ("Houston", "Houston", "TX"), ("Iowa State", "Ames", "IA"),
        ("Kansas", "Lawrence", "KS"), ("TCU", "Fort Worth", "TX"),
        ("Texas Tech", "Lubbock", "TX"), ("UCF", "Orlando", "FL"),
    ],
    "SEC": [
        ("Alabama", "Tuscaloosa", "AL"), ("Arkansas", "Fayetteville", "AR"),
        ("Auburn", "Auburn", "AL"), ("Florida", "Gainesville", "FL"),
        ("Georgia", "Athens", "GA"), ("Kentucky", "Lexington", "KY"),
        ("LSU", "Baton Rouge", "LA"), ("Ole Miss", "Oxford", "MS"),
        ("Mississippi State", "Starkville", "MS"), ("Missouri", "Columbia", "MO"),
        ("Oklahoma", "Norman", "OK"), ("South Carolina", "Columbia", "SC"),
        ("Tennessee", "Knoxville", "TN"), ("Texas", "Austin", "TX"),
        ("Texas A&M", "College Station", "TX"),
    ],
    "Big East": [
        ("Butler", "Indianapolis", "IN"), ("UConn", "Storrs", "CT"),
        ("Creighton", "Omaha", "NE"), ("DePaul", "Chicago", "IL"),
        ("Georgetown", "Washington", "DC"), ("Providence", "Providence", "RI"),
        ("St. John's", "Queens", "NY"), ("Seton Hall", "South Orange", "NJ"),
        ("Villanova", "Villanova", "PA"),
    ],
    "Atlantic 10": [
        ("Dayton", "Dayton", "OH"), ("Duquesne", "Pittsburgh", "PA"),
        ("Fordham", "Bronx", "NY"), ("George Mason", "Fairfax", "VA"),
        ("George Washington", "Washington", "DC"), ("Rhode Island", "Kingston", "RI"),
        ("Saint Joseph's", "Philadelphia", "PA"), ("Saint Louis", "St. Louis", "MO"),
    ],
    "West Coast Conference": [
        ("Loyola Marymount", "Los Angeles", "CA"), ("Saint Mary's", "Moraga", "CA"),
        ("San Diego", "San Diego", "CA"),
    ],
    "Missouri Valley Conference": [
        ("Belmont", "Nashville", "TN"), ("Bradley", "Peoria", "IL"),
        ("Drake", "Des Moines", "IA"), ("Evansville", "Evansville", "IN"),
        ("UIC", "Chicago", "IL"), ("Illinois State", "Normal", "IL"),
        ("Indiana State", "Terre Haute", "IN"), ("Murray State", "Murray", "KY"),
        ("Southern Illinois", "Carbondale", "IL"), ("Valparaiso", "Valparaiso", "IN"),
    ],
    "American": [
        ("Charlotte", "Charlotte", "NC"), ("East Carolina", "Greenville", "NC"),
        ("Florida Atlantic", "Boca Raton", "FL"), ("Memphis", "Memphis", "TN"),
        ("North Texas", "Denton", "TX"), ("South Florida", "Tampa", "FL"),
        ("Tulsa", "Tulsa", "OK"), ("UAB", "Birmingham", "AL"),
        ("UTSA", "San Antonio", "TX"), ("Wichita State", "Wichita", "KS"),
    ],
    "Conference USA": [
        ("Delaware", "Newark", "DE"), ("FIU", "Miami", "FL"),
        ("Jacksonville State", "Jacksonville", "AL"), ("Kennesaw State", "Kennesaw", "GA"),
        ("Liberty", "Lynchburg", "VA"), ("Middle Tennessee", "Murfreesboro", "TN"),
        ("Missouri State", "Springfield", "MO"), ("New Mexico State", "Las Cruces", "NM"),
        ("Sam Houston", "Huntsville", "TX"), ("Western Kentucky", "Bowling Green", "KY"),
    ],
    "Big Sky": [
        ("Idaho State", "Pocatello", "ID"), ("Montana", "Missoula", "MT"),
        ("Northern Colorado", "Greeley", "CO"), ("Portland State", "Portland", "OR"),
        ("Southern Utah", "Cedar City", "UT"), ("Utah Tech", "St. George", "UT"),
        ("Weber State", "Ogden", "UT"),
    ],
    "CAA": [
        ("Campbell", "Buies Creek", "NC"), ("Charleston", "Charleston", "SC"),
        ("Drexel", "Philadelphia", "PA"), ("Elon", "Elon", "NC"),
        ("Hampton", "Hampton", "VA"), ("Hofstra", "Hempstead", "NY"),
        ("Monmouth", "West Long Branch", "NJ"), ("NC A&T", "Greensboro", "NC"),
        ("Stony Brook", "Stony Brook", "NY"), ("Towson", "Towson", "MD"),
        ("UNC Wilmington", "Wilmington", "NC"),
    ],
    "Horizon League": [
        ("Detroit Mercy", "Detroit", "MI"), ("Green Bay", "Green Bay", "WI"),
        ("IU Indianapolis", "Indianapolis", "IN"), ("Northern Illinois", "DeKalb", "IL"),
        ("Northern Kentucky", "Highland Heights", "KY"), ("Oakland", "Rochester", "MI"),
        ("Robert Morris", "Moon Township", "PA"), ("Youngstown State", "Youngstown", "OH"),
    ],
    "ASUN": [
        ("Bellarmine", "Louisville", "KY"), ("Florida Gulf Coast", "Fort Myers", "FL"),
        ("Jacksonville", "Jacksonville", "FL"), ("Lipscomb", "Nashville", "TN"),
        ("North Florida", "Jacksonville", "FL"), ("Queens (Charlotte)", "Charlotte", "NC"),
        ("Stetson", "DeLand", "FL"), ("West Florida", "Pensacola", "FL"),
    ],
    "Big South": [
        ("Charleston Southern", "Charleston", "SC"), ("Gardner-Webb", "Boiling Springs", "NC"),
        ("Longwood", "Farmville", "VA"), ("Presbyterian", "Clinton", "SC"),
        ("Radford", "Radford", "VA"), ("USC Upstate", "Spartanburg", "SC"),
        ("Winthrop", "Rock Hill", "SC"),
    ],
    "America East": [
        ("Albany", "Albany", "NY"), ("Binghamton", "Binghamton", "NY"),
        ("Bryant", "Smithfield", "RI"), ("Maine", "Orono", "ME"),
        ("UMass Lowell", "Lowell", "MA"), ("UMBC", "Baltimore", "MD"),
    ],
    "Big West": [
        ("Cal Poly", "San Luis Obispo", "CA"), ("CSU Fullerton", "Fullerton", "CA"),
        ("CSU Northridge", "Northridge", "CA"), ("California Baptist", "Riverside", "CA"),
        ("CSU Bakersfield", "Bakersfield", "CA"), ("Long Beach State", "Long Beach", "CA"),
        ("Sacramento State", "Sacramento", "CA"), ("UC Riverside", "Riverside", "CA"),
        ("UC San Diego", "San Diego", "CA"), ("UC Santa Barbara", "Santa Barbara", "CA"),
        ("Utah Valley", "Orem", "UT"),
    ],
    "Mountain West": [
        ("Air Force", "Colorado Springs", "CO"), ("Grand Canyon", "Phoenix", "AZ"),
        ("Hawaii", "Honolulu", "HI"), ("Nevada", "Reno", "NV"),
        ("UNLV", "Las Vegas", "NV"), ("New Mexico", "Albuquerque", "NM"),
        ("San Jose State", "San Jose", "CA"), ("UC Davis", "Davis", "CA"),
    ],
    "MAC": [
        ("Akron", "Akron", "OH"), ("Ball State", "Muncie", "IN"),
        ("Bowling Green", "Bowling Green", "OH"), ("Central Michigan", "Mount Pleasant", "MI"),
        ("Kent State", "Kent", "OH"), ("Ohio", "Athens", "OH"),
        ("Toledo", "Toledo", "OH"), ("UMass", "Amherst", "MA"),
    ],
    "Sun Belt": [
        ("Appalachian State", "Boone", "NC"), ("Coastal Carolina", "Conway", "SC"),
        ("Georgia Southern", "Statesboro", "GA"), ("Georgia State", "Atlanta", "GA"),
        ("James Madison", "Harrisonburg", "VA"), ("Louisiana", "Lafayette", "LA"),
        ("Marshall", "Huntington", "WV"), ("Old Dominion", "Norfolk", "VA"),
        ("South Alabama", "Mobile", "AL"), ("Troy", "Troy", "AL"),
    ],
    "SWAC": [
        ("Alabama A&M", "Huntsville", "AL"), ("Alabama State", "Montgomery", "AL"),
        ("Alcorn State", "Lorman", "MS"), ("Arkansas-Pine Bluff", "Pine Bluff", "AR"),
        ("Bethune-Cookman", "Daytona Beach", "FL"), ("Florida A&M", "Tallahassee", "FL"),
        ("Grambling State", "Grambling", "LA"), ("Jackson State", "Jackson", "MS"),
        ("Prairie View A&M", "Prairie View", "TX"), ("Southern", "Baton Rouge", "LA"),
        ("Texas Southern", "Houston", "TX"),
    ],
    "Southland": [
        ("East Texas A&M", "Commerce", "TX"), ("Houston Christian", "Houston", "TX"),
        ("Incarnate Word", "San Antonio", "TX"), ("Lamar", "Beaumont", "TX"),
        ("McNeese", "Lake Charles", "LA"), ("Nicholls", "Thibodaux", "LA"),
        ("Northwestern State", "Natchitoches", "LA"), ("Southeastern Louisiana", "Hammond", "LA"),
        ("Stephen F. Austin", "Nacogdoches", "TX"), ("Texas A&M-Corpus Christi", "Corpus Christi", "TX"),
    ],
    "MAAC": [
        ("Canisius", "Buffalo", "NY"), ("Fairfield", "Fairfield", "CT"),
        ("Iona", "New Rochelle", "NY"), ("Manhattan", "Riverdale", "NY"),
        ("Marist", "Poughkeepsie", "NY"), ("Merrimack", "North Andover", "MA"),
        ("Mount St. Mary's", "Emmitsburg", "MD"), ("Niagara", "Lewiston", "NY"),
        ("Quinnipiac", "Hamden", "CT"), ("Rider", "Lawrenceville", "NJ"),
        ("Sacred Heart", "Fairfield", "CT"), ("Saint Peter's", "Jersey City", "NJ"),
        ("Siena", "Loudonville", "NY"),
    ],
    "OVC": [
        ("Eastern Illinois", "Charleston", "IL"), ("Lindenwood", "St. Charles", "MO"),
        ("Morehead State", "Morehead", "KY"), ("Southeast Missouri State", "Cape Girardeau", "MO"),
        ("Southern Indiana", "Evansville", "IN"), ("SIU Edwardsville", "Edwardsville", "IL"),
        ("Tennessee State", "Nashville", "TN"), ("UT Martin", "Martin", "TN"),
        ("Western Illinois", "Macomb", "IL"),
    ],
    "SoCon": [
        ("Chattanooga", "Chattanooga", "TN"), ("East Tennessee State", "Johnson City", "TN"),
        ("Mercer", "Macon", "GA"), ("Samford", "Homewood", "AL"),
        ("UNC Greensboro", "Greensboro", "NC"), ("Western Carolina", "Cullowhee", "NC"),
    ],
    "Patriot League": [
        ("Army", "West Point", "NY"), ("Bucknell", "Lewisburg", "PA"),
        ("Colgate", "Hamilton", "NY"), ("Holy Cross", "Worcester", "MA"),
        ("Lafayette", "Easton", "PA"), ("Lehigh", "Bethlehem", "PA"),
    ],
    "Summit League": [
        ("UMKC", "Kansas City", "MO"), ("North Dakota", "Grand Forks", "ND"),
        ("North Dakota State", "Fargo", "ND"), ("South Dakota", "Vermillion", "SD"),
        ("Oral Roberts", "Tulsa", "OK"),
    ],
    "NEC": [
        ("Central Connecticut", "New Britain", "CT"), ("Fairleigh Dickinson", "Teaneck", "NJ"),
        ("Le Moyne", "Syracuse", "NY"), ("LIU", "Brooklyn", "NY"),
        ("Mercyhurst", "Erie", "PA"), ("New Haven", "West Haven", "CT"),
        ("Stonehill", "Easton", "MA"),
    ],
    "MEAC": [
        ("Coppin State", "Baltimore", "MD"), ("Delaware State", "Dover", "DE"),
        ("Howard", "Washington", "DC"), ("Maryland Eastern Shore", "Princess Anne", "MD"),
        ("Morgan State", "Baltimore", "MD"), ("Norfolk State", "Norfolk", "VA"),
        ("NC Central", "Durham", "NC"), ("South Carolina State", "Orangeburg", "SC"),
    ],
    "Ivy League": [
        ("Brown", "Providence", "RI"), ("Columbia", "New York", "NY"),
        ("Cornell", "Ithaca", "NY"), ("Dartmouth", "Hanover", "NH"),
        ("Harvard", "Cambridge", "MA"), ("Penn", "Philadelphia", "PA"),
        ("Princeton", "Princeton", "NJ"), ("Yale", "New Haven", "CT"),
    ],
}

IVY_NOTE = (
    "Included on moderate confidence: the source fetch showed only 4 of 8 "
    "Ivy schools before truncating mid-word at 'Har[vard]', strongly "
    "suggesting the underlying table continues alphabetically rather than "
    "stopping there. Corroborated by general knowledge that Ivy League "
    "softball has run as a full 8-team round robin for decades, but this "
    "is the one conference in this file not confirmed by a complete "
    "single-source table."
)


def slugify(school_name):
    return re.sub(r"[^A-Za-z0-9]+", "_", school_name).strip("_").lower()


def main():
    with open(ENTITIES_PATH, newline="", encoding="utf-8") as f:
        existing = list(csv.DictReader(f))
    existing_ids = {r["entity_id"] for r in existing}

    new_rows = []
    seen_ids = set()
    n_schools = 0
    for conference, schools in CONFERENCES.items():
        for school, city, state in schools:
            n_schools += 1
            slug = slugify(school)
            entity_id = f"sfb_{slug}"
            if entity_id in existing_ids or entity_id in seen_ids:
                raise ValueError(f"duplicate entity_id: {entity_id} ({school})")
            seen_ids.add(entity_id)
            new_rows.append({
                "entity_id": entity_id,
                "organization_id": f"college_{slug}",
                "entity_name": f"{school} Softball",
                "sport": "Softball",
                "sex_category": "women",
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
                "notes": IVY_NOTE if conference == "Ivy League" else "",
            })

    all_rows = existing + new_rows
    with open(ENTITIES_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Appended {len(new_rows)} softball entities across {len(CONFERENCES)} conferences")
    print(f"Total registry size: {len(all_rows)}")
    print(
        "DEFERRED (not included): Pac-12 and United Athletic Conference "
        "(formerly WAC) softball -- roughly 18 more programs, pending "
        "cleaner sourcing (same two conferences deferred for baseball)."
    )


if __name__ == "__main__":
    main()
