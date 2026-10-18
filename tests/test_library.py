"""Library-level tests added after the independent review (2026-10-16): functions that matter but were not tested directly."""
import json
import pathlib
import sys

import numpy as np
import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import lib_model as LM  # noqa: E402
import lib_trends as L  # noqa: E402


def test_compute_H_with_neutral_place_factor_equals_original():
    rng = np.random.default_rng(0)
    A, R, E = rng.random((5, 7)), rng.random((7, 7)), rng.random((7, 4))
    assert np.allclose(LM.compute_H(A, R, E), LM.compute_H(A, R, E, np.ones((5, 7))))


def test_place_factor_decays_with_distance_and_is_one_at_home():
    states = ["CA", "NV", "NY"]
    ents = [{"home_state": "CA"}]
    D = LM.place_distance(states, ["x"], ents)
    F = LM.place_matrix(states, ["x"], ents, gamma=0.33)
    assert D[0, 0] < 0.01 and F[0, 0] == pytest.approx(1.0, abs=1e-3)
    assert F[1, 0] > F[2, 0]                      # Nevada is closer to California than New York is
    assert np.allclose(LM.place_matrix(states, ["x"], ents, gamma=0.0), 1.0)


def test_edges_are_unique_per_directed_pair_and_family():
    edges = [e for e in LM.build_edges(measured=False) if e[0] != "UNRESOLVED"]
    keys = [(e[0], e[1], e[2]) for e in edges]
    assert len(keys) == len(set(keys))


def _job(rows):
    return {"family": "T", "kind": "entities", "win": "W5", "names": ["A1", "A2", "X"], "rows": rows}


def test_estimate_recovers_a_known_ratio():
    smap = {"Alabama": "AL"}
    est = L.estimate([_job({"Alabama": [50, 30, 10]})], smap)       # X is a fifth of A1
    ln, var, flag = est[("X", "AL", "W5")]
    assert flag == "ok" and np.exp(ln) == pytest.approx(0.2, rel=0.08)


def test_estimate_keeps_censored_cells_as_censored_not_zero():
    smap = {"Alabama": "AL"}
    est = L.estimate([_job({"Alabama": [60, 40, 0]})], smap)        # X reported as 0: below detection, never a true zero
    ln, var, flag = est[("X", "AL", "W5")]
    assert flag == "below_detection" and np.isfinite(ln) and var >= 0.5


def test_verdict_file_is_internally_consistent():
    p = ROOT / "output" / "verdict.json"
    if not p.exists():
        pytest.skip("not built")
    v = json.loads(p.read_text(encoding="utf-8"))
    assert (v["declared_winner"] is not None) == (not v["failed_gates"])        # a winner only if every gate passed
    assert v["provisional"] or not v["open_items"]                                # open items keep the verdict provisional
    assert set(v["failed_gates"]) <= set(v["gates"])


def test_share_interval_bounds_are_ordered_and_censoring_widens_them():
    import channel_decomposition as CD
    rng = np.random.default_rng(0)
    units = ["a", "b", "c"]
    vals = {"a": 5.0, "b": 3.0, "c": 1.0}
    var = {"a": 0.01, "b": 0.01, "c": 0.5}
    detected = {"a": False, "b": False, "c": False}
    c0, lo0, hi0 = CD.share_interval(units, vals, var, detected, 'a', None, rng)
    assert lo0 <= c0 <= hi0
    censored_top = {"a": True, "b": False, "c": False}
    c1, lo1, hi1 = CD.share_interval(units, vals, var, censored_top, 'a', None, rng)
    assert lo1 <= c1 <= hi1 and lo1 == 0.0 and hi1 > c1          # a censored top unit can be anywhere from 0 to twice its floor
    assert (hi1 - lo1) > (hi0 - lo0)


def test_channel_decomposition_outputs_are_comparable_and_honest():
    p = ROOT / "data" / "model" / "channel_decomposition.csv"
    if not p.exists():
        pytest.skip("not built")
    import csv
    rows = list(csv.DictReader(open(p, encoding="utf-8")))
    for r in rows:
        assert float(r["raw_lo"]) <= float(r["raw_hi"]) + 1e-9                     # no inverted intervals
        if r["testable"] == "True":
            assert int(r["detected_units"]) >= 3 and float(r["detected_coverage"]) >= 0.8
        if r["verdict"] == "supported":
            assert r["model_share_excess_basis"] != "" and r["testable"] == "True"   # supported only when the corrected comparison used the same units


def test_missing_topdown_rank_never_corroborates():
    p = ROOT / "data" / "model" / "corroboration.csv"
    if not p.exists():
        pytest.skip("not built")
    import csv
    for r in csv.DictReader(open(p, encoding="utf-8")):
        if r["topdown_rank"] in ("", "0", "None"):
            assert r["C1_state_framing"] != "True" and r["corroborated"] != "True"


def test_gate_filters_ignore_padding_variants_and_irrelevant_sports():
    import build_report as BR
    variants = [
        {"variant": "base", "spearman_vs_base": "1.0", "top5": "A-B", "base_top1_rank": "1"},
        {"variant": "near_null", "spearman_vs_base": "0.995", "top5": "A-B", "base_top1_rank": "1"},
        {"variant": "informative", "spearman_vs_base": "0.90", "top5": "C-D", "base_top1_rank": "2"},
        {"variant": "leave_out_football", "spearman_vs_base": "0.9", "top5": "A-B", "base_top1_rank": "5"},
        {"variant": "leave_out_softball", "spearman_vs_base": "1.0", "top5": "A-B", "base_top1_rank": "1"},
    ]
    assert [v["variant"] for v in BR.informative_variants(variants)] == ["informative"]       # near-null variants cannot pad the denominator
    groups = {"football": {"nfl", "cfb"}, "softball": {"sfb"}}
    rel = BR.relevant_leave_outs(variants, {"nfl"}, groups)
    assert [v["variant"] for v in rel] == ["leave_out_football"]                               # softball cannot affect an NFL-driven pair


def test_second_proxy_gate_cannot_pass_without_or_against_proxies():
    import json
    v = json.loads((ROOT / "output" / "verdict.json").read_text(encoding="utf-8"))
    detail = v["diagnostics"]["second_proxy_detail"]
    gate = next(g for g in v["gates"] if g.startswith("second_independent_proxy"))
    if not detail or any(not ok for ok in detail.values()):
        assert v["gates"][gate] is False
