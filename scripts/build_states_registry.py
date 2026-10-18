"""Phase 4B step 2/3 (partial): build data/registries/states.csv.

Source: Census Bureau Vintage 2025 county population estimates
(co-est2025-alldata.csv), state-level rows (SUMLEV == 040). Region/division
codes come straight from that file so the classification is traceable to
source rather than hand-typed.

Run from the project root:
    python scripts/build_states_registry.py
"""
import csv
import datetime
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from lib_states import STATE_FIPS_TO_USPS, CENSUS_REGION_NAMES, CENSUS_DIVISION_NAMES

ROOT = pathlib.Path(__file__).parent.parent
RAW_SOURCE = ROOT / "data" / "raw" / "co-est2025-alldata_source.csv"
OUT_PATH = ROOT / "data" / "registries" / "states.csv"
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
            if row["SUMLEV"] != "040":
                continue
            fips = row["STATE"]
            usps = STATE_FIPS_TO_USPS.get(fips)
            if usps is None:
                continue
            rows.append({
                "state_id": usps,
                "state_name": row["STNAME"],
                "state_fips": fips,
                "census_region": CENSUS_REGION_NAMES.get(row["REGION"], ""),
                "census_division": CENSUS_DIVISION_NAMES.get(row["DIVISION"], ""),
                "is_contest_state": "FALSE" if usps == "DC" else "TRUE",
                "population_2025": row["POPESTIMATE2025"],
                "population_2020_base": row["ESTIMATESBASE2020"],
                "source": SOURCE_URL,
                "retrieved_at": retrieved_at,
                "notes": (
                    "D.C. retained in network per docs/PROTOCOL.md section 5; not a "
                    "contest state (D-001)." if usps == "DC" else ""
                ),
            })

    rows.sort(key=lambda r: r["state_id"])
    fieldnames = [
        "state_id", "state_name", "state_fips", "census_region",
        "census_division", "is_contest_state", "population_2025",
        "population_2020_base", "source", "retrieved_at", "notes",
    ]
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
