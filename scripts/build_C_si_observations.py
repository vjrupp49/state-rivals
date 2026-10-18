"""Phase 4B step 5: population-weight county plurality territories into
C_si (docs/PROTOCOL.md section 8):

    C_si = [sum of population in counties where i is the plurality team] /
           population of state s

This is population living in plurality counties, NOT true fan share --
docs/PROTOCOL.md is explicit that this is one raw ingredient into P_si|k, never a
direct stand-in for A. Results are written as rows in
data/observations/observations.csv (metric = 'county_plurality_pop_share'),
each traceable back to the Vivid Seats scrape + Census population join.

Requires build_county_population.py, build_states_registry.py, and
build_county_fandom.py to have already been run.

Run from the project root:
    python scripts/build_C_si_observations.py
"""
import csv
import pathlib
from collections import defaultdict

ROOT = pathlib.Path(__file__).parent.parent
RAW_DIR = ROOT / "data" / "raw"
OBS_PATH = ROOT / "data" / "observations" / "observations.csv"
RETRIEVED_AT = "2026-09-15"

SPORT_QUALITY_NOTE = {
    "nfl": "",
    "mlb": "",
    "nba": "",
    "mls": "",
    "nhl": (
        "docs/PROTOCOL.md section 10 flags this Vivid Seats NHL map as OLDER than "
        "the others (predates the Arizona-to-Utah relocation and current "
        "team-name era); treat as Moderate/Low confidence pending a "
        "current-map re-pull."
    ),
    "wnba": (
        "State-level plurality only (Vivid Seats did not publish "
        "county-level WNBA data), so this is not population-weighted "
        "within the state -- it is a single state-wide assignment."
    ),
}


def load_county_population():
    pop = {}
    with open(RAW_DIR / "county_population.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pop[row["county_fips"]] = int(row["population_2025"])
    return pop


def load_state_population():
    pop = {}
    with open(ROOT / "data" / "registries" / "states.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pop[row["state_id"]] = int(row["population_2025"])
    return pop


def load_state_name_to_id():
    lookup = {}
    with open(ROOT / "data" / "registries" / "states.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            lookup[row["state_name"]] = row["state_id"]
    return lookup


def main():
    county_pop = load_county_population()
    state_pop = load_state_population()
    state_name_to_id = load_state_name_to_id()

    # (sport, state_id, entity_id) -> summed plurality-county population
    agg = defaultdict(int)
    county_level_sports = set()

    with open(RAW_DIR / "county_fandom.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row["entity_id"]:
                continue  # unresolved / historical-only / no registry yet (cfb)
            sport = row["sport"]
            state_id = state_name_to_id.get(row["state_name"])
            if state_id is None:
                continue
            if row["county_fips"]:
                county_level_sports.add(sport)
                pop = county_pop.get(row["county_fips"])
                if pop is None:
                    continue
                agg[(sport, state_id, row["entity_id"])] += pop
            elif sport == "wnba":
                # state-level plurality: treat as 100% of state population
                agg[(sport, state_id, row["entity_id"])] += state_pop[state_id]

    obs_rows = []
    obs_id = 1
    for (sport, state_id, entity_id), pop_sum in sorted(agg.items()):
        denom = state_pop[state_id]
        c_si = pop_sum / denom if denom else 0
        note = SPORT_QUALITY_NOTE.get(sport, "")
        quality = "Moderate" if sport != "wnba" else "Low"
        obs_rows.append({
            "observation_id": f"C_SI_{obs_id:05d}",
            "entity_id": entity_id,
            "state_id": state_id,
            "metric": "county_plurality_pop_share",
            "value": round(c_si, 6),
            "unit": "share_of_state_population",
            "source_url": "https://www.vividseats.com (see data/raw/county_fandom.csv per-row source) + https://www.census.gov (Vintage 2025 county population estimates)",
            "publisher": "Vivid Seats ticket-origin plurality map + U.S. Census Bureau population",
            "publication_date": "2025-2026",
            "measurement_window": "current (single ticket-origin snapshot, not multi-year)",
            "geography": "county-plurality-weighted" if sport in county_level_sports and sport != "wnba" else "state-level",
            "sample_size": "",
            "quality_class": quality,
            "missingness_type": "observed",
            "retrieved_at": RETRIEVED_AT,
            "notes": note,
        })
        obs_id += 1

    with open(OBS_PATH, newline="", encoding="utf-8") as f:
        existing_fieldnames = next(csv.reader(f))

    with open(OBS_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=existing_fieldnames)
        writer.writeheader()
        writer.writerows(obs_rows)

    print(f"Wrote {len(obs_rows)} C_si observation rows to {OBS_PATH}")
    by_sport = defaultdict(int)
    for (sport, _, _) in agg:
        by_sport[sport] += 1
    for sport, n in sorted(by_sport.items()):
        print(f"  {sport}: {n} (state, entity) pairs with nonzero plurality population")


if __name__ == "__main__":
    main()
