"""Phase 4B step 4/5: consolidate the raw Vivid Seats county/state ticket-
origin plurality scrapes into data/raw/county_fandom.csv, joined to
entity_id from the professional-core registry.

Inputs (already extracted from each blog post's embedded Flourish dataset --
see data/raw/vividseats_*_raw.csv and docs/PROTOCOL.md section 10 for the source
URLs):
    vividseats_nfl_county_raw.csv   (choropleth schema: county+state label)
    vividseats_mlb_county_raw.csv   (regions schema: county FIPS)
    vividseats_nba_county_raw.csv   (regions schema: county FIPS)
    vividseats_mls_county_raw.csv   (regions schema: county FIPS)
    vividseats_nhl_county_raw.csv   (choropleth schema: county+state label;
                                      docs/PROTOCOL.md section 10 flags this as the
                                      OLDER NHL map -- it still lists Arizona
                                      Coyotes, not Utah Mammoth)
    vividseats_wnba_state_raw.csv   (state-level, not county-level)
    vividseats_cfb_county_raw.csv   (college football -- joined via the
                                      registry built by
                                      build_cfb_entities_registry.py, which
                                      covers only the 168 programs that
                                      actually won a county in this scrape,
                                      not the full FBS+FCS+D-II universe)

This is C_si raw material only (population-weighted plurality-county
fandom), never a substitute for A itself (docs/PROTOCOL.md section 8).

Run from the project root (after build_entities_registry.py and
build_county_population.py):
    python scripts/build_county_fandom.py
"""
import csv
import datetime
import pathlib

ROOT = pathlib.Path(__file__).parent
if ROOT.name == "scripts":
    ROOT = ROOT.parent
RAW_DIR = ROOT / "data" / "raw"
ENTITIES_PATH = ROOT / "data" / "registries" / "entities.csv"
COUNTY_POP_PATH = RAW_DIR / "county_population.csv"
OUT_PATH = RAW_DIR / "county_fandom.csv"
RETRIEVED_AT = "2026-09-15"

# team_name string as scraped -> entity_id, where it differs from
# entities.csv entity_name. Exact matches are resolved automatically.
ALIASES = {
    "Atlanta United": "mls_atlutd",
    "Chicago Fire": "mls_chifire",
    "DC United": "mls_dcunited",
    "Houston Dynamo": "mls_houston",
    "Los Angeles Galaxy": "mls_lagalaxy",
}

# Team names that resolve to no CURRENT entity_id -- historical/defunct
# lineage only (docs/PROTOCOL.md section 5: relocated/defunct teams get zero
# current attention; historical lineage is archived, not carried forward).
HISTORICAL_ONLY = {
    "Arizona Coyotes": "Predecessor of nhl_mammoth (relocated to Salt Lake "
                        "City in 2024). This row is from the OLDER Vivid "
                        "Seats NHL map (docs/PROTOCOL.md section 10) and predates "
                        "the relocation -- left unmatched to any current "
                        "entity_id per the relocated/defunct-team rule.",
}

SOURCES = {
    "nfl": "https://www.vividseats.com/blog/most-popular-nfl-teams-by-state-county",
    "mlb": "https://www.vividseats.com/blog/most-popular-mlb-teams-by-county",
    "nba": "https://www.vividseats.com/blog/most-popular-nba-teams-by-state-county",
    "mls": "https://www.vividseats.com/blog/most-popular-mls-teams-by-state-county",
    "nhl": "https://www.vividseats.com/blog/most-popular-nhl-teams-by-state-county",
    "wnba": "https://www.vividseats.com/blog/most-popular-wnba-teams-by-state",
    "cfb": "https://www.vividseats.com/blog/most-popular-ncaa-football-teams-by-state-county",
}


def load_entity_lookup():
    with open(ENTITIES_PATH, newline="", encoding="utf-8") as f:
        entities = list(csv.DictReader(f))
    by_name = {e["entity_name"]: e["entity_id"] for e in entities}
    return by_name


def load_county_fips_lookup():
    """(county_full_or_short_name, state_name) -> county_fips, for the
    choropleth-schema files that only give a 'County, State' text label."""
    lookup_by_full = {}
    with open(COUNTY_POP_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row["county_name"], row["state_name"])
            lookup_by_full[key] = row["county_fips"]
    return lookup_by_full


