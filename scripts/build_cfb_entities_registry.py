"""Phase 4B step 1 (registry side, continued): append college football
programs to data/registries/entities.csv.

Scope decision: rather than trying to enumerate the full ~260-program FBS+FCS
universe (and the much larger D-II/D-III/NAIA tail) from scratch, this script
uses the 168 program names that ALREADY surfaced as a real county-plurality
winner somewhere in data/raw/vividseats_cfb_county_raw.csv. That scrape is
itself real evidence of statewide relevance (docs/PROTOCOL.md section 6 active-
universe logic), so it's a defensible, evidence-grounded starting set rather
than an arbitrary one -- and using the exact Vivid Seats strings as
entity_name means data/raw/county_fandom.csv's cfb rows can now be joined to
an entity_id (they couldn't be before this script ran).

This is NOT the complete Division I football universe (some FBS/FCS programs
never win a county outright and won't appear here), and it does NOT cover
any other college sport (basketball, hockey, baseball, etc. still need their
own build). See data/registries/README.md for what's still missing.

Level/conference verified 2026-09-15 against Wikipedia FBS/FCS program lists,
with two live corrections caught by direct verification: North Dakota State
moved from FCS to FBS (Mountain West) effective 2026-07-01 -- the docs/PROTOCOL.md
section 6 "FCS anchor" framing for NDSU is now stale; South Dakota State
remains FCS (Missouri Valley Football Conference).

Run from the project root (after build_entities_registry.py):
    python scripts/build_cfb_entities_registry.py
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

LEVEL_LEAGUE = {
    "FBS": "NCAA Division I FBS",
    "FCS": "NCAA Division I FCS",
    "D-II": "NCAA Division II",
}

SOURCE = (
    "Team names from data/raw/vividseats_cfb_county_raw.csv (Vivid Seats "
    "college football fan map, retrieved 2026-09-15); level/conference "
    "cross-checked against https://en.wikipedia.org/wiki/List_of_NCAA_"
    "Division_I_FBS_football_programs and .../FCS_football_programs, plus "
    "direct per-program verification for recent realignment."
)

# (raw entity_name as scraped, level, conference, home_city, home_state, notes)
PROGRAMS = [
    ("Abilene Christian Wildcats Football", "FCS", "UAC", "Abilene", "TX", ""),
    ("Air Force Academy Falcons Football", "FBS", "Mountain West", "Colorado Springs", "CO", ""),
    ("Alabama A&M Bulldogs Football", "FCS", "SWAC", "Huntsville", "AL", ""),
    ("Alabama Crimson Tide Football", "FBS", "SEC", "Tuscaloosa", "AL", ""),
    ("Angelo State Rams Football", "D-II", "Lone Star Conference", "San Angelo", "TX", ""),
    ("Appalachian State Mountaineers Football", "FBS", "Sun Belt", "Boone", "NC", ""),
    ("Arizona State Sun Devils Football", "FBS", "Big 12", "Tempe", "AZ", ""),
    ("Arizona Wildcats Football", "FBS", "Big 12", "Tucson", "AZ", ""),
    ("Arkansas Razorbacks Football", "FBS", "SEC", "Fayetteville", "AR", ""),
    ("Arkansas State Red Wolves Football", "FBS", "Sun Belt", "Jonesboro", "AR", ""),
    ("Army West Point Black Knights Football", "FBS", "American", "West Point", "NY", ""),
    ("Auburn Tigers Football", "FBS", "SEC", "Auburn", "AL", ""),
    ("BYU Cougars Football", "FBS", "Big 12", "Provo", "UT", ""),
    ("Baylor Bears Football", "FBS", "Big 12", "Waco", "TX", ""),
    ("Boise State Broncos Football", "FBS", "Pac-12", "Boise", "ID", "Rebuilt Pac-12 (post-2024 realignment)."),
    ("Boston College Eagles Football", "FBS", "ACC", "Chestnut Hill", "MA", ""),
    ("Buffalo Bulls Football", "FBS", "MAC", "Buffalo", "NY", ""),
    ("California Golden Bears Football", "FBS", "ACC", "Berkeley", "CA", ""),
    ("Central Michigan Chippewas Football", "FBS", "MAC", "Mount Pleasant", "MI", ""),
    ("Cincinnati Bearcats Football", "FBS", "Big 12", "Cincinnati", "OH", ""),
    ("Citadel Bulldogs Football", "FCS", "SoCon", "Charleston", "SC", ""),
    ("Clemson Tigers Football", "FBS", "ACC", "Clemson", "SC", ""),
    ("Coastal Carolina Chanticleers Football", "FBS", "Sun Belt", "Conway", "SC", ""),
    ("Colorado Buffaloes Football", "FBS", "Big 12", "Boulder", "CO", ""),
    ("Colorado State Rams Football", "FBS", "Pac-12", "Fort Collins", "CO", "Rebuilt Pac-12."),
    ("Dartmouth Big Green Football", "FCS", "Ivy League", "Hanover", "NH", ""),
    ("Dayton Flyers Football", "FCS", "Pioneer Football League", "Dayton", "OH", ""),
    ("Delaware Blue Hens Football", "FBS", "Conference USA", "Newark", "DE", ""),
    ("Duke Blue Devils Football", "FBS", "ACC", "Durham", "NC", ""),
    ("East Carolina Pirates Football", "FBS", "American", "Greenville", "NC", ""),
    ("East Tennessee State Buccaneers Football", "FCS", "SoCon", "Johnson City", "TN", ""),
    ("East Texas A&M Lions Football", "FCS", "Southland", "Commerce", "TX", ""),
    ("Florida Gators Football", "FBS", "SEC", "Gainesville", "FL", ""),
    ("Florida State Seminoles Football", "FBS", "ACC", "Tallahassee", "FL", ""),
    ("Fresno State Bulldogs Football", "FBS", "Pac-12", "Fresno", "CA", "Rebuilt Pac-12."),
    ("Georgia Bulldogs Football", "FBS", "SEC", "Athens", "GA", ""),
    ("Georgia Southern Eagles Football", "FBS", "Sun Belt", "Statesboro", "GA", ""),
    ("Georgia State Panthers Football", "FBS", "Sun Belt", "Atlanta", "GA", ""),
    ("Georgia Tech Yellow Jackets Football", "FBS", "ACC", "Atlanta", "GA", ""),
    ("Grambling State Tigers Football", "FCS", "SWAC", "Grambling", "LA", ""),
    ("Grand Valley State Lakers Football", "D-II", "GLIAC", "Allendale", "MI", ""),
    ("Hampton Pirates Football", "FCS", "CAA", "Hampton", "VA", ""),
    ("Hawaii Rainbow Warriors Football", "FBS", "Mountain West", "Honolulu", "HI", ""),
    ("Houston Cougars Football", "FBS", "Big 12", "Houston", "TX", ""),
    ("Idaho State Bengals Football", "FCS", "Big Sky", "Pocatello", "ID", ""),
    ("Idaho Vandals Football", "FCS", "Big Sky", "Moscow", "ID", ""),
    ("Illinois Fighting Illini Football", "FBS", "Big Ten", "Champaign", "IL", ""),
    ("Indiana Hoosiers Football", "FBS", "Big Ten", "Bloomington", "IN", ""),
    ("Indiana State Sycamores Football", "FCS", "MVFC", "Terre Haute", "IN", ""),
    ("Iowa Hawkeyes Football", "FBS", "Big Ten", "Iowa City", "IA", ""),
    ("Iowa State Cyclones Football", "FBS", "Big 12", "Ames", "IA", ""),
    ("Jackson State Tigers Football", "FCS", "SWAC", "Jackson", "MS", ""),
    ("Jacksonville State Gamecocks Football", "FBS", "Conference USA", "Jacksonville", "AL", ""),
    ("James Madison Dukes Football", "FBS", "Sun Belt", "Harrisonburg", "VA", ""),
    ("Kansas Jayhawks Football", "FBS", "Big 12", "Lawrence", "KS", ""),
    ("Kansas State Wildcats Football", "FBS", "Big 12", "Manhattan", "KS", ""),
    ("Kennesaw State Owls Football", "FBS", "Conference USA", "Kennesaw", "GA", ""),
    ("Kentucky Wildcats Football", "FBS", "SEC", "Lexington", "KY", ""),
    ("LSU Tigers Football", "FBS", "SEC", "Baton Rouge", "LA", ""),
    ("Lamar University Cardinals Football", "FCS", "Southland", "Beaumont", "TX", ""),
    ("Lenoir Rhyne Bears Football", "D-II", "South Atlantic Conference", "Hickory", "NC", ""),
    ("Liberty Flames Football", "FBS", "Conference USA", "Lynchburg", "VA", ""),
    ("Louisiana Monroe Warhawks Football", "FBS", "Sun Belt", "Monroe", "LA", ""),
    ("Louisiana Tech Bulldogs Football", "FBS", "Conference USA", "Ruston", "LA", ""),
    ("Louisville Cardinals Football", "FBS", "ACC", "Louisville", "KY", ""),
    ("Maine Black Bears Football", "FCS", "CAA", "Orono", "ME", ""),
    ("Marshall Thundering Herd Football", "FBS", "Sun Belt", "Huntington", "WV", ""),
    ("Maryland Terrapins Football", "FBS", "Big Ten", "College Park", "MD", ""),
    ("Mercer Bears Football", "FCS", "SoCon", "Macon", "GA", ""),
    ("Miami Hurricanes Football", "FBS", "ACC", "Coral Gables", "FL", ""),
    ("Michigan State Spartans Football", "FBS", "Big Ten", "East Lansing", "MI", ""),
    ("Michigan Wolverines Football", "FBS", "Big Ten", "Ann Arbor", "MI", ""),
    ("Minnesota Golden Gophers Football", "FBS", "Big Ten", "Minneapolis", "MN", ""),
    ("Mississippi State Bulldogs Football", "FBS", "SEC", "Starkville", "MS", ""),
    ("Missouri State Bears Football", "FBS", "Conference USA", "Springfield", "MO", "Moved up to FBS/CUSA in 2025."),
    ("Missouri Tigers Football", "FBS", "SEC", "Columbia", "MO", ""),
    ("Montana Grizzlies Football", "FCS", "Big Sky", "Missoula", "MT", ""),
    ("Montana State Bobcats Football", "FCS", "Big Sky", "Bozeman", "MT", ""),
    ("Navy Midshipmen Football", "FBS", "American", "Annapolis", "MD", ""),
    ("Nebraska Cornhuskers Football", "FBS", "Big Ten", "Lincoln", "NE", ""),
    ("Nevada Wolf Pack Football", "FBS", "Mountain West", "Reno", "NV", ""),
    ("New Hampshire Wildcats Football", "FCS", "CAA", "Durham", "NH", ""),
    ("New Mexico Lobos Football", "FBS", "Mountain West", "Albuquerque", "NM", ""),
    ("New Mexico State Aggies Football", "FBS", "Conference USA", "Las Cruces", "NM", ""),
    ("Norfolk State Spartans Football", "FCS", "MEAC", "Norfolk", "VA", ""),
    ("North Alabama Lions Football", "FCS", "UAC", "Florence", "AL", ""),
    ("North Carolina State Wolfpack Football", "FBS", "ACC", "Raleigh", "NC", ""),
    ("North Carolina Tar Heels Football", "FBS", "ACC", "Chapel Hill", "NC", ""),
    ("North Dakota Fighting Hawks Football", "FCS", "MVFC", "Grand Forks", "ND", ""),
    ("North Dakota State Bison Football", "FBS", "Mountain West", "Fargo", "ND",
     "Moved from FCS to FBS effective 2026-07-01, joining Mountain West for "
     "the 2026 season -- verified directly 2026-09-15; the 'FCS anchor' "
     "framing in docs/PROTOCOL.md section 6 is now stale for this program."),
    ("North Texas Mean Green Football", "FBS", "American", "Denton", "TX", ""),
    ("Northern Arizona Lumberjacks Football", "FCS", "Big Sky", "Flagstaff", "AZ", ""),
    ("Northern Colorado Bears Football", "FCS", "Big Sky", "Greeley", "CO", ""),
    ("Northern Illinois Huskies Football", "FBS", "MAC", "DeKalb", "IL", ""),
    ("Northern Iowa Panthers Football", "FCS", "MVFC", "Cedar Falls", "IA", ""),
    ("Northwestern Wildcats Football", "FBS", "Big Ten", "Evanston", "IL", ""),
    ("Notre Dame Fighting Irish Football", "FBS", "Independent", "Notre Dame", "IN", ""),
    ("Ohio Bobcats Football", "FBS", "MAC", "Athens", "OH", ""),
    ("Ohio State Buckeyes Football", "FBS", "Big Ten", "Columbus", "OH", ""),
    ("Oklahoma Sooners Football", "FBS", "SEC", "Norman", "OK", ""),
    ("Oklahoma State Cowboys Football", "FBS", "Big 12", "Stillwater", "OK", ""),
    ("Old Dominion Monarchs Football", "FBS", "Sun Belt", "Norfolk", "VA", ""),
    ("Ole Miss Rebels Football", "FBS", "SEC", "Oxford", "MS", ""),
    ("Oregon Ducks Football", "FBS", "Big Ten", "Eugene", "OR", ""),
    ("Oregon State Beavers Football", "FBS", "Pac-12", "Corvallis", "OR", "Rebuilt Pac-12."),
    ("Penn State Nittany Lions Football", "FBS", "Big Ten", "University Park", "PA", ""),
    ("Pittsburg State Gorillas Football", "D-II", "MIAA", "Pittsburg", "KS", ""),
    ("Pittsburgh Panthers Football", "FBS", "ACC", "Pittsburgh", "PA", ""),
    ("Purdue Boilermakers Football", "FBS", "Big Ten", "West Lafayette", "IN", ""),
    ("Rhode Island Rams Football", "FCS", "CAA", "Kingston", "RI", ""),
    ("Richmond Spiders Football", "FCS", "Patriot League", "Richmond", "VA", ""),
    ("Rutgers Scarlet Knights Football", "FBS", "Big Ten", "Piscataway", "NJ", ""),
    ("SMU Mustangs Football", "FBS", "ACC", "Dallas", "TX", ""),
    ("Sam Houston State Bearkats Football", "FBS", "Conference USA", "Huntsville", "TX", ""),
    ("Samford University Bulldogs Football", "FCS", "SoCon", "Homewood", "AL", ""),
    ("San Diego State Aztecs Football", "FBS", "Pac-12", "San Diego", "CA", "Rebuilt Pac-12."),
    ("San Jose State Spartans Football", "FBS", "Mountain West", "San Jose", "CA", ""),
    ("South Alabama Jaguars Football", "FBS", "Sun Belt", "Mobile", "AL", ""),
    ("South Carolina Gamecocks Football", "FBS", "SEC", "Columbia", "SC", ""),
    ("South Dakota Coyotes Football", "FCS", "MVFC", "Vermillion", "SD", ""),
    ("South Dakota State Jackrabbits Football", "FCS", "MVFC", "Brookings", "SD",
     "Confirmed still FCS/MVFC as of 2026-09-15 (verified directly; unlike "
     "NDSU, has not moved to FBS)."),
    ("South Florida Bulls Football", "FBS", "American", "Tampa", "FL", ""),
    ("Southeast Missouri State Redhawks Football", "FCS", "OVC", "Cape Girardeau", "MO", ""),
    ("Southeastern Oklahoma State Savage Storm Football", "D-II", "Great American Conference", "Durant", "OK", ""),
    ("Southern Arkansas University Muleriders Football", "D-II", "Great American Conference", "Magnolia", "AR", ""),
    ("Southern Illinois Salukis Football", "FCS", "MVFC", "Carbondale", "IL", ""),
    ("Southern Miss Golden Eagles Football", "FBS", "Sun Belt", "Hattiesburg", "MS", ""),
    ("Stanford Cardinal Football", "FBS", "ACC", "Stanford", "CA", ""),
    ("Stephen F Austin Lumberjacks Football", "FCS", "Southland", "Nacogdoches", "TX", ""),
    ("Stony Brook Seawolves Football", "FCS", "CAA", "Stony Brook", "NY", ""),
    ("Syracuse Orange Football", "FBS", "ACC", "Syracuse", "NY", ""),
    ("TCU Horned Frogs Football", "FBS", "Big 12", "Fort Worth", "TX", ""),
    ("Tarleton State Texans Football", "FCS", "UAC", "Stephenville", "TX", ""),
    ("Temple Owls Football", "FBS", "American", "Philadelphia", "PA", ""),
    ("Tennessee Vols Football", "FBS", "SEC", "Knoxville", "TN", ""),
    ("Texas A&M Aggies Football", "FBS", "SEC", "College Station", "TX", ""),
    ("Texas Longhorns Football", "FBS", "SEC", "Austin", "TX", ""),
    ("Texas State San Marcos Bobcats Football", "FBS", "Pac-12", "San Marcos", "TX", "Rebuilt Pac-12."),
    ("Texas Tech Red Raiders Football", "FBS", "Big 12", "Lubbock", "TX", ""),
    ("Toledo Rockets Football", "FBS", "MAC", "Toledo", "OH", ""),
    ("Troy Trojans Football", "FBS", "Sun Belt", "Troy", "AL", ""),
    ("Truman State Bulldogs Football", "D-II", "GLVC", "Kirksville", "MO", ""),
    ("Tulane Green Wave Football", "FBS", "American", "New Orleans", "LA", ""),
    ("Tulsa Golden Hurricane Football", "FBS", "American", "Tulsa", "OK", ""),
    ("UC Davis Aggies Football", "FCS", "Big Sky", "Davis", "CA", ""),
    ("UCF Knights Football", "FBS", "Big 12", "Orlando", "FL", ""),
    ("UCLA Bruins Football", "FBS", "Big Ten", "Los Angeles", "CA", ""),
    ("UConn Huskies Football", "FBS", "Independent", "East Hartford", "CT", ""),
    ("UMass Minutemen Football", "FBS", "Independent", "Amherst", "MA", ""),
    ("UNLV Rebels Football", "FBS", "Mountain West", "Las Vegas", "NV", ""),
    ("USC Trojans Football", "FBS", "Big Ten", "Los Angeles", "CA", ""),
    ("UTEP Miners Football", "FBS", "Conference USA", "El Paso", "TX", ""),
    ("Utah State Aggies Football", "FBS", "Pac-12", "Logan", "UT", "Rebuilt Pac-12."),
    ("Utah Utes Football", "FBS", "Big 12", "Salt Lake City", "UT", ""),
    ("Vanderbilt Commodores Football", "FBS", "SEC", "Nashville", "TN", ""),
    ("Virginia Cavaliers Football", "FBS", "ACC", "Charlottesville", "VA", ""),
    ("Virginia Tech Hokies Football", "FBS", "ACC", "Blacksburg", "VA", ""),
    ("Wake Forest Demon Deacons Football", "FBS", "ACC", "Winston-Salem", "NC", ""),
    ("Washington Huskies Football", "FBS", "Big Ten", "Seattle", "WA", ""),
    ("Washington State Cougars Football", "FBS", "Pac-12", "Pullman", "WA", "Rebuilt Pac-12."),
    ("West Texas A&M Buffaloes Football", "D-II", "Lone Star Conference", "Canyon", "TX", ""),
    ("West Virginia Mountaineers Football", "FBS", "Big 12", "Morgantown", "WV", ""),
    ("Western Carolina Catamounts Football", "FCS", "SoCon", "Cullowhee", "NC", ""),
    ("Western Kentucky Hilltoppers Football", "FBS", "Conference USA", "Bowling Green", "KY", ""),
    ("Western Michigan Broncos Football", "FBS", "MAC", "Kalamazoo", "MI", ""),
    ("William and Mary Tribe Football", "FCS", "CAA", "Williamsburg", "VA", ""),
    ("Wisconsin Badgers Football", "FBS", "Big Ten", "Madison", "WI", ""),
    ("Wyoming Cowboys Football", "FBS", "Mountain West", "Laramie", "WY", ""),
]


def slugify(entity_name):
    name = entity_name.replace(" Football", "")
    name = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").lower()
    return f"cfb_{name}"


def main():
    with open(ENTITIES_PATH, newline="", encoding="utf-8") as f:
        existing = list(csv.DictReader(f))
    existing_ids = {r["entity_id"] for r in existing}
    existing_names = {r["entity_name"] for r in existing}

    new_rows = []
    seen_ids = set()
    for name, level, conference, city, state, notes in PROGRAMS:
        if name in existing_names:
            continue
        entity_id = slugify(name)
        if entity_id in existing_ids or entity_id in seen_ids:
            raise ValueError(f"duplicate entity_id generated: {entity_id} for {name}")
        seen_ids.add(entity_id)
        new_rows.append({
            "entity_id": entity_id,
            "organization_id": entity_id,
            "entity_name": name,
            "sport": "American football",
            "sex_category": "men",
            "level": level,
            "professional_college": "college",
            "league": LEVEL_LEAGUE[level],
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

    all_rows = existing + new_rows
    with open(ENTITIES_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Appended {len(new_rows)} college football entities (total registry: {len(all_rows)})")
    by_level = {}
    for _, level, *_ in PROGRAMS:
        by_level[level] = by_level.get(level, 0) + 1
    for level, n in sorted(by_level.items()):
        print(f"  {level}: {n}")
    print(
        "NOTE: this is the set of programs that actually won a county "
        "plurality somewhere in the Vivid Seats scrape -- not the full "
        "FBS+FCS+D-II universe. No other college sport is in the registry "
        "yet."
    )


if __name__ == "__main__":
    main()
