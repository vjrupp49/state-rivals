"""Phase 4B step 1 (registry side, continued): append men's and women's
Division I college basketball programs to data/registries/entities.csv.

Unlike college football (build_cfb_entities_registry.py, which was
evidence-bootstrapped from a Vivid Seats scrape), this is a COMPLETE
enumeration of all current NCAA Division I member institutions, each
producing two entities (men's and women's basketball program). docs/PROTOCOL.md
section 5 is explicit that "all Division I varsity programs are automatic
candidates" for the registry -- entity registry membership is not the same
thing as "active" status in the A-matrix (that's decided later by the
0.25%/98%/opponent-activation thresholds in section 6). No Vivid Seats
county-level fandom map exists for college basketball (checked directly),
so there is no equivalent evidence-bootstrap available here the way there
was for football.

Conference membership verified 2026-09-15 against each conference's current
Wikipedia page, one conference at a time (32 conferences), because the
combined "List of NCAA Division I institutions" page truncates on fetch.
Total across all 32 conferences: 365 institutions, matching Wikipedia's
independently stated "currently 365 institutions classified as Division I"
figure -- a useful cross-check that the conference-by-conference tally has
no double-counts or gaps.

Two cross-conference notes caught along the way:
- Gonzaga is a full member of the rebuilt Pac-12 for basketball (a
  "non-football" member), NOT the West Coast Conference where it used to
  play -- easy to get wrong from memory/stale sources.
- The WAC rebranded to the United Athletic Conference (UAC) effective
  2026-07-01; some of its current members (Abilene Christian, Tarleton
  State, North Alabama, Eastern Kentucky, Austin Peay) already appear in
  the football registry tagged "UAC", so this is consistent, not a
  duplicate naming scheme.
- Several institutions (e.g. North Dakota State, South Dakota State) play
  Summit League basketball despite NDSU's football program having moved to
  FBS/Mountain West -- basketball and football conference membership are
  genuinely independent and both are correct.

This still is not exhaustive of every possible D-I basketball-only
independent, and home_city for a handful of schools is a reasonable
best-known value rather than independently re-verified here.

Run from the project root (after build_cfb_entities_registry.py):
    python scripts/build_cbb_entities_registry.py
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
    "Conference membership verified 2026-09-15 against each conference's "
    "current Wikipedia page (32 D-I basketball conferences, fetched "
    "individually); cross-checked total (365) against Wikipedia's "
    "'List_of_NCAA_Division_I_institutions' stated institution count."
)

# conference_name -> [(school_name, city, state), ...]
CONFERENCES = {
    "ACC": [
        ("Boston College", "Chestnut Hill", "MA"), ("California", "Berkeley", "CA"),
        ("Clemson", "Clemson", "SC"), ("Duke", "Durham", "NC"),
        ("Florida State", "Tallahassee", "FL"), ("Georgia Tech", "Atlanta", "GA"),
        ("Louisville", "Louisville", "KY"), ("Miami (FL)", "Coral Gables", "FL"),
        ("North Carolina", "Chapel Hill", "NC"), ("NC State", "Raleigh", "NC"),
        ("Notre Dame", "Notre Dame", "IN"), ("Pittsburgh", "Pittsburgh", "PA"),
        ("SMU", "Dallas", "TX"), ("Stanford", "Stanford", "CA"),
        ("Syracuse", "Syracuse", "NY"), ("Virginia", "Charlottesville", "VA"),
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
        ("Washington", "Seattle", "WA"), ("Wisconsin", "Madison", "WI"),
    ],
    "Big 12": [
        ("Arizona", "Tucson", "AZ"), ("Arizona State", "Tempe", "AZ"),
        ("Baylor", "Waco", "TX"), ("BYU", "Provo", "UT"),
        ("UCF", "Orlando", "FL"), ("Cincinnati", "Cincinnati", "OH"),
        ("Colorado", "Boulder", "CO"), ("Houston", "Houston", "TX"),
        ("Iowa State", "Ames", "IA"), ("Kansas", "Lawrence", "KS"),
        ("Kansas State", "Manhattan", "KS"), ("Oklahoma State", "Stillwater", "OK"),
        ("TCU", "Fort Worth", "TX"), ("Texas Tech", "Lubbock", "TX"),
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
        ("Georgetown", "Washington", "DC"), ("Marquette", "Milwaukee", "WI"),
        ("Providence", "Providence", "RI"), ("St. John's", "Queens", "NY"),
        ("Seton Hall", "South Orange", "NJ"), ("Villanova", "Villanova", "PA"),
        ("Xavier", "Cincinnati", "OH"),
    ],
    "Atlantic 10": [
        ("Davidson", "Davidson", "NC"), ("Dayton", "Dayton", "OH"),
        ("Duquesne", "Pittsburgh", "PA"), ("Fordham", "Bronx", "NY"),
        ("George Mason", "Fairfax", "VA"), ("George Washington", "Washington", "DC"),
        ("La Salle", "Philadelphia", "PA"), ("Loyola Chicago", "Chicago", "IL"),
        ("Rhode Island", "Kingston", "RI"), ("Richmond", "Richmond", "VA"),
        ("St. Bonaventure", "St. Bonaventure", "NY"), ("Saint Joseph's", "Philadelphia", "PA"),
        ("Saint Louis", "St. Louis", "MO"), ("VCU", "Richmond", "VA"),
    ],
    "West Coast Conference": [
        ("Denver", "Denver", "CO"), ("Loyola Marymount", "Los Angeles", "CA"),
        ("Pacific", "Stockton", "CA"), ("Pepperdine", "Malibu", "CA"),
        ("Portland", "Portland", "OR"), ("Saint Mary's", "Moraga", "CA"),
        ("San Diego", "San Diego", "CA"), ("San Francisco", "San Francisco", "CA"),
        ("Santa Clara", "Santa Clara", "CA"), ("Seattle", "Seattle", "WA"),
    ],
    "Missouri Valley Conference": [
        ("Belmont", "Nashville", "TN"), ("Bradley", "Peoria", "IL"),
        ("Drake", "Des Moines", "IA"), ("Evansville", "Evansville", "IN"),
        ("UIC", "Chicago", "IL"), ("Illinois State", "Normal", "IL"),
        ("Indiana State", "Terre Haute", "IN"), ("Murray State", "Murray", "KY"),
        ("Northern Iowa", "Cedar Falls", "IA"), ("Southern Illinois", "Carbondale", "IL"),
        ("Valparaiso", "Valparaiso", "IN"),
    ],
    "Mountain West": [
        ("Air Force", "Colorado Springs", "CO"), ("Grand Canyon", "Phoenix", "AZ"),
        ("UC Davis", "Davis", "CA"), ("Hawaii", "Honolulu", "HI"),
        ("Nevada", "Reno", "NV"), ("UNLV", "Las Vegas", "NV"),
        ("New Mexico", "Albuquerque", "NM"), ("San Jose State", "San Jose", "CA"),
        ("UTEP", "El Paso", "TX"), ("Wyoming", "Laramie", "WY"),
    ],
    "American": [
        ("UAB", "Birmingham", "AL"), ("East Carolina", "Greenville", "NC"),
        ("Florida Atlantic", "Boca Raton", "FL"), ("Memphis", "Memphis", "TN"),
        ("Charlotte", "Charlotte", "NC"), ("North Texas", "Denton", "TX"),
        ("Rice", "Houston", "TX"), ("South Florida", "Tampa", "FL"),
        ("Temple", "Philadelphia", "PA"), ("UTSA", "San Antonio", "TX"),
        ("Tulane", "New Orleans", "LA"), ("Tulsa", "Tulsa", "OK"),
        ("Wichita State", "Wichita", "KS"),
    ],
    "MAC": [
        ("Akron", "Akron", "OH"), ("Ball State", "Muncie", "IN"),
        ("Bowling Green", "Bowling Green", "OH"), ("Buffalo", "Buffalo", "NY"),
        ("Central Michigan", "Mount Pleasant", "MI"), ("Eastern Michigan", "Ypsilanti", "MI"),
        ("Kent State", "Kent", "OH"), ("UMass", "Amherst", "MA"),
        ("Miami (OH)", "Oxford", "OH"), ("Ohio", "Athens", "OH"),
        ("Toledo", "Toledo", "OH"), ("Western Michigan", "Kalamazoo", "MI"),
    ],
    "Conference USA": [
        ("Delaware", "Newark", "DE"), ("FIU", "Miami", "FL"),
        ("Jacksonville State", "Jacksonville", "AL"), ("Kennesaw State", "Kennesaw", "GA"),
        ("Liberty", "Lynchburg", "VA"), ("Middle Tennessee", "Murfreesboro", "TN"),
        ("Missouri State", "Springfield", "MO"), ("New Mexico State", "Las Cruces", "NM"),
        ("Sam Houston", "Huntsville", "TX"), ("Western Kentucky", "Bowling Green", "KY"),
    ],
    "Sun Belt": [
        ("Appalachian State", "Boone", "NC"), ("Coastal Carolina", "Conway", "SC"),
        ("Georgia Southern", "Statesboro", "GA"), ("Georgia State", "Atlanta", "GA"),
        ("James Madison", "Harrisonburg", "VA"), ("Marshall", "Huntington", "WV"),
        ("Old Dominion", "Norfolk", "VA"), ("Arkansas State", "Jonesboro", "AR"),
        ("Louisiana", "Lafayette", "LA"), ("Louisiana Monroe", "Monroe", "LA"),
        ("Louisiana Tech", "Ruston", "LA"), ("South Alabama", "Mobile", "AL"),
        ("Southern Miss", "Hattiesburg", "MS"), ("Troy", "Troy", "AL"),
    ],
    "Pac-12": [
        ("Boise State", "Boise", "ID"), ("Fresno State", "Fresno", "CA"),
        ("Colorado State", "Fort Collins", "CO"), ("Gonzaga", "Spokane", "WA"),
        ("Oregon State", "Corvallis", "OR"), ("San Diego State", "San Diego", "CA"),
        ("Texas State", "San Marcos", "TX"), ("Utah State", "Logan", "UT"),
        ("Washington State", "Pullman", "WA"),
    ],
    "Ivy League": [
        ("Brown", "Providence", "RI"), ("Columbia", "New York", "NY"),
        ("Cornell", "Ithaca", "NY"), ("Dartmouth", "Hanover", "NH"),
        ("Harvard", "Cambridge", "MA"), ("Penn", "Philadelphia", "PA"),
        ("Princeton", "Princeton", "NJ"), ("Yale", "New Haven", "CT"),
    ],
    "Patriot League": [
        ("American University", "Washington", "DC"), ("Army", "West Point", "NY"),
        ("Boston University", "Boston", "MA"), ("Bucknell", "Lewisburg", "PA"),
        ("Colgate", "Hamilton", "NY"), ("Holy Cross", "Worcester", "MA"),
        ("Lafayette", "Easton", "PA"), ("Lehigh", "Bethlehem", "PA"),
        ("Loyola Maryland", "Baltimore", "MD"), ("Navy", "Annapolis", "MD"),
    ],
    "CAA": [
        ("Campbell", "Buies Creek", "NC"), ("Charleston", "Charleston", "SC"),
        ("Drexel", "Philadelphia", "PA"), ("Elon", "Elon", "NC"),
        ("Hampton", "Hampton", "VA"), ("Hofstra", "Hempstead", "NY"),
        ("Monmouth", "West Long Branch", "NJ"), ("NC A&T", "Greensboro", "NC"),
        ("Northeastern", "Boston", "MA"), ("Stony Brook", "Stony Brook", "NY"),
        ("Towson", "Towson", "MD"), ("UNC Wilmington", "Wilmington", "NC"),
        ("William & Mary", "Williamsburg", "VA"),
    ],
    "Horizon League": [
        ("Cleveland State", "Cleveland", "OH"), ("Detroit Mercy", "Detroit", "MI"),
        ("Green Bay", "Green Bay", "WI"), ("IU Indianapolis", "Indianapolis", "IN"),
        ("Milwaukee", "Milwaukee", "WI"), ("Northern Illinois", "DeKalb", "IL"),
        ("Northern Kentucky", "Highland Heights", "KY"), ("Oakland", "Rochester", "MI"),
        ("Purdue Fort Wayne", "Fort Wayne", "IN"), ("Robert Morris", "Moon Township", "PA"),
        ("Wright State", "Dayton", "OH"), ("Youngstown State", "Youngstown", "OH"),
    ],
    "Summit League": [
        ("UMKC", "Kansas City", "MO"), ("Nebraska Omaha", "Omaha", "NE"),
        ("North Dakota", "Grand Forks", "ND"), ("North Dakota State", "Fargo", "ND"),
        ("Oral Roberts", "Tulsa", "OK"), ("St. Thomas", "St. Paul", "MN"),
        ("South Dakota", "Vermillion", "SD"), ("South Dakota State", "Brookings", "SD"),
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
    "Big Sky": [
        ("Eastern Washington", "Cheney", "WA"), ("Idaho", "Moscow", "ID"),
        ("Idaho State", "Pocatello", "ID"), ("Montana", "Missoula", "MT"),
        ("Montana State", "Bozeman", "MT"), ("Northern Arizona", "Flagstaff", "AZ"),
        ("Northern Colorado", "Greeley", "CO"), ("Portland State", "Portland", "OR"),
        ("Southern Utah", "Cedar City", "UT"), ("Utah Tech", "St. George", "UT"),
        ("Weber State", "Ogden", "UT"),
    ],
    "Big South": [
        ("Charleston Southern", "Charleston", "SC"), ("Gardner-Webb", "Boiling Springs", "NC"),
        ("High Point", "High Point", "NC"), ("Longwood", "Farmville", "VA"),
        ("Presbyterian", "Clinton", "SC"), ("Radford", "Radford", "VA"),
        ("UNC Asheville", "Asheville", "NC"), ("USC Upstate", "Spartanburg", "SC"),
        ("Winthrop", "Rock Hill", "SC"),
    ],
    "ASUN": [
        ("Bellarmine", "Louisville", "KY"), ("Florida Gulf Coast", "Fort Myers", "FL"),
        ("Jacksonville", "Jacksonville", "FL"), ("Lipscomb", "Nashville", "TN"),
        ("North Florida", "Jacksonville", "FL"), ("Queens (Charlotte)", "Charlotte", "NC"),
        ("Stetson", "DeLand", "FL"), ("West Florida", "Pensacola", "FL"),
    ],
    "America East": [
        ("Albany", "Albany", "NY"), ("Binghamton", "Binghamton", "NY"),
        ("Bryant", "Smithfield", "RI"), ("Maine", "Orono", "ME"),
        ("UMBC", "Baltimore", "MD"), ("UMass Lowell", "Lowell", "MA"),
        ("New Hampshire", "Durham", "NH"), ("NJIT", "Newark", "NJ"),
        ("Vermont", "Burlington", "VT"),
    ],
    "Southland": [
        ("East Texas A&M", "Commerce", "TX"), ("Houston Christian", "Houston", "TX"),
        ("Incarnate Word", "San Antonio", "TX"), ("Lamar", "Beaumont", "TX"),
        ("New Orleans", "New Orleans", "LA"), ("McNeese", "Lake Charles", "LA"),
        ("Nicholls", "Thibodaux", "LA"), ("Northwestern State", "Natchitoches", "LA"),
        ("Southeastern Louisiana", "Hammond", "LA"), ("Stephen F. Austin", "Nacogdoches", "TX"),
        ("Texas A&M-Corpus Christi", "Corpus Christi", "TX"), ("UT Rio Grande Valley", "Edinburg", "TX"),
    ],
    "United Athletic Conference": [
        ("Abilene Christian", "Abilene", "TX"), ("Austin Peay", "Clarksville", "TN"),
        ("Central Arkansas", "Conway", "AR"), ("Eastern Kentucky", "Richmond", "KY"),
        ("Arkansas-Little Rock", "Little Rock", "AR"), ("North Alabama", "Florence", "AL"),
        ("Tarleton State", "Stephenville", "TX"), ("UT Arlington", "Arlington", "TX"),
        ("West Georgia", "Carrollton", "GA"),
    ],
    "SoCon": [
        ("Chattanooga", "Chattanooga", "TN"), ("Citadel", "Charleston", "SC"),
        ("East Tennessee State", "Johnson City", "TN"), ("Furman", "Greenville", "SC"),
        ("Mercer", "Macon", "GA"), ("Samford", "Homewood", "AL"),
        ("UNC Greensboro", "Greensboro", "NC"), ("Tennessee Tech", "Cookeville", "TN"),
        ("VMI", "Lexington", "VA"), ("Western Carolina", "Cullowhee", "NC"),
        ("Wofford", "Spartanburg", "SC"),
    ],
    "OVC": [
        ("Eastern Illinois", "Charleston", "IL"), ("Lindenwood", "St. Charles", "MO"),
        ("Morehead State", "Morehead", "KY"), ("Southeast Missouri State", "Cape Girardeau", "MO"),
        ("SIU Edwardsville", "Edwardsville", "IL"), ("Southern Indiana", "Evansville", "IN"),
        ("Tennessee State", "Nashville", "TN"), ("UT Martin", "Martin", "TN"),
        ("Western Illinois", "Macomb", "IL"),
    ],
    "NEC": [
        ("Central Connecticut", "New Britain", "CT"), ("Chicago State", "Chicago", "IL"),
        ("Fairleigh Dickinson", "Teaneck", "NJ"), ("Le Moyne", "Syracuse", "NY"),
        ("LIU", "Brooklyn", "NY"), ("Mercyhurst", "Erie", "PA"),
        ("New Haven", "West Haven", "CT"), ("Stonehill", "Easton", "MA"),
        ("Wagner", "Staten Island", "NY"),
    ],
    "MEAC": [
        ("Coppin State", "Baltimore", "MD"), ("Delaware State", "Dover", "DE"),
        ("Howard", "Washington", "DC"), ("Maryland Eastern Shore", "Princess Anne", "MD"),
        ("Morgan State", "Baltimore", "MD"), ("Norfolk State", "Norfolk", "VA"),
        ("NC Central", "Durham", "NC"), ("South Carolina State", "Orangeburg", "SC"),
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
}


def slugify(school_name):
    name = re.sub(r"[^A-Za-z0-9]+", "_", school_name).strip("_").lower()
    return name


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
            for sex, label in [("men", "Men's Basketball"), ("women", "Women's Basketball")]:
                entity_id = f"cbb_{sex[0]}_{slug}"
                if entity_id in existing_ids or entity_id in seen_ids:
                    raise ValueError(f"duplicate entity_id: {entity_id} ({school})")
                seen_ids.add(entity_id)
                new_rows.append({
                    "entity_id": entity_id,
                    "organization_id": f"college_{slug}",
                    "entity_name": f"{school} {label}",
                    "sport": "Basketball",
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

    print(f"Institutions covered: {n_schools} (across {len(CONFERENCES)} conferences)")
    print(f"Appended {len(new_rows)} basketball entities (men's + women's)")
    print(f"Total registry size: {len(all_rows)}")


if __name__ == "__main__":
    main()
