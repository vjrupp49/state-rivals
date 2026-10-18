"""Phase 4B step 1 (registry side): build data/registries/entities.csv.

Populates the "guaranteed professional core" (docs/PROTOCOL.md section 5): NFL(32) +
MLB(30) + NBA(30) + NHL(32) + MLS(30) + WNBA(15) + NWSL(16) + PWHL(12) = 197
entities. College Division I programs, lower-division/NAIA, and
team-by-team pro leagues (UFL, USL, pro volleyball, etc.) are a separate,
much larger build tracked in data/registries/README.md and are NOT included
here yet -- do not treat this file as the complete active-entity universe.

Sources verified 2026-09-15 (retrieved_at below):
- NFL/MLB/NBA: stable league membership, no relocations/expansions pending;
  https://www.nfl.com/teams/ , https://www.mlb.com/team , https://www.nba.com/teams
- NHL, MLS, WNBA, NWSL, PWHL: verified via Wikipedia league pages same date
  (post-2025/2026 expansion and relocation changes, e.g. Utah Mammoth,
  San Diego FC, Toronto Tempo/Portland Fire, Denver Summit/Boston Legacy,
  PWHL Hamilton/Vancouver Goldeneyes/Detroit/Las Vegas/San Jose).

Run from the project root:
    python scripts/build_entities_registry.py
"""
import csv
import datetime
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
OUT_PATH = ROOT / "data" / "registries" / "entities.csv"
RETRIEVED_AT = "2026-09-15"

FIELDNAMES = [
    "entity_id", "organization_id", "entity_name", "sport", "sex_category",
    "level", "professional_college", "league", "conference", "division",
    "home_city", "home_state", "stadium_or_campus", "active_from",
    "active_to", "current_status", "source", "notes",
]

# (entity_id, name, city, state, conference, division)
NFL = [
    ("nfl_bills", "Buffalo Bills", "Buffalo", "NY", "AFC", "East"),
    ("nfl_dolphins", "Miami Dolphins", "Miami Gardens", "FL", "AFC", "East"),
    ("nfl_patriots", "New England Patriots", "Foxborough", "MA", "AFC", "East"),
    ("nfl_jets", "New York Jets", "East Rutherford", "NJ", "AFC", "East"),
    ("nfl_ravens", "Baltimore Ravens", "Baltimore", "MD", "AFC", "North"),
    ("nfl_bengals", "Cincinnati Bengals", "Cincinnati", "OH", "AFC", "North"),
    ("nfl_browns", "Cleveland Browns", "Cleveland", "OH", "AFC", "North"),
    ("nfl_steelers", "Pittsburgh Steelers", "Pittsburgh", "PA", "AFC", "North"),
    ("nfl_texans", "Houston Texans", "Houston", "TX", "AFC", "South"),
    ("nfl_colts", "Indianapolis Colts", "Indianapolis", "IN", "AFC", "South"),
    ("nfl_jaguars", "Jacksonville Jaguars", "Jacksonville", "FL", "AFC", "South"),
    ("nfl_titans", "Tennessee Titans", "Nashville", "TN", "AFC", "South"),
    ("nfl_broncos", "Denver Broncos", "Denver", "CO", "AFC", "West"),
    ("nfl_chiefs", "Kansas City Chiefs", "Kansas City", "MO", "AFC", "West"),
    ("nfl_raiders", "Las Vegas Raiders", "Las Vegas", "NV", "AFC", "West"),
    ("nfl_chargers", "Los Angeles Chargers", "Inglewood", "CA", "AFC", "West"),
    ("nfl_cowboys", "Dallas Cowboys", "Arlington", "TX", "NFC", "East"),
    ("nfl_giants", "New York Giants", "East Rutherford", "NJ", "NFC", "East"),
    ("nfl_eagles", "Philadelphia Eagles", "Philadelphia", "PA", "NFC", "East"),
    ("nfl_commanders", "Washington Commanders", "Landover", "MD", "NFC", "East"),
    ("nfl_bears", "Chicago Bears", "Chicago", "IL", "NFC", "North"),
    ("nfl_lions", "Detroit Lions", "Detroit", "MI", "NFC", "North"),
    ("nfl_packers", "Green Bay Packers", "Green Bay", "WI", "NFC", "North"),
    ("nfl_vikings", "Minnesota Vikings", "Minneapolis", "MN", "NFC", "North"),
    ("nfl_falcons", "Atlanta Falcons", "Atlanta", "GA", "NFC", "South"),
    ("nfl_panthers", "Carolina Panthers", "Charlotte", "NC", "NFC", "South"),
    ("nfl_saints", "New Orleans Saints", "New Orleans", "LA", "NFC", "South"),
    ("nfl_buccaneers", "Tampa Bay Buccaneers", "Tampa", "FL", "NFC", "South"),
    ("nfl_cardinals", "Arizona Cardinals", "Glendale", "AZ", "NFC", "West"),
    ("nfl_rams", "Los Angeles Rams", "Inglewood", "CA", "NFC", "West"),
    ("nfl_49ers", "San Francisco 49ers", "Santa Clara", "CA", "NFC", "West"),
    ("nfl_seahawks", "Seattle Seahawks", "Seattle", "WA", "NFC", "West"),
]

