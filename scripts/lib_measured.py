"""Measured antipathy per (state, unit), on one scale ('Cowboys suck' units per state). Shared by channel_decomposition.py and
measured_hostility.py. A unit is a pro team or a college school (school-level terms cannot separate sports)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import lib_trends as L  # noqa: E402
import trends_worker as TW  # noqa: E402

OKF = ("ok", "anchor", "low_anchor")
CENS = OKF + ("below_detection",)


def measurements(smap, reg):
    """Observed-only view: (v, unit_name, school_of_cfb) with v[(state, unit)] = interest in Cowboys-suck units for cells that are
    detected (not censored); None if the bridges are not ready. Censored cells are treated as missing here (never as zero)."""
    out = measurements_full(smap, reg)
    if out is None:
        return None
    full, unit_name, school_of_cfb = out
    return {k: x[0] for k, x in full.items() if not x[2]}, unit_name, school_of_cfb


def measurements_full(smap, reg):
    """(full, unit_name, school_of_cfb) with full[(state, unit)] = (value, ln_variance, censored). A censored cell (below detection) carries
    the estimator's floor value, an UPPER bound on the true interest, and a large variance; callers decide how to bound it (D-007)."""
    bridge = {}
    for lg in ("mlb", "nba", "nhl", "cfb"):
        bj = L.load_jobs(family=f"BRIDGE_{lg}")
        if not bj:
            return None
        bridge[lg] = L.estimate(bj, smap)

    cfb_terms = TW._hate_terms_cfb()                       # entity -> 'School sucks'
    school_of_cfb = {e: t[:-6] for e, t in cfb_terms.items()}
    unit_name = {}                                         # unit key -> display
    v = {}                                                 # (state, unit) -> (Cowboys-unit interest, ln variance, censored)

    def add(sid, unit, e, scale, svar, name):
        v[(sid, unit)] = (math.exp(e[0]) * scale, e[1] + svar, e[2] == 'below_detection')
        unit_name[unit] = name

    est_cfb = est_sch = None
    for lg in ("nfl", "mlb", "nba", "nhl", "cfb", "sch"):
        jobs = L.load_jobs(family=f"HATE_{lg}")
        if not jobs:
            continue
        est = L.estimate(jobs, smap)
        if lg == "cfb":
            est_cfb = est
        if lg == "sch":
            est_sch = est
        for sid in smap.values():
            svar = 0.0
            if lg == "nfl":
                scale = 1.0
            elif lg in ("mlb", "nba", "nhl"):
                b_a = bridge[lg].get((TW.BRIDGE_TERMS[lg], sid, "W5"))
                if not (b_a and b_a[2] in OKF):
                    continue
                scale = math.exp(b_a[0])
                svar = b_a[1]
            elif lg == "cfb":
                b_a = bridge["cfb"].get(("Ohio State sucks", sid, "W5"))
                l_os = est.get(("Ohio State sucks", sid, "W5"))
                if not (b_a and l_os and b_a[2] in OKF and l_os[2] in OKF):
                    continue
                scale = math.exp(b_a[0] - l_os[0])
                svar = b_a[1] + l_os[1]
            else:                                          # 'sch': units of Duke; Duke in Cowboys units via the cfb chain
                if est_cfb is None:
                    continue
                b_os = bridge["cfb"].get(("Ohio State sucks", sid, "W5"))
                c_os = est_cfb.get(("Ohio State sucks", sid, "W5"))
                c_duke = est_cfb.get(("Duke sucks", sid, "W5"))
                if not (b_os and c_os and c_duke and all(x[2] in OKF for x in (b_os, c_os, c_duke))):
                    continue
                scale = math.exp(c_duke[0]) * math.exp(b_os[0] - c_os[0])
                svar = c_duke[1] + b_os[1] + c_os[1]
            if lg in ("nfl", "mlb", "nba", "nhl"):
                for eid, term in TW._hate_terms(lg).items():
                    e = est.get((term, sid, "W5"))
                    if e and e[2] in CENS:
                        add(sid, "pro:" + eid, e, scale, svar, reg[eid]["entity_name"])
            elif lg == "cfb":
                for eid, term in cfb_terms.items():
                    e = est.get((term, sid, "W5"))
                    if e and e[2] in CENS:
                        add(sid, "sch:" + school_of_cfb[eid], e, scale, svar, school_of_cfb[eid])
            else:
                for sch in TW.EXTRA_SCHOOLS:
                    e = est.get((sch + " sucks", sid, "W5"))
                    if e and e[2] in CENS:
                        add(sid, "sch:" + sch, e, scale, svar, sch)
    return v, unit_name, school_of_cfb
