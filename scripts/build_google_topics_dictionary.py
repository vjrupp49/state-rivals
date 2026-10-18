"""Phase 4B step 6: build data/raw/google_topics.csv (query dictionary only).

docs/PROTOCOL.md section 8 requires every Trends query to use an unambiguous
entity/topic definition (e.g. "Minnesota Vikings -- American football
team"), never a bare ambiguous string. This script only constructs the
disambiguated query strings and flags entities whose bare mascot name is a
common English word / shared across leagues -- it does NOT call the Trends
API. Resolving each query string to a stable Trends topic ID (mid) and
pulling the actual 5-year series is step 7, a separate live-data script.

Run from the project root (after build_entities_registry.py):
    python scripts/build_google_topics_dictionary.py
"""
import csv
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
ENTITIES_PATH = ROOT / "data" / "registries" / "entities.csv"
OUT_PATH = ROOT / "data" / "raw" / "google_topics.csv"

SPORT_TO_TOPIC_TYPE = {
    "American football": "American football team",
    "Baseball": "Baseball team",
    "Basketball": "Basketball team",
    "Ice hockey": "Ice hockey team",
    "Soccer": "Soccer team",
}

# Bare mascot/nickname is a common word or shared across multiple
# franchises/leagues -- these MUST use the disambiguated query, never the
# bare string, when pulled in Phase 4B step 7.
AMBIGUOUS_MASCOTS = {
    "Giants", "Rangers", "Jets", "Panthers", "Heat", "Jazz", "Kings", "Wild",
    "Storm", "Sun", "Fire", "Dream", "Pride", "Current", "Stars", "Magic",
    "Thunder", "Wave", "Union", "Dynamo", "Revolution", "Crew", "Sky",
    "Liberty", "Mercury", "Lightning", "Wings", "Aces", "Mystics",
}


def load_entities():
    with open(ENTITIES_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_rows(entities):
    rows = []
    for e in entities:
        mascot = e["entity_name"].split()[-1]
        if e["entity_name"].endswith("Football") and e["professional_college"] == "college":
            # College football entity names already read like
            # "Alabama Crimson Tide Football" -- fully disambiguated on
            # their own; appending "American football team" would just be
            # redundant ("Football ... American football team").
            query_string = e["entity_name"]
        else:
            topic_type = SPORT_TO_TOPIC_TYPE.get(e["sport"], e["sport"])
            query_string = f'{e["entity_name"]} — {topic_type}'
        ambiguity_flag = "TRUE" if mascot in AMBIGUOUS_MASCOTS else "FALSE"
        rows.append({
            "entity_id": e["entity_id"],
            "entity_name": e["entity_name"],
            "query_string": query_string,
            "query_type": "topic",
            "trends_topic_mid": "",  # resolved live in Phase 4B step 7
            "ambiguity_flag": ambiguity_flag,
            "ambiguity_reason": (
                f"Bare nickname '{mascot}' is shared/common; must resolve to "
                "the league-specific topic entity, not the bare search term."
                if ambiguity_flag == "TRUE" else ""
            ),
            "status": "query_defined_topic_unresolved",
            "notes": "",
        })
    return rows


def main():
    entities = load_entities()
    rows = build_rows(entities)
    fieldnames = [
        "entity_id", "entity_name", "query_string", "query_type",
        "trends_topic_mid", "ambiguity_flag", "ambiguity_reason", "status",
        "notes",
    ]
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    n_ambiguous = sum(1 for r in rows if r["ambiguity_flag"] == "TRUE")
    print(f"Wrote {len(rows)} query rows to {OUT_PATH}")
    print(f"Flagged ambiguous mascot names: {n_ambiguous}")
    print(
        "All trends_topic_mid values are blank -- resolving them and pulling "
        "the actual 5-year Trends series is Phase 4B step 7, not done here."
    )


if __name__ == "__main__":
    main()