MLB = [
    ("mlb_orioles", "Baltimore Orioles", "Baltimore", "MD", "AL", "East"),
    ("mlb_redsox", "Boston Red Sox", "Boston", "MA", "AL", "East"),
    ("mlb_yankees", "New York Yankees", "New York", "NY", "AL", "East"),
    ("mlb_rays", "Tampa Bay Rays", "St. Petersburg", "FL", "AL", "East"),
    ("mlb_bluejays", "Toronto Blue Jays", "Toronto", "ON", "AL", "East"),
    ("mlb_whitesox", "Chicago White Sox", "Chicago", "IL", "AL", "Central"),
    ("mlb_guardians", "Cleveland Guardians", "Cleveland", "OH", "AL", "Central"),
    ("mlb_tigers", "Detroit Tigers", "Detroit", "MI", "AL", "Central"),
    ("mlb_royals", "Kansas City Royals", "Kansas City", "MO", "AL", "Central"),
    ("mlb_twins", "Minnesota Twins", "Minneapolis", "MN", "AL", "Central"),
    ("mlb_astros", "Houston Astros", "Houston", "TX", "AL", "West"),
    ("mlb_angels", "Los Angeles Angels", "Anaheim", "CA", "AL", "West"),
    ("mlb_athletics", "Athletics", "West Sacramento", "CA", "AL", "West"),
    ("mlb_mariners", "Seattle Mariners", "Seattle", "WA", "AL", "West"),
    ("mlb_rangers", "Texas Rangers", "Arlington", "TX", "AL", "West"),
    ("mlb_braves", "Atlanta Braves", "Cumberland", "GA", "NL", "East"),
    ("mlb_marlins", "Miami Marlins", "Miami", "FL", "NL", "East"),
    ("mlb_mets", "New York Mets", "New York", "NY", "NL", "East"),
    ("mlb_phillies", "Philadelphia Phillies", "Philadelphia", "PA", "NL", "East"),
    ("mlb_nationals", "Washington Nationals", "Washington", "DC", "NL", "East"),
    ("mlb_cubs", "Chicago Cubs", "Chicago", "IL", "NL", "Central"),
    ("mlb_reds", "Cincinnati Reds", "Cincinnati", "OH", "NL", "Central"),
    ("mlb_brewers", "Milwaukee Brewers", "Milwaukee", "WI", "NL", "Central"),
    ("mlb_pirates", "Pittsburgh Pirates", "Pittsburgh", "PA", "NL", "Central"),
    ("mlb_cardinals", "St. Louis Cardinals", "St. Louis", "MO", "NL", "Central"),
    ("mlb_diamondbacks", "Arizona Diamondbacks", "Phoenix", "AZ", "NL", "West"),
    ("mlb_rockies", "Colorado Rockies", "Denver", "CO", "NL", "West"),
    ("mlb_dodgers", "Los Angeles Dodgers", "Los Angeles", "CA", "NL", "West"),
    ("mlb_padres", "San Diego Padres", "San Diego", "CA", "NL", "West"),
    ("mlb_giants", "San Francisco Giants", "San Francisco", "CA", "NL", "West"),
]

