"""Invariant tests on committed model outputs and the brief's worked arithmetic."""
import math
import pathlib

import pandas as pd
import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODEL = ROOT / "data" / "model"


def _need(path):
    if not path.exists():
        pytest.skip(f"{path.name} not built")
    return path


def test_geometric_mean_penalizes_lopsided_pairs():
    # docs/PROTOCOL.md section 2: .50/.10 -> .224 ; balanced .30/.30 -> .300 (computed by the library's pair_scores)
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    import lib_model as LM
    import numpy as np
    _, m1 = LM.pair_scores(np.array([[0.0, 0.50], [0.10, 0.0]]), ["a", "b"])
    _, m2 = LM.pair_scores(np.array([[0.0, 0.30], [0.30, 0.0]]), ["a", "b"])
    assert round(m1[0, 1], 3) == 0.224 and round(m2[0, 1], 3) == 0.300


def test_worked_example_channel():
    # .32 NFL share * .82 Vikings share = .2624 ; * .50 salience * 1.0 identity = .1312 (computed by the library's compute_H)
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    import lib_model as LM
    import numpy as np
    A = np.array([[0.32 * 0.82, 0.0]])
    R = np.array([[0.0, 0.50], [0.0, 0.0]])
    E = np.array([[0.0, 0.0], [1.0, 0.0]])
    assert round(LM.compute_H(A, R, E)[0, 0], 4) == 0.1312


def test_attention_rows_sum_to_one():
    df = pd.read_csv(_need(MODEL / "A_matrix.csv")).set_index("state_id")
    assert len(df) == 50
    assert (df.sum(axis=1) - 1).abs().max() < 1e-9
    assert (df >= 0).all().all()


def test_pair_scores_cover_all_pairs_and_are_reciprocal():
    df = pd.read_csv(_need(MODEL / "pair_scores.csv"))
    assert len(df) == 1225
    assert (df.state_a < df.state_b).all()
    assert df[["state_a", "state_b"]].drop_duplicates().shape[0] == 1225
    expect = (df.H_a_to_b * df.H_b_to_a) ** 0.5
    assert ((expect - df.M).abs() < 1e-6).all()


def test_states_registry():
    df = pd.read_csv(ROOT / "data" / "registries" / "states.csv")
    assert df.state_id.is_unique
    assert (df.is_contest_state.astype(str).str.upper() == "TRUE").sum() == 50


def test_entity_ids_unique():
    df = pd.read_csv(ROOT / "data" / "registries" / "entities.csv")
    assert df.entity_id.is_unique


def test_priors_config_is_well_formed():
    import yaml
    pri = yaml.safe_load((ROOT / "config" / "priors.yaml").read_text(encoding="utf-8"))
    assert set(pri["tier_s"]) == set(pri["tier_t"]) == {1, 2, 3}
    assert all(0 < v < 1 for v in pri["tier_s"].values())
    assert 0 < pri["row_cap"] <= 1
    for eid, spec in pri["e_entity_exceptions"].items():
        assert sum(spec.values()) <= 1.0 + 1e-9, eid
