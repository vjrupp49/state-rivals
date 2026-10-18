"""Phase 4B step 1 (registry side, continued): append Division I college
baseball programs to data/registries/entities.csv.

docs/PROTOCOL.md section 6 names LSU baseball (11,185 avg attendance; 458,606
total, 2025) as an evidence-forced regional inclusion -- this is a complete
enumeration of D-I baseball-sponsoring programs, not just LSU.

Baseball sponsorship is NOT a simple subset of D-I membership: a
meaningful fraction of full conference members in every conference do not
field a baseball team at all (verified per-school, not assumed), and full
conferences can differ from their basketball/football membership. Two
whole conferences confirmed to sponsor NO baseball at all: Big Sky (dropped
it in 1974) and MEAC. Some MEAC/Big-Sky schools instead play baseball as
affiliate members of other conferences (e.g. Coppin State, Delaware State,
Maryland Eastern Shore, and Norfolk State play NEC baseball; Northern
Colorado plays Summit League baseball) -- these are tagged accordingly
below rather than dropped.

Verification notes / known gaps (2026-09-15):
- Two conferences are explicitly DEFERRED, not guessed: Pac-12 and the
  United Athletic Conference (formerly WAC). Wikipedia's sponsored-sports
  tables for both repeatedly failed to resolve on fetch (truncated/missing
  content across multiple attempts), and this script's author was not
  confident enough in general knowledge of either league's current
  per-school baseball sponsorship to commit it without a source. That's
  roughly 9 Pac-12 + 9 UAC schools not yet represented for baseball.
- The American Conference baseball list required resolving a direct
  contradiction between two Wikipedia fetches (one said Florida Atlantic,
  Tulane, and Wichita State sponsor baseball; a later fetch on the same
  page said they don't). Resolved in favor of "yes" for those three based
  on corroborating prior knowledge (Wichita State won the 1989 College
  World Series and has fielded baseball continuously; Tulane's program
  predates 1900) -- flagged here as a judgment call, not a clean single-
  source fact, unlike everything else in this file.
- Every other list below reflects a Wikipedia "men's sponsored sports by
  school" table fetch, generally cross-checked when a total looked off
  (e.g. Mountain West's baseball list initially returned only 5 of 10
  members and needed a second, more targeted fetch that reached 7, then a
  Nevada-specific check to resolve one remaining omission).

Run from the project root (after build_hockey_entities_registry.py):
    python scripts/build_baseball_entities_registry.py
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
    "Wikipedia 'Men's sponsored sports by school' tables, fetched per "
    "conference 2026-09-15, cross-checked against a per-conference member "
    "count where the first fetch looked incomplete. See script docstring "
    "for the specific American Conference judgment call and the two "
    "deferred conferences (Pac-12, UAC)."
)

# conference_name -> [(school, city, state), ...] for schools CONFIRMED to
# sponsor baseball (i.e. already filtered down from full conference
# membership).
CONFERENCES = {
    "ACC": [
        ("Boston College", "Chestnut Hill", "MA"), ("California", "Berkeley", "CA"),
        ("Clemson", "Clemson", "SC"), ("Duke", "Durham", "NC"),
        ("Florida State", "Tallahassee", "FL"), ("Georgia Tech", "Atlanta", "GA"),
        ("Louisville", "Louisville", "KY"), ("Miami (FL)", "Coral Gables", "FL"),
        ("North Carolina", "Chapel Hill", "NC"), ("NC State", "Raleigh", "NC"),
        ("Notre Dame", "Notre Dame", "IN"), ("Pittsburgh", "Pittsburgh", "PA"),
        ("Stanford", "Stanford", "CA"), ("Virginia", "Charlottesville", "VA"),
        ("Virginia Tech", "Blacksburg", "VA"), ("Wake Forest", "Winston-Salem", "NC"),
    ],
    "Big Ten": [
        ("Illinois", "Champaign", "IL"), ("Indiana", "Bloomington", "IN"),
        ("Iowa", "Iowa City", "IA"), ("Maryland", "College Park", "MD"),
        ("Michigan", "Ann Arbor", "MI"), ("Michigan State", "East Lansing", "MI"),
        ("Minnesota", "Minneapolis", "MN"), ("Nebraska", "Lincoln", "NE"),
        ("Northwestern", "Evanston", "IL"), ("Ohio State", "Columbus", "OH"),
        ("Oregon", "Eugene", "OR"), ("Penn State", "University Park", "PA"),
        ("Purdue", "West Lafayette", "IN"), ("Rutgers", "Piscataway", "NJ"),
        ("UCLA", "Los Angeles", "CA"), ("USC", "Los Angeles", "CA"),
        ("Washington", "Seattle", "WA"),
    ],
    "Big 12": [
        ("Arizona", "Tucson", "AZ"), ("Arizona State", "Tempe", "AZ"),
        ("Baylor", "Waco", "TX"), ("BYU", "Provo", "UT"),
        ("Cincinnati", "Cincinnati", "OH"), ("Houston", "Houston", "TX"),
        ("Kansas", "Lawrence", "KS"), ("Kansas State", "Manhattan", "KS"),
        ("Oklahoma State", "Stillwater", "OK"), ("TCU", "Fort Worth", "TX"),
        ("Texas Tech", "Lubbock", "TX"), ("UCF", "Orlando", "FL"),
        ("Utah", "Salt Lake City", "UT"), ("West Virginia", "Morgantown", "WV"),
    ],
    "SEC": [
        ("Alabama", "Tuscaloosa", "AL"), ("Arkansas", "Fayetteville", "AR"),
        ("Auburn", "Auburn", "AL"), ("Florida", "Gainesville", "FL"),
        ("Georgia", "Athens", "GA"), ("Kentucky", "Lexington", "KY"),
        ("LSU", "Baton Rouge", "LA"), ("Ole Miss", "Oxford", "MS"),
        ("Mississippi State", "Starkville", "MS"), ("Missouri", "Columbia", "MO"),
        ("Oklahoma", "Norman", "OK"), ("South Carolina", "Columbia", "SC"),
        ("Tennessee", "Knoxville", "TN"), ("Texas", "Austin", "TX"),
        ("Texas A&M", "College Station", "TX"), ("Vanderbilt", "Nashville", "TN"),
    ],
    "Big East": [
        ("Butler", "Indianapolis", "IN"), ("UConn", "Storrs", "CT"),
        ("Creighton", "Omaha", "NE"), ("DePaul", "Chicago", "IL"),
        ("Providence", "Providence", "RI"), ("St. John's", "Queens", "NY"),
        ("Seton Hall", "South Orange", "NJ"), ("Villanova", "Villanova", "PA"),
        ("Xavier", "Cincinnati", "OH"),
    ],
    "Atlantic 10": [
        ("Davidson", "Davidson", "NC"), ("Dayton", "Dayton", "OH"),
        ("Fordham", "Bronx", "NY"), ("George Mason", "Fairfax", "VA"),
        ("George Washington", "Washington", "DC"), ("La Salle", "Philadelphia", "PA"),
        ("Rhode Island", "Kingston", "RI"), ("Richmond", "Richmond", "VA"),
        ("St. Bonaventure", "St. Bonaventure", "NY"), ("Saint Joseph's", "Philadelphia", "PA"),
        ("Saint Louis", "St. Louis", "MO"), ("VCU", "Richmond", "VA"),
    ],
    "West Coast Conference": [
        ("Loyola Marymount", "Los Angeles", "CA"), ("Pacific", "Stockton", "CA"),
        ("Pepperdine", "Malibu", "CA"), ("Portland", "Portland", "OR"),
        ("Saint Mary's", "Moraga", "CA"), ("San Diego", "San Diego", "CA"),
        ("San Francisco", "San Francisco", "CA"), ("Santa Clara", "Santa Clara", "CA"),
        ("Seattle", "Seattle", "WA"),
    ],
    "Missouri Valley Conference": [
        ("Belmont", "Nashville", "TN"), ("Bradley", "Peoria", "IL"),
        ("Evansville", "Evansville", "IN"), ("UIC", "Chicago", "IL"),
        ("Illinois State", "Normal", "IL"), ("Indiana State", "Terre Haute", "IN"),
        ("Murray State", "Murray", "KY"), ("Southern Illinois", "Carbondale", "IL"),
        ("Valparaiso", "Valparaiso", "IN"),
    ],
    "Mountain West": [
        ("Air Force", "Colorado Springs", "CO"), ("Grand Canyon", "Phoenix", "AZ"),
        ("Hawaii", "Honolulu", "HI"), ("Nevada", "Reno", "NV"),
        ("UNLV", "Las Vegas", "NV"), ("New Mexico", "Albuquerque", "NM"),
        ("San Jose State", "San Jose", "CA"),
    ],
    "American": [
        ("UAB", "Birmingham", "AL"), ("East Carolina", "Greenville", "NC"),
        ("Florida Atlantic", "Boca Raton", "FL"), ("Memphis", "Memphis", "TN"),
        ("Charlotte", "Charlotte", "NC"), ("Rice", "Houston", "TX"),
        ("South Florida", "Tampa", "FL"), ("UTSA", "San Antonio", "TX"),
        ("Tulane", "New Orleans", "LA"), ("Wichita State", "Wichita", "KS"),
    ],
    "MAC": [
        ("Akron", "Akron", "OH"), ("Ball State", "Muncie", "IN"),
        ("Bowling Green", "Bowling Green", "OH"), ("Central Michigan", "Mount Pleasant", "MI"),
        ("Eastern Michigan", "Ypsilanti", "MI"), ("Kent State", "Kent", "OH"),
        ("UMass", "Amherst", "MA"), ("Miami (OH)", "Oxford", "OH"),
        ("Ohio", "Athens", "OH"), ("Toledo", "Toledo", "OH"),
        ("Western Michigan", "Kalamazoo", "MI"),
    ],
    "Conference USA": [
        ("Delaware", "Newark", "DE"), ("FIU", "Miami", "FL"),
        ("Jacksonville State", "Jacksonville", "AL"), ("Kennesaw State", "Kennesaw", "GA"),
        ("Liberty", "Lynchburg", "VA"), ("Middle Tennessee", "Murfreesboro", "TN"),
        ("Missouri State", "Springfield", "MO"), ("New Mexico State", "Las Cruces", "NM"),
        ("Sam Houston", "Huntsville", "TX"), ("Western Kentucky", "Bowling Green", "KY"),
    ],
    "Sun Belt": [
        ("Appalachian State", "Boone", "NC"), ("Arkansas State", "Jonesboro", "AR"),
        ("Coastal Carolina", "Conway", "SC"), ("Georgia Southern", "Statesboro", "GA"),
        ("Georgia State", "Atlanta", "GA"), ("James Madison", "Harrisonburg", "VA"),
        ("Marshall", "Huntington", "WV"), ("Old Dominion", "Norfolk", "VA"),
        ("Louisiana", "Lafayette", "LA"), ("Louisiana Monroe", "Monroe", "LA"),
        ("Louisiana Tech", "Ruston", "LA"), ("South Alabama", "Mobile", "AL"),
        ("Southern Miss", "Hattiesburg", "MS"), ("Troy", "Troy", "AL"),
    ],
    "Ivy League": [
        ("Brown", "Providence", "RI"), ("Columbia", "New York", "NY"),
        ("Cornell", "Ithaca", "NY"), ("Dartmouth", "Hanover", "NH"),
        ("Harvard", "Cambridge", "MA"), ("Penn", "Philadelphia", "PA"),
        ("Princeton", "Princeton", "NJ"), ("Yale", "New Haven", "CT"),
    ],
    "CAA": [
        ("Campbell", "Buies Creek", "NC"), ("Charleston", "Charleston", "SC"),
        ("Elon", "Elon", "NC"), ("Hofstra", "Hempstead", "NY"),
        ("Monmouth", "West Long Branch", "NJ"), ("NC A&T", "Greensboro", "NC"),
        ("Northeastern", "Boston", "MA"), ("Stony Brook", "Stony Brook", "NY"),
        ("Towson", "Towson", "MD"), ("UNC Wilmington", "Wilmington", "NC"),
        ("William & Mary", "Williamsburg", "VA"),
    ],
    "Horizon League": [
        ("Milwaukee", "Milwaukee", "WI"), ("Northern Illinois", "DeKalb", "IL"),
        ("Northern Kentucky", "Highland Heights", "KY"), ("Oakland", "Rochester", "MI"),
        ("Wright State", "Dayton", "OH"), ("Youngstown State", "Youngstown", "OH"),
    ],
    "ASUN": [
        ("Bellarmine", "Louisville", "KY"), ("Florida Gulf Coast", "Fort Myers", "FL"),
        ("Jacksonville", "Jacksonville", "FL"), ("Lipscomb", "Nashville", "TN"),
        ("North Florida", "Jacksonville", "FL"), ("Queens (Charlotte)", "Charlotte", "NC"),
        ("Stetson", "DeLand", "FL"),
    ],
    "Big South": [
        ("Charleston Southern", "Charleston", "SC"), ("Gardner-Webb", "Boiling Springs", "NC"),
        ("High Point", "High Point", "NC"), ("Longwood", "Farmville", "VA"),
        ("Presbyterian", "Clinton", "SC"), ("Radford", "Radford", "VA"),
        ("UNC Asheville", "Asheville", "NC"), ("USC Upstate", "Spartanburg", "SC"),
        ("Winthrop", "Rock Hill", "SC"),
    ],
    "Southland": [
        ("East Texas A&M", "Commerce", "TX"), ("Houston Christian", "Houston", "TX"),
        ("Incarnate Word", "San Antonio", "TX"), ("Lamar", "Beaumont", "TX"),
        ("New Orleans", "New Orleans", "LA"), ("McNeese", "Lake Charles", "LA"),
        ("Nicholls", "Thibodaux", "LA"), ("Northwestern State", "Natchitoches", "LA"),
        ("Southeastern Louisiana", "Hammond", "LA"), ("Stephen F. Austin", "Nacogdoches", "TX"),
        ("Texas A&M-Corpus Christi", "Corpus Christi", "TX"),
    ],
    "SoCon": [
        ("Citadel", "Charleston", "SC"), ("East Tennessee State", "Johnson City", "TN"),
        ("Mercer", "Macon", "GA"), ("Samford", "Homewood", "AL"),
        ("Tennessee Tech", "Cookeville", "TN"), ("UNC Greensboro", "Greensboro", "NC"),
        ("Western Carolina", "Cullowhee", "NC"), ("Wofford", "Spartanburg", "SC"),
    ],
    "OVC": [
        ("Eastern Illinois", "Charleston", "IL"), ("Lindenwood", "St. Charles", "MO"),
        ("Morehead State", "Morehead", "KY"), ("SIU Edwardsville", "Edwardsville", "IL"),
        ("Southeast Missouri State", "Cape Girardeau", "MO"), ("Southern Indiana", "Evansville", "IN"),
        ("UT Martin", "Martin", "TN"), ("Western Illinois", "Macomb", "IL"),
    ],
    "SWAC": [
        ("Alabama A&M", "Huntsville", "AL"), ("Alabama State", "Montgomery", "AL"),
        ("Alcorn State", "Lorman", "MS"), ("Arkansas-Pine Bluff", "Pine Bluff", "AR"),
        ("Bethune-Cookman", "Daytona Beach", "FL"), ("Florida A&M", "Tallahassee", "FL"),
        ("Grambling State", "Grambling", "LA"), ("Jackson State", "Jackson", "MS"),
        ("Mississippi Valley State", "Itta Bena", "MS"), ("Prairie View A&M", "Prairie View", "TX"),
        ("Southern", "Baton Rouge", "LA"), ("Texas Southern", "Houston", "TX"),
    ],
    "Big West": [
        ("California Baptist", "Riverside", "CA"), ("Cal Poly", "San Luis Obispo", "CA"),
        ("CSU Bakersfield", "Bakersfield", "CA"), ("CSU Fullerton", "Fullerton", "CA"),
        ("Long Beach State", "Long Beach", "CA"), ("CSU Northridge", "Northridge", "CA"),
        ("Sacramento State", "Sacramento", "CA"), ("UC Irvine", "Irvine", "CA"),
        ("UC Riverside", "Riverside", "CA"), ("UC San Diego", "San Diego", "CA"),
        ("UC Santa Barbara", "Santa Barbara", "CA"), ("Utah Valley", "Orem", "UT"),
    ],
    "Patriot League": [
        ("Army", "West Point", "NY"), ("Bucknell", "Lewisburg", "PA"),
        ("Holy Cross", "Worcester", "MA"), ("Lafayette", "Easton", "PA"),
        ("Lehigh", "Bethlehem", "PA"),
    ],
    "Summit League": [
        ("North Dakota State", "Fargo", "ND"), ("Oral Roberts", "Tulsa", "OK"),
        ("St. Thomas", "St. Paul", "MN"), ("South Dakota", "Vermillion", "SD"),
        ("Nebraska Omaha", "Omaha", "NE"), ("UMKC", "Kansas City", "MO"),
        ("Northern Colorado", "Greeley", "CO"),
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
    "NEC": [
        ("Central Connecticut", "New Britain", "CT"), ("Fairleigh Dickinson", "Teaneck", "NJ"),
        ("Le Moyne", "Syracuse", "NY"), ("LIU", "Brooklyn", "NY"),
        ("Mercyhurst", "Erie", "PA"), ("New Haven", "West Haven", "CT"),
        ("Stonehill", "Easton", "MA"), ("Wagner", "Staten Island", "NY"),
    ],
    "America East": [
        ("Albany", "Albany", "NY"), ("Binghamton", "Binghamton", "NY"),
        ("Bryant", "Smithfield", "RI"), ("Maine", "Orono", "ME"),
        ("NJIT", "Newark", "NJ"), ("UMass Lowell", "Lowell", "MA"),
        ("UMBC", "Baltimore", "MD"),
    ],
}

# schools whose HOME conference doesn't sponsor baseball, so they play
# baseball as an affiliate/associate member of a different conference.
BASEBALL_AFFILIATES = {
    "NEC (baseball affiliate; home conference MEAC)": [
        ("Coppin State", "Baltimore", "MD"), ("Delaware State", "Dover", "DE"),
        ("Maryland Eastern Shore", "Princess Anne", "MD"), ("Norfolk State", "Norfolk", "VA"),
    ],
}


def slugify(school_name):
    return re.sub(r"[^A-Za-z0-9]+", "_", school_name).strip("_").lower()


def main():
    with open(ENTITIES_PATH, newline="", encoding="utf-8") as f:
        existing = list(csv.DictReader(f))
    existing_ids = {r["entity_id"] for r in existing}

    new_rows = []
    seen_ids = set()

    def add(school, city, state, conference, notes=""):
        slug = slugify(school)
        entity_id = f"bsb_{slug}"
        if entity_id in existing_ids or entity_id in seen_ids:
            raise ValueError(f"duplicate entity_id: {entity_id} ({school})")
        seen_ids.add(entity_id)
        new_rows.append({
            "entity_id": entity_id,
            "organization_id": f"college_{slug}",
            "entity_name": f"{school} Baseball",
            "sport": "Baseball",
            "sex_category": "men",
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
            "notes": notes,
        })

    n_schools = 0
    for conference, schools in CONFERENCES.items():
        for school, city, state in schools:
            n_schools += 1
            add(school, city, state, conference)

    for conference, schools in BASEBALL_AFFILIATES.items():
        for school, city, state in schools:
            n_schools += 1
            add(school, city, state, conference,
                notes="Baseball-only affiliate; MEAC (this school's home "
                      "conference for other sports) does not sponsor "
                      "baseball at all.")

    all_rows = existing + new_rows
    with open(ENTITIES_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Appended {len(new_rows)} baseball entities across {len(CONFERENCES) + len(BASEBALL_AFFILIATES)} conference groupings")
    print(f"Total registry size: {len(all_rows)}")
    print(
        "DEFERRED (not included): Pac-12 and United Athletic Conference "
        "(formerly WAC) baseball -- roughly 18 more programs, pending "
        "cleaner sourcing. Big Sky and MEAC confirmed to sponsor no "
        "baseball at all."
    )


if __name__ == "__main__":
    main()