NBA = [
    ("nba_celtics", "Boston Celtics", "Boston", "MA", "Eastern", "Atlantic"),
    ("nba_nets", "Brooklyn Nets", "Brooklyn", "NY", "Eastern", "Atlantic"),
    ("nba_knicks", "New York Knicks", "New York", "NY", "Eastern", "Atlantic"),
    ("nba_76ers", "Philadelphia 76ers", "Philadelphia", "PA", "Eastern", "Atlantic"),
    ("nba_raptors", "Toronto Raptors", "Toronto", "ON", "Eastern", "Atlantic"),
    ("nba_bulls", "Chicago Bulls", "Chicago", "IL", "Eastern", "Central"),
    ("nba_cavaliers", "Cleveland Cavaliers", "Cleveland", "OH", "Eastern", "Central"),
    ("nba_pistons", "Detroit Pistons", "Detroit", "MI", "Eastern", "Central"),
    ("nba_pacers", "Indiana Pacers", "Indianapolis", "IN", "Eastern", "Central"),
    ("nba_bucks", "Milwaukee Bucks", "Milwaukee", "WI", "Eastern", "Central"),
    ("nba_hawks", "Atlanta Hawks", "Atlanta", "GA", "Eastern", "Southeast"),
    ("nba_hornets", "Charlotte Hornets", "Charlotte", "NC", "Eastern", "Southeast"),
    ("nba_heat", "Miami Heat", "Miami", "FL", "Eastern", "Southeast"),
    ("nba_magic", "Orlando Magic", "Orlando", "FL", "Eastern", "Southeast"),
    ("nba_wizards", "Washington Wizards", "Washington", "DC", "Eastern", "Southeast"),
    ("nba_nuggets", "Denver Nuggets", "Denver", "CO", "Western", "Northwest"),
    ("nba_timberwolves", "Minnesota Timberwolves", "Minneapolis", "MN", "Western", "Northwest"),
    ("nba_thunder", "Oklahoma City Thunder", "Oklahoma City", "OK", "Western", "Northwest"),
    ("nba_trailblazers", "Portland Trail Blazers", "Portland", "OR", "Western", "Northwest"),
    ("nba_jazz", "Utah Jazz", "Salt Lake City", "UT", "Western", "Northwest"),
    ("nba_warriors", "Golden State Warriors", "San Francisco", "CA", "Western", "Pacific"),
    ("nba_clippers", "LA Clippers", "Inglewood", "CA", "Western", "Pacific"),
    ("nba_lakers", "Los Angeles Lakers", "Los Angeles", "CA", "Western", "Pacific"),
    ("nba_suns", "Phoenix Suns", "Phoenix", "AZ", "Western", "Pacific"),
    ("nba_kings", "Sacramento Kings", "Sacramento", "CA", "Western", "Pacific"),
    ("nba_mavericks", "Dallas Mavericks", "Dallas", "TX", "Western", "Southwest"),
    ("nba_rockets", "Houston Rockets", "Houston", "TX", "Western", "Southwest"),
    ("nba_grizzlies", "Memphis Grizzlies", "Memphis", "TN", "Western", "Southwest"),
    ("nba_pelicans", "New Orleans Pelicans", "New Orleans", "LA", "Western", "Southwest"),
    ("nba_spurs", "San Antonio Spurs", "San Antonio", "TX", "Western", "Southwest"),
]

