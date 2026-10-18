"""Phase 4B step 7 (pilot): validate the anchored-batch Google Trends
extraction methodology from docs/PROTOCOL.md section 8 on a small, checkable
slice before committing to the full 1,765-entity x 50-state run.

Why a pilot first: Trends only returns relative 0-100 scores WITHIN a single
<=5-term comparison, so covering an entire sport's entity set for one state
needs multiple batches -- and separate batches aren't on the same scale
unless every batch shares a common "anchor" term whose returned value lets
you rescale the rest onto one coordinate system (this is exactly the
"anchored query batching" docs/PROTOCOL.md section 8 calls for). This script
proves that mechanism actually works and produces sane numbers, using NFL
in Minnesota as the test case -- we already have real, independently
sourced ground truth to check against (data/observations/observations.csv:
Vikings = 97.9% county-plurality population share in MN from Phase 4B step
4-5), so a correct extraction should show the Vikings dominating.

This does NOT attempt the full-scale pull. At one request every ~2 seconds
to stay under Trends' unofficial rate limits, 1,765 entities x 50 states in
anchored batches of 5 is on the order of tens of thousands of requests --
a multi-day background job, not a single-session task. This script's job
is to prove the methodology and give a real (small) data point, not to
fabricate coverage.

Run from the project root:
    python scripts/pull_trends_pilot.py
"""
import csv
import datetime
import pathlib
import time

from pytrends.request import TrendReq

ROOT = pathlib.Path(__file__).parent.parent
OUT_PATH = ROOT / "data" / "raw" / "trends_pilot_nfl_mn.csv"
RETRIEVED_AT = "2026-09-15"

# Query strings as drafted in data/raw/google_topics.csv for the 32 NFL
# entities. Cowboys chosen as anchor: nationally highest and most stable
# search volume, so it's very unlikely to be zero/near-zero in any batch,
# which would make rescaling unstable.
ANCHOR = "Dallas Cowboys"
NFL_TEAMS = [
    "Buffalo Bills", "Miami Dolphins", "New England Patriots", "New York Jets",
    "Baltimore Ravens", "Cincinnati Bengals", "Cleveland Browns", "Pittsburgh Steelers",
    "Houston Texans", "Indianapolis Colts", "Jacksonville Jaguars", "Tennessee Titans",
    "Denver Broncos", "Kansas City Chiefs", "Las Vegas Raiders", "Los Angeles Chargers",
    "New York Giants", "Philadelphia Eagles", "Washington Commanders",
    "Chicago Bears", "Detroit Lions", "Green Bay Packers", "Minnesota Vikings",
    "Atlanta Falcons", "Carolina Panthers", "New Orleans Saints", "Tampa Bay Buccaneers",
    "Arizona Cardinals", "Los Angeles Rams", "San Francisco 49ers", "Seattle Seahawks",
]
GEO = "US-MN"
TIMEFRAME = "today 12-m"
REQUEST_DELAY_SEC = 2.5


def batches(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def main():
    pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
    raw_scores = {}  # team -> mean interest-over-time value, RAW (uncalibrated)
    anchor_values = []

    team_batches = list(batches(NFL_TEAMS, 4))  # 4 teams + anchor = 5 terms
    print(f"Pulling {len(team_batches)} anchored batches for geo={GEO}...")

    for i, batch in enumerate(team_batches):
        terms = [ANCHOR] + batch
        for attempt in range(3):
            try:
                pytrends.build_payload(terms, cat=0, timeframe=TIMEFRAME, geo=GEO)
                df = pytrends.interest_over_time()
                break
            except Exception as e:
                print(f"  batch {i} attempt {attempt} failed: {e}")
                time.sleep(5 * (attempt + 1))
        else:
            print(f"  batch {i} FAILED after 3 attempts, skipping")
            continue

        means = df[terms].mean()
        anchor_val = means[ANCHOR]
        anchor_values.append(anchor_val)
        for team in batch:
            raw_scores[team] = {"raw_mean": means[team], "anchor_in_batch": anchor_val}
        print(f"  batch {i}: anchor={anchor_val:.1f}, " +
              ", ".join(f"{t}={means[t]:.1f}" for t in batch))
        time.sleep(REQUEST_DELAY_SEC)

    if not anchor_values:
        print("No successful batches -- aborting.")
        return

    # Rescale every batch onto a common coordinate system using the
    # grand-mean anchor value as the reference point (docs/PROTOCOL.md section 8
    # "anchored query batching").
    grand_mean_anchor = sum(anchor_values) / len(anchor_values)
    rows = []
    for team, vals in raw_scores.items():
        rescale_factor = grand_mean_anchor / vals["anchor_in_batch"] if vals["anchor_in_batch"] else float("nan")
        calibrated = vals["raw_mean"] * rescale_factor
        rows.append({
            "entity_name": team,
            "geo": GEO,
            "raw_mean_interest": round(vals["raw_mean"], 2),
            "anchor_value_in_its_batch": round(vals["anchor_in_batch"], 2),
            "grand_mean_anchor": round(grand_mean_anchor, 2),
            "calibrated_score": round(calibrated, 2),
            "timeframe": TIMEFRAME,
            "source": "Google Trends via pytrends (unofficial API)",
            "retrieved_at": RETRIEVED_AT,
        })

    # Within-sport share P_si|k for this one state, from calibrated scores.
    total = sum(r["calibrated_score"] for r in rows)
    for r in rows:
        r["P_within_nfl_this_state"] = round(r["calibrated_score"] / total, 4) if total else None

    rows.sort(key=lambda r: -r["calibrated_score"])

    fieldnames = ["entity_name", "geo", "raw_mean_interest",
                  "anchor_value_in_its_batch", "grand_mean_anchor",
                  "calibrated_score", "P_within_nfl_this_state",
                  "timeframe", "source", "retrieved_at"]
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} calibrated team scores to {OUT_PATH}")
    print("\nTop 5 by calibrated score (within-NFL share of MN attention):")
    for r in rows[:5]:
        print(f"  {r['entity_name']}: calibrated={r['calibrated_score']}, "
              f"P_within_nfl={r['P_within_nfl_this_state']}")


if __name__ == "__main__":
    main()
