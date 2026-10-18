"""Schema contract: required columns for every published table (documented in docs/DATA_DICTIONARY.md)."""
import csv
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent

REQUIRED = {
    "data/registries/entities.csv": "entity_id organization_id entity_name sport sex_category level professional_college league conference division home_city home_state stadium_or_campus active_from active_to current_status source notes",
    "data/registries/states.csv": "state_id state_name state_fips census_region census_division is_contest_state population_2025 population_2020_base source retrieved_at notes",
    "data/registries/rivalry_edges.csv": "entity_i entity_j sport direction discovery_class source source_date lifecycle_status analyst_tier S_prior T_prior",
    "data/observations/observations.csv": "observation_id entity_id state_id metric value unit source_url publisher publication_date measurement_window geography sample_size quality_class missingness_type retrieved_at notes",
    "data/model/attention_team.csv": "state_id family entity_id P G_C G_P C_si confidence logsd flag",
    "data/model/attention_sport.csv": "state_id sport W method",
    "data/model/pair_scores.csv": "rank state_a state_b M H_a_to_b H_b_to_a reciprocity_ratio",
    "data/model/pair_uncertainty.csv": "state_a state_b M_base M_p05 M_p50 M_p95 P_rank1 P_top3 P_top10 median_rank",
    "data/model/channel_ledger.csv": "pair_rank direction source_state supported_entity rival_entity sport_family embodied_target_state contribution share_of_directed_H",
    "output/leaderboard.csv": "rank state_a state_b M M_p05 M_p95 P_rank1 P_top3 reciprocity",
}


@pytest.mark.parametrize("path,cols", REQUIRED.items())
def test_required_columns(path, cols):
    p = ROOT / path
    if not p.exists():
        pytest.skip(f"{path} not built")
    with open(p, newline="", encoding="utf-8") as f:
        header = next(csv.reader(f))
    missing = [c for c in cols.split() if c not in header]
    assert not missing, f"{path} missing {missing}"


def test_observations_have_unique_ids_and_provenance():
    import gzip
    import io
    ids, bad = set(), 0
    streams = [open(ROOT / "data/observations/observations.csv", newline="", encoding="utf-8")]
    gz = ROOT / "data/observations/observations_trends.csv.gz"
    if gz.exists():
        streams.append(io.TextIOWrapper(gzip.open(gz), encoding="utf-8", newline=""))
    for f in streams:
        with f:
            for r in csv.DictReader(f):
                assert r["observation_id"] not in ids
                ids.add(r["observation_id"])
                bad += not (r["source_url"] and r["publisher"])
    assert bad == 0


def test_edges_reference_registry_entities():
    ents = set()
    with open(ROOT / "data/registries/entities.csv", newline="", encoding="utf-8") as f:
        ents = {r["entity_id"] for r in csv.DictReader(f)}
    with open(ROOT / "data/registries/rivalry_edges.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            assert r["entity_i"] in ents and r["entity_j"] in ents


def test_no_duplicate_program_per_organization_and_family():
    seen = {}
    with open(ROOT / "data/registries/entities.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            eid = r["entity_id"]
            fam = "_".join(eid.split("_")[:2]) if eid.split("_")[0] in ("cbb", "hky", "lax") else eid.split("_")[0]
            if r["professional_college"] != "college" or fam == "cfb":
                continue
            key = (fam, r["organization_id"])
            assert key not in seen, f"duplicate {key}: {seen[key]} and {eid}"
            seen[key] = eid


def test_football_has_no_duplicate_programs_by_state_and_nickname():
    seen = {}
    with open(ROOT / "data/registries/entities.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not r["entity_id"].startswith("cfb_"):
                continue
            nick = r["entity_name"].replace(" Football", "").split()[-1].lower()
            key = (r["home_state"], nick, r["level"])
            seen.setdefault(key, []).append(r["entity_id"])
    dups = {k: v for k, v in seen.items() if len(v) > 1}
    # known legitimate same-state/same-nickname pairs (different schools): listed explicitly
    allowed = {("SC", "bulldogs", "FCS"), ("TX", "cardinals", "FCS"), ("AL", "bulldogs", "FCS"), ("NC", "eagles", "FCS"), ("OH", "bobcats", "FBS")}
    assert not {k: v for k, v in dups.items() if k not in allowed}, dups