NHL = [
    ("nhl_bruins", "Boston Bruins", "Boston", "MA", "Eastern", "Atlantic"),
    ("nhl_sabres", "Buffalo Sabres", "Buffalo", "NY", "Eastern", "Atlantic"),
    ("nhl_redwings", "Detroit Red Wings", "Detroit", "MI", "Eastern", "Atlantic"),
    ("nhl_panthers", "Florida Panthers", "Sunrise", "FL", "Eastern", "Atlantic"),
    ("nhl_canadiens", "Montreal Canadiens", "Montreal", "QC", "Eastern", "Atlantic"),
    ("nhl_senators", "Ottawa Senators", "Ottawa", "ON", "Eastern", "Atlantic"),
    ("nhl_lightning", "Tampa Bay Lightning", "Tampa", "FL", "Eastern", "Atlantic"),
    ("nhl_mapleleafs", "Toronto Maple Leafs", "Toronto", "ON", "Eastern", "Atlantic"),
    ("nhl_hurricanes", "Carolina Hurricanes", "Raleigh", "NC", "Eastern", "Metropolitan"),
    ("nhl_bluejackets", "Columbus Blue Jackets", "Columbus", "OH", "Eastern", "Metropolitan"),
    ("nhl_devils", "New Jersey Devils", "Newark", "NJ", "Eastern", "Metropolitan"),
    ("nhl_islanders", "New York Islanders", "Elmont", "NY", "Eastern", "Metropolitan"),
    ("nhl_rangers", "New York Rangers", "New York", "NY", "Eastern", "Metropolitan"),
    ("nhl_flyers", "Philadelphia Flyers", "Philadelphia", "PA", "Eastern", "Metropolitan"),
    ("nhl_penguins", "Pittsburgh Penguins", "Pittsburgh", "PA", "Eastern", "Metropolitan"),
    ("nhl_capitals", "Washington Capitals", "Washington", "DC", "Eastern", "Metropolitan"),
    ("nhl_blackhawks", "Chicago Blackhawks", "Chicago", "IL", "Western", "Central"),
    ("nhl_avalanche", "Colorado Avalanche", "Denver", "CO", "Western", "Central"),
    ("nhl_stars", "Dallas Stars", "Dallas", "TX", "Western", "Central"),
    ("nhl_wild", "Minnesota Wild", "Saint Paul", "MN", "Western", "Central"),
    ("nhl_predators", "Nashville Predators", "Nashville", "TN", "Western", "Central"),
    ("nhl_blues", "St. Louis Blues", "St. Louis", "MO", "Western", "Central"),
    ("nhl_mammoth", "Utah Mammoth", "Salt Lake City", "UT", "Western", "Central"),
    ("nhl_jets", "Winnipeg Jets", "Winnipeg", "MB", "Western", "Central"),
    ("nhl_ducks", "Anaheim Ducks", "Anaheim", "CA", "Western", "Pacific"),
    ("nhl_flames", "Calgary Flames", "Calgary", "AB", "Western", "Pacific"),
    ("nhl_oilers", "Edmonton Oilers", "Edmonton", "AB", "Western", "Pacific"),
    ("nhl_kings", "Los Angeles Kings", "Los Angeles", "CA", "Western", "Pacific"),
    ("nhl_sharks", "San Jose Sharks", "San Jose", "CA", "Western", "Pacific"),
    ("nhl_kraken", "Seattle Kraken", "Seattle", "WA", "Western", "Pacific"),
    ("nhl_canucks", "Vancouver Canucks", "Vancouver", "BC", "Western", "Pacific"),
    ("nhl_goldenknights", "Vegas Golden Knights", "Las Vegas", "NV", "Western", "Pacific"),
]

MLS = [
    ("mls_atlutd", "Atlanta United FC", "Atlanta", "GA", "Eastern", ""),
    ("mls_charlotte", "Charlotte FC", "Charlotte", "NC", "Eastern", ""),
    ("mls_chifire", "Chicago Fire FC", "Chicago", "IL", "Eastern", ""),
    ("mls_cincinnati", "FC Cincinnati", "Cincinnati", "OH", "Eastern", ""),
    ("mls_columbus", "Columbus Crew", "Columbus", "OH", "Eastern", ""),
    ("mls_dcunited", "D.C. United", "Washington", "DC", "Eastern", ""),
    ("mls_miami", "Inter Miami CF", "Fort Lauderdale", "FL", "Eastern", ""),
    ("mls_montreal", "CF Montreal", "Montreal", "QC", "Eastern", ""),
    ("mls_nashville", "Nashville SC", "Nashville", "TN", "Eastern", ""),
    ("mls_newengland", "New England Revolution", "Foxborough", "MA", "Eastern", ""),
    ("mls_nycfc", "New York City FC", "Bronx", "NY", "Eastern", ""),
    ("mls_nyrb", "New York Red Bulls", "Harrison", "NJ", "Eastern", ""),
    ("mls_orlando", "Orlando City SC", "Orlando", "FL", "Eastern", ""),
    ("mls_philly", "Philadelphia Union", "Chester", "PA", "Eastern", ""),
    ("mls_toronto", "Toronto FC", "Toronto", "ON", "Eastern", ""),
    ("mls_austin", "Austin FC", "Austin", "TX", "Western", ""),
    ("mls_colorado", "Colorado Rapids", "Commerce City", "CO", "Western", ""),
    ("mls_dallas", "FC Dallas", "Frisco", "TX", "Western", ""),
    ("mls_houston", "Houston Dynamo FC", "Houston", "TX", "Western", ""),
    ("mls_lagalaxy", "LA Galaxy", "Carson", "CA", "Western", ""),
    ("mls_lafc", "Los Angeles FC", "Los Angeles", "CA", "Western", ""),
    ("mls_minnesota", "Minnesota United FC", "Saint Paul", "MN", "Western", ""),
    ("mls_portland", "Portland Timbers", "Portland", "OR", "Western", ""),
    ("mls_rsl", "Real Salt Lake", "Sandy", "UT", "Western", ""),
    ("mls_sandiego", "San Diego FC", "San Diego", "CA", "Western", ""),
    ("mls_sanjose", "San Jose Earthquakes", "San Jose", "CA", "Western", ""),
    ("mls_seattle", "Seattle Sounders FC", "Seattle", "WA", "Western", ""),
    ("mls_sportingkc", "Sporting Kansas City", "Kansas City", "KS", "Western", ""),
    ("mls_stlouis", "St. Louis City SC", "St. Louis", "MO", "Western", ""),
    ("mls_vancouver", "Vancouver Whitecaps FC", "Vancouver", "BC", "Western", ""),
]

