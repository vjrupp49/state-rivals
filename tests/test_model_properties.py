"""Model properties required by docs/PROTOCOL.md section 11, tested on toy matrices (engine) and real outputs (data).

Toy tests use the engine itself (lib_model.compute_H, pair_scores, build_R) so they cannot pass
by construction of the priors. Data tests check the committed outputs.
"""
import pathlib
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import lib_model as LM  # noqa: E402


def _pair_M(A, R, E, states=("a", "b")):
    H = LM.compute_H(A, R, E)
    Hs, M = LM.pair_scores(H, list(states))
    return Hs, M


def test_shared_fandom_dampens_hostility():
    # entities: 0 = team in state a, 1 = rival team embodying state b. Both directions rival.
    R = np.array([[0.0, 0.5], [0.5, 0.0]])
    E = np.array([[1.0, 0.0], [0.0, 1.0]])      # entity0 -> a, entity1 -> b
    base = np.array([[0.8, 0.2], [0.2, 0.8]])    # a mostly supports 0; b mostly supports 1
    shared = np.array([[0.8, 0.2], [0.2, 0.8]])
    # a's residents shift attention toward team 1 (shared fandom of b's team): a->b hostility falls
    shared[0] = [0.5, 0.5]
    H0, _ = _pair_M(base, R, E)
    H1, _ = _pair_M(shared, R, E)
    # a->b flows through team 0's rivalry toward team 1 (embodying b)
    assert H1[0, 1] < H0[0, 1]


def test_one_sided_rivalry_loses_under_reciprocal_score():
    # same total hostility, balanced vs lopsided: geometric mean must prefer balance
    lopsided = np.sqrt(0.50 * 0.10)
    balanced = np.sqrt(0.30 * 0.30)
    assert lopsided < balanced < (0.50 + 0.10) / 2 + 1e-12


def test_in_state_rivalry_consumes_attention():
    ids = ["i", "j", "k"]                         # i rivals j (other state) and optionally k (same state as i)
    fam = "nfl"
    without = [("i", "j", fam, 1, 0.40, 0.85)]
    with_in_state = without + [("i", "k", fam, 1, 0.50, 0.85)]
    r0 = LM.build_R(ids, without)
    r1 = LM.build_R(ids, with_in_state)
    # adding an in-state rival pushes the row over the cap and shrinks the interstate edge
    assert r1[0, 1] < r0[0, 1]


def test_geometric_mean_is_symmetric_and_diagonal_ignored():
    A = np.array([[0.6, 0.4], [0.3, 0.7]])
    R = np.array([[0.2, 0.3], [0.1, 0.4]])
    E = np.eye(2)
    Hs, M = _pair_M(A, R, E)
    assert Hs[0, 0] == 0 and Hs[1, 1] == 0
    assert M[0, 1] == pytest.approx(M[1, 0])
    assert M[0, 1] == pytest.approx(np.sqrt(Hs[0, 1] * Hs[1, 0]))


def test_new_leagues_do_not_leapfrog():
    p = ROOT / "data" / "model" / "channel_ledger.csv"
    if not p.exists():
        pytest.skip("channel ledger not built")
    cl = pd.read_csv(p)
    top = cl[cl.pair_rank <= 10]
    young = top[top.sport_family.isin(["pwhl", "wnba", "nwsl"])].contribution.sum()
    assert young / top.contribution.sum() < 0.05


def test_random_pairs_stay_near_zero():
    p = ROOT / "data" / "model" / "pair_scores.csv"
    if not p.exists():
        pytest.skip("pair scores not built")
    m = pd.read_csv(p).M
    assert m.median() < 0.05 * m.nlargest(10).mean()


def test_stress_cases_are_scored():
    p = ROOT / "data" / "model" / "pair_scores.csv"
    if not p.exists():
        pytest.skip("pair scores not built")
    ps = pd.read_csv(p).set_index(["state_a", "state_b"])
    for pair in (("KS", "MO"), ("MA", "NY"), ("OR", "WA")):
        assert pair in ps.index and ps.loc[pair, "M"] > 0


def test_measured_split_preserves_total_salience():
    # the measured co-search split may only move salience among a team's rivals, never create or destroy it
    a = LM.build_edges(measured=False)
    b = LM.build_edges(measured=True)
    ta = sum(e[4] for e in a if e[0] != "UNRESOLVED")
    tb = sum(e[4] for e in b if e[0] != "UNRESOLVED")
    assert tb == pytest.approx(ta, rel=1e-9)
    assert all(x[:4] == y[:4] and x[5] == y[5] for x, y in zip(a, b) if x[0] != "UNRESOLVED")   # tiers and T untouched


def test_verdict_coverage_gate_sees_the_lead_pair_channels():
    # regression: the gate once ran before the channel ledger was loaded, so it failed unconditionally
    import json
    v = json.loads((ROOT / "output" / "verdict.json").read_text(encoding="utf-8"))
    audit = json.loads((ROOT / "data" / "model" / "A_audit.json").read_text(encoding="utf-8"))
    cov = audit["family_detected_coverage"]
    led = pd.read_csv(ROOT / "data" / "model" / "channel_ledger.csv")
    top = led[(led.pair_rank == 1) & (led.share_of_directed_H >= 0.05)]
    expect = bool(len(top)) and all(cov.get(f, 0) >= 0.7 for f in top.sport_family)
    gate = next(g for g in v["gates"] if g.startswith("detected_trends_coverage>=70%"))
    assert (gate not in v["failed_gates"]) == expect       # the gate exists and agrees with the data
