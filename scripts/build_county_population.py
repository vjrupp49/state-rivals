"""Phase 4B step 2/3: build data/raw/county_population.csv.

Source: Census Bureau Vintage 2025 county population estimates
(co-est2025-alldata.csv), county-level rows (SUMLEV == 050). This feeds the
county-to-state mapping and the population-weighting in C_si (docs/PROTOCOL.md
section 8).

Run from the project root:
    python scripts/build_county_population.py
"""
import csv
import datetime
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_states import STATE_FIPS_TO_USPS

ROOT = pathlib.Path(__file__).parent.parent
RAW_SOURCE = ROOT / "data" / "raw" / "co-est2025-alldata_source.csv"
OUT_PATH = ROOT / "data" / "raw" / "county_population.csv"
SOURCE_URL = (
    "https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/"
    "counties/totals/co-est2025-alldata.csv"
)


def main():
    retrieved_at = datetime.date.today().isoformat()
    rows = []
    with open(RAW_SOURCE, newline="", encoding="latin-1") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["SUMLEV"] != "050":
                continue
            state_fips = row["STATE"]
            usps = STATE_FIPS_TO_USPS.get(state_fips)
            if usps is None:
                continue
            county_fips = state_fips + row["COUNTY"]
            rows.append({
                "county_fips": county_fips,
                "state_id": usps,
                "state_name": row["STNAME"],
                "county_name": row["CTYNAME"],
                "population_2025": row["POPESTIMATE2025"],
                "population_2020_base": row["ESTIMATESBASE2020"],
                "source": SOURCE_URL,
                "retrieved_at": retrieved_at,
            })

    rows.sort(key=lambda r: r["county_fips"])
    fieldnames = [
        "county_fips", "state_id", "state_name", "county_name",
        "population_2025", "population_2020_base", "source", "retrieved_at",
    ]
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} county rows to {OUT_PATH}")
    n_states = len({r["state_id"] for r in rows})
    print(f"Distinct states+DC represented: {n_states}")


if __name__ == "__main__":
    main()