WNBA = [
    ("wnba_dream", "Atlanta Dream", "Atlanta", "GA", "", ""),
    ("wnba_sky", "Chicago Sky", "Chicago", "IL", "", ""),
    ("wnba_sun", "Connecticut Sun", "Uncasville", "CT", "", ""),
    ("wnba_wings", "Dallas Wings", "Arlington", "TX", "", ""),
    ("wnba_valkyries", "Golden State Valkyries", "San Francisco", "CA", "", ""),
    ("wnba_fever", "Indiana Fever", "Indianapolis", "IN", "", ""),
    ("wnba_aces", "Las Vegas Aces", "Las Vegas", "NV", "", ""),
    ("wnba_sparks", "Los Angeles Sparks", "Los Angeles", "CA", "", ""),
    ("wnba_lynx", "Minnesota Lynx", "Minneapolis", "MN", "", ""),
    ("wnba_liberty", "New York Liberty", "Brooklyn", "NY", "", ""),
    ("wnba_mercury", "Phoenix Mercury", "Phoenix", "AZ", "", ""),
    ("wnba_fire", "Portland Fire", "Portland", "OR", "", "2026 expansion team"),
    ("wnba_storm", "Seattle Storm", "Seattle", "WA", "", ""),
    ("wnba_tempo", "Toronto Tempo", "Toronto", "ON", "", "2026 expansion team; Canadian market, non-contestant geography"),
    ("wnba_mystics", "Washington Mystics", "Washington", "DC", "", ""),
]

NWSL = [
    ("nwsl_angelcity", "Angel City FC", "Los Angeles", "CA", "", ""),
    ("nwsl_bayfc", "Bay FC", "San Jose", "CA", "", ""),
    ("nwsl_bostonlegacy", "Boston Legacy FC", "Foxborough", "MA", "", "2026 expansion team"),
    ("nwsl_chicagostars", "Chicago Stars FC", "Evanston", "IL", "", ""),
    ("nwsl_denversummit", "Denver Summit FC", "Centennial", "CO", "", "2026 expansion team"),
    ("nwsl_gotham", "NJ/NY Gotham FC", "Harrison", "NJ", "", ""),
    ("nwsl_houstondash", "Houston Dash", "Houston", "TX", "", ""),
    ("nwsl_kccurrent", "Kansas City Current", "Kansas City", "MO", "", ""),
    ("nwsl_nccourage", "North Carolina Courage", "Cary", "NC", "", ""),
    ("nwsl_orlandopride", "Orlando Pride", "Orlando", "FL", "", ""),
    ("nwsl_portlandthorns", "Portland Thorns FC", "Portland", "OR", "", ""),
    ("nwsl_racinglouisville", "Racing Louisville FC", "Louisville", "KY", "", ""),
    ("nwsl_sandiegowave", "San Diego Wave FC", "San Diego", "CA", "", ""),
    ("nwsl_seattlereign", "Seattle Reign FC", "Seattle", "WA", "", ""),
    ("nwsl_utahroyals", "Utah Royals", "Sandy", "UT", "", ""),
    ("nwsl_washspirit", "Washington Spirit", "Washington", "DC", "", ""),
]

