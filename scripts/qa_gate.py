"""QA gate (Phase 4B definition of done + Phase 8 sanity checks + brief worked-example unit tests).
Writes output/qa_report.json and returns the check list. status per check: pass | warn | fail.
"""
import csv
import json
import math
import sys
import pathlib
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import lib_model as LM

ROOT, MODEL = LM.ROOT, LM.MODEL


def run():
    checks = []

    def add(name, status, detail=""):
        checks.append({"check": name, "status": status, "detail": detail})

    # --- unit tests from docs/PROTOCOL.md worked examples
    add("unit: geometric mean .50/.10 = .224 vs balanced .30/.30 = .300",
        "pass" if abs(math.sqrt(.5 * .1) - .2236) < 1e-3 and abs(math.sqrt(.3 * .3) - .3) < 1e-12 else "fail")
    add("unit: A(MN,Vikings)=.32*.82=.2624 ; channel .2624*.50*1=.1312",
        "pass" if abs(.32 * .82 - .2624) < 1e-9 and abs(.2624 * .5 * 1 - .1312) < 1e-9 else "fail")
    R = np.array([[0, .5], [0, 0]]); E = np.array([[0, 0], [1., 0]]); A = np.array([[.2624, 0]])
    add("unit: library compute_H reproduces .1312 on the brief's toy case (with and without a neutral place factor)",
        "pass" if abs(LM.compute_H(A, R, E)[0, 0] - .1312) < 1e-9 and abs(LM.compute_H(A, R, E, np.ones((1, 2)))[0, 0] - .1312) < 1e-9 else "fail")
    Hs_ = np.array([[0.0, .5], [.1, 0.0]])
    _, Mt_ = LM.pair_scores(Hs_, ["a", "b"])
    add("unit: library pair_scores gives the geometric mean (.50,.10 -> .2236)", "pass" if abs(Mt_[0, 1] - math.sqrt(.05)) < 1e-9 else "fail")
    # --- matrices
    states, ids, A, other = LM.load_A()
    err = float(np.abs(A.sum(1) + other - 1).max())
    add("every state row of A (+OTHER) sums to 1", "pass" if err < 1e-9 else "fail", f"max err {err:.2e}")
    add("A has no NaN / negative cells", "pass" if np.isfinite(A).all() and (A >= 0).all() else "fail")
    audit = json.loads((MODEL / "A_audit.json").read_text())
    hi = audit.get("states_other_gt_2pct", [])
    add("OTHER visible; states with OTHER>2% flagged for re-inspection", "warn" if hi else "pass",
        f"{len(hi)} states >2% (unmeasured/unregistered sports land in OTHER by design)")
    unm = audit.get("families_unmeasured_to_OTHER", [])
    add("all sport families measured (>=50% real signal)", "warn" if unm else "pass", f"unmeasured: {unm}")
    pm = min(float(r["P"]) for r in csv.DictReader(open(MODEL / "attention_team.csv", encoding="utf-8")))
    add("no entity has exactly-zero P (missing != zero, D-007)", "pass" if pm > 0 else "fail", f"min P={pm:.2e}")
    E = list(csv.reader(open(MODEL / "E_matrix.csv", encoding="utf-8")))[1:]
    es = max(sum(float(x) for x in r[1:]) for r in E)
    add("E row sums <= 1", "pass" if es <= 1 + 1e-6 else "fail", f"max {es:.6f}")
    # --- provenance
    import gzip
    import io
    obs = list(csv.DictReader(open(ROOT / "data" / "observations" / "observations.csv", encoding="utf-8")))
    tg = ROOT / "data" / "observations" / "observations_trends.csv.gz"
    if tg.exists():
        obs += list(csv.DictReader(io.TextIOWrapper(gzip.open(tg), encoding="utf-8")))
    miss = sum(1 for r in obs if not r["source_url"])
    add("every observation row has provenance (source_url)", "pass" if miss == 0 else "fail", f"{len(obs)} rows, {miss} missing")
    ent = list(csv.DictReader(open(ROOT / "data" / "registries" / "entities.csv", encoding="utf-8")))
    add("every registry entity has a source", "pass" if all(e["source"] for e in ent) else "fail")
    # --- pair outputs
    ps = list(csv.DictReader(open(MODEL / "pair_scores.csv", encoding="utf-8")))
    add("1,225 unordered pairs scored", "pass" if len(ps) == 1225 else "fail", f"{len(ps)}")
    rk = {(r["state_a"], r["state_b"]): int(r["rank"]) for r in ps}
    rk.update({(b, a): v for (a, b), v in list(rk.items())})
    for a, b in (("MI", "OH"), ("MN", "WI")):
        r = rk.get((a, b))
        add(f"sanity: {a}-{b} emerges as a strong channel (top 25 of 1,225)", "pass" if r and r <= 25 else "warn",
            f"rank {r} -- NOTE rivalry priors name these rivalries, so this checks wiring, not independent evidence")
    ms = np.array([float(r["M"]) for r in ps])
    top10 = np.sort(ms)[::-1][:10].mean()
    add("sanity: median pair far below top pairs (no-structure pairs near zero)", "pass" if np.median(ms) < 0.1 * top10 else "warn",
        f"median {np.median(ms):.4g} vs top10 mean {top10:.4g}")
    mi = json.loads((MODEL / "model_run.json").read_text())
    add("all curated rivalry specs resolved to registry entities", "pass" if mi["n_unresolved"] == 0 else "warn",
        f"{mi['n_unresolved']} unresolved: {mi['unresolved_samples'][:5]}")
    out = ROOT / "output"
    out.mkdir(exist_ok=True)
    (out / "qa_report.json").write_text(json.dumps(checks, indent=1), encoding="utf-8")
    return checks


if __name__ == "__main__":
    c = run()
    for x in c:
        print(f"[{x['status'].upper():4}] {x['check']} {x['detail']}")