def resolve_entity(team_name, by_name, unmatched_log):
    if not team_name:
        return "", ""
    if team_name in by_name:
        return by_name[team_name], ""
    if team_name in ALIASES:
        return ALIASES[team_name], ""
    if team_name in HISTORICAL_ONLY:
        return "", HISTORICAL_ONLY[team_name]
    unmatched_log.add(team_name)
    return "", "UNMATCHED -- needs alias or registry entry"


def guess_county_fips(label, state_name, fips_lookup):
    # label is like "Abbeville, South Carolina" -- strip the state suffix,
    # then try common county-equivalent suffixes against
    # county_population.csv. Known remaining gap: Connecticut, where Vivid
    # Seats' map still uses the legacy 8 counties retired by the Census
    # Bureau in 2022 in favor of 9 planning regions -- joining those needs
    # an explicit crosswalk this script doesn't have yet.
    short = label.split(",")[0].strip()
    for candidate in (f"{short} County", short, f"{short} Parish",
                       f"{short} Borough", f"{short} Census Area",
                       f"{short} Municipality", f"{short} city",
                       f"{short} City and Borough"):
        key = (candidate, state_name)
        if key in fips_lookup:
            return fips_lookup[key]
    return ""


def main():
    by_name = load_entity_lookup()
    fips_lookup = load_county_fips_lookup()
    unmatched = set()
    out_rows = []

    def add(county_fips, county_name, state_name, sport_key, team_name):
        entity_id, note = resolve_entity(team_name, by_name, unmatched)
        out_rows.append({
            "county_fips": county_fips,
            "county_name": county_name,
            "state_name": state_name,
            "sport": sport_key,
            "raw_team_name": team_name,
            "entity_id": entity_id,
            "source": SOURCES[sport_key],
            "retrieved_at": RETRIEVED_AT,
            "notes": note,
        })

    # --- regions-schema files: carry county_fips, but as extracted from the
    # Flourish JSON it's a bare int (e.g. "1061" for Alabama's 01061) --
    # left unpadded, this silently fails the county_population.csv join for
    # every state with a leading-zero FIPS code (01-09: AL, AK, AZ, AR, CA,
    # CO, CT, DE). Zero-pad to the canonical 5-digit code here.
    for sport_key, fname in [("mlb", "vividseats_mlb_county_raw.csv"),
                              ("nba", "vividseats_nba_county_raw.csv"),
                              ("mls", "vividseats_mls_county_raw.csv"),
                              ("cfb", "vividseats_cfb_county_raw.csv")]:
        with open(RAW_DIR / fname, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                add(row["county_fips"].zfill(5), row["county_full_name"],
                    row["state_name"], sport_key, row["team_name"])

    # --- choropleth-schema files: "County, State" label, need fips lookup ---
    for sport_key, fname in [("nfl", "vividseats_nfl_county_raw.csv"),
                              ("nhl", "vividseats_nhl_county_raw.csv")]:
        with open(RAW_DIR / fname, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                label = row["county_state_label"]
                state_name = row["state_name"]
                if not state_name:
                    continue  # a few malformed labels with no state (e.g. "Eastern,")
                fips = guess_county_fips(label, state_name, fips_lookup)
                entity_id, note = resolve_entity(row["team_name"], by_name, unmatched)
                if not fips:
                    note = (note + "; " if note else "") + (
                        "county_fips lookup failed against "
                        "county_population.csv -- likely a Connecticut "
                        "legacy-county/planning-region mismatch or an "
                        "unhandled county-equivalent suffix."
                    )
                out_rows.append({
                    "county_fips": fips,
                    "county_name": label,
                    "state_name": state_name,
                    "sport": sport_key,
                    "raw_team_name": row["team_name"],
                    "entity_id": entity_id,
                    "source": SOURCES[sport_key],
                    "retrieved_at": RETRIEVED_AT,
                    "notes": note,
                })

    # --- WNBA: state-level, no county_fips ---
    with open(RAW_DIR / "vividseats_wnba_state_raw.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            add("", "", row["state_name"], "wnba", row["team_name"])

    fieldnames = ["county_fips", "county_name", "state_name", "sport",
                  "raw_team_name", "entity_id", "source", "retrieved_at",
                  "notes"]
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Wrote {len(out_rows)} rows to {OUT_PATH}")
    n_no_fips = sum(1 for r in out_rows if r["sport"] in ("nfl", "nhl") and not r["county_fips"])
    print(f"NFL/NHL rows where county_fips lookup failed: {n_no_fips}")
    if unmatched:
        print(f"Unmatched team names ({len(unmatched)}), needs alias or registry fix:")
        for t in sorted(unmatched):
            print(f"  - {t}")


if __name__ == "__main__":
    main()