PWHL = [
    ("pwhl_montreal", "Montreal Victoire", "Laval", "QC", "", "Original six (2024)"),
    ("pwhl_ottawa", "Ottawa Charge", "Kanata", "ON", "", "Original six (2024)"),
    ("pwhl_toronto", "Toronto Sceptres", "Toronto", "ON", "", "Original six (2024)"),
    ("pwhl_boston", "Boston Fleet", "Boston", "MA", "", "Original six (2024)"),
    ("pwhl_minnesota", "Minnesota Frost", "Saint Paul", "MN", "", "Original six (2024)"),
    ("pwhl_newyork", "New York Sirens", "Newark", "NJ", "", "Original six (2024)"),
    ("pwhl_seattle", "Seattle Torrent", "Seattle", "WA", "", "2025 expansion"),
    ("pwhl_vancouver", "Vancouver Goldeneyes", "Vancouver", "BC", "", "2025 expansion"),
    ("pwhl_hamilton", "PWHL Hamilton", "Hamilton", "ON", "", "2026 expansion; team name not yet finalized in source"),
    ("pwhl_detroit", "PWHL Detroit", "Detroit", "MI", "", "2026 expansion; team name not yet finalized in source"),
    ("pwhl_lasvegas", "PWHL Las Vegas", "Paradise", "NV", "", "2026 expansion; team name not yet finalized in source"),
    ("pwhl_sanjose", "PWHL San Jose", "San Jose", "CA", "", "2026 expansion; team name not yet finalized in source"),
]

LEAGUE_META = {
    "NFL": dict(sport="American football", sex_category="men", league="NFL",
                source="https://www.nfl.com/teams/", rows=NFL),
    "MLB": dict(sport="Baseball", sex_category="men", league="MLB",
                source="https://www.mlb.com/team", rows=MLB),
    "NBA": dict(sport="Basketball", sex_category="men", league="NBA",
                source="https://www.nba.com/teams", rows=NBA),
    "NHL": dict(sport="Ice hockey", sex_category="men", league="NHL",
                source="https://en.wikipedia.org/wiki/National_Hockey_League", rows=NHL),
    "MLS": dict(sport="Soccer", sex_category="men", league="MLS",
                source="https://en.wikipedia.org/wiki/Major_League_Soccer", rows=MLS),
    "WNBA": dict(sport="Basketball", sex_category="women", league="WNBA",
                 source="https://en.wikipedia.org/wiki/Women%27s_National_Basketball_Association", rows=WNBA),
    "NWSL": dict(sport="Soccer", sex_category="women", league="NWSL",
                 source="https://en.wikipedia.org/wiki/National_Women%27s_Soccer_League", rows=NWSL),
    "PWHL": dict(sport="Ice hockey", sex_category="women", league="PWHL",
                 source="https://en.wikipedia.org/wiki/Professional_Women%27s_Hockey_League", rows=PWHL),
}

LINEAGE_NOTES = {
    "nhl_mammoth": (
        "Franchise relocated from Arizona (Coyotes) to Salt Lake City in "
        "2024; played one season as 'Utah Hockey Club' before adopting "
        "'Utah Mammoth' for 2025-26. Historical Arizona-era attention is "
        "not carried forward as current per docs/PROTOCOL.md section 5 "
        "(relocated/defunct team rule)."
    ),
    "mlb_athletics": (
        "Relocated from Oakland to Sacramento (Sutter Health Park, West "
        "Sacramento) starting the 2025 season, en route to a planned Las "
        "Vegas market. Current-market era only; Oakland-era attention is "
        "historical, not current."
    ),
}


def build_rows():
    out = []
    for league_name, meta in LEAGUE_META.items():
        for entity_id, name, city, state, conf, div in meta["rows"]:
            out.append({
                "entity_id": entity_id,
                "organization_id": entity_id,
                "entity_name": name,
                "sport": meta["sport"],
                "sex_category": meta["sex_category"],
                "level": "professional",
                "professional_college": "professional",
                "league": meta["league"],
                "conference": conf,
                "division": div,
                "home_city": city,
                "home_state": state,
                "stadium_or_campus": "",
                "active_from": "",
                "active_to": "",
                "current_status": "active",
                "source": meta["source"],
                "notes": LINEAGE_NOTES.get(entity_id, ""),
            })
    return out


def main():
    rows = build_rows()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} pro-core entity rows to {OUT_PATH}")
    for league_name, meta in LEAGUE_META.items():
        print(f"  {league_name}: {len(meta['rows'])}")
    print(
        "NOTE: this covers the 197-entity guaranteed professional core only. "
        "Division I college programs, lower-division/NAIA, and team-by-team "
        "leagues (UFL, USL, pro volleyball, etc.) are NOT yet in this file."
    )


if __name__ == "__main__":
    main()
