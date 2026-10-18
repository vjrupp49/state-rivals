"""Model library: E (entity -> identity) priors, rivalry edges (K, S, T, R), H and M.

EVERYTHING in the rivalry and E layers below is an ANALYST PRIOR, not measured
survey data (Know Rivalry blocks scripted access; no survey points retrieved).
Priors are uniform by tier/class, listed in one place, tagged source=analyst_prior,
and stress-tested in robustness.py (including a flat-tier 'structure only' variant).
Locked decisions D-004..D-006 (directed graph, geometric-mean reciprocity,
H = A(S.T)E) are implemented exactly; diagonal H_aa is ignored.
"""
import csv
import math
import pathlib
import re
import numpy as np
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODEL = ROOT / "data" / "model"
STATES = None

# ---------------------------------------------------------------- priors (config/*.yaml)
CONFIG = ROOT / "config"


def _load_yaml(name):
    with open(CONFIG / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


_PRI = _load_yaml("priors.yaml")
_CUR = _load_yaml("rivalry_curated.yaml")
TIER_S = _PRI["tier_s"]                  # share of i's rivalry attention going to j
TIER_T = _PRI["tier_t"]                  # emotional temperature
CLASS_FACTOR = _PRI["class_factor"]
ROW_CAP = _PRI["row_cap"]
# pro: family -> [(spec_a, spec_b, tier_a_to_b, tier_b_to_a)] ; spec = nickname within family
PRO = {k: [tuple(x) for x in v] for k, v in _CUR["pro"].items()}
# college pairs by school short name: (A, B, fb_ab, fb_ba, bb_tier, {sport: tier override})
COL = [tuple(x) for x in _CUR["college"]]
SUFFIX = {"cbb_m": "Men's Basketball", "cbb_w": "Women's Basketball", "hky_m": "Men's Ice Hockey",
          "hky_w": "Women's Ice Hockey", "bsb": "Baseball", "sfb": "Softball",
          "vbw": "Women's Volleyball"}
ALIAS_CFB = {"Miami (FL)": "Miami", "NC State": "North Carolina State"}


def fam_of(eid):
    p = eid.split("_")
    return "_".join(p[:2]) if p[0] in ("cbb", "hky") else p[0]


def load_entities():
    with open(ROOT / "data" / "registries" / "entities.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_edges(flat=False, measured=True):
    """Return list of directed edges (i, j, fam, tier_ij, S, T, cls)."""
    ents = load_entities()
    byfam = {}
    for e in ents:
        byfam.setdefault(fam_of(e["entity_id"]), []).append(e)
    edges = []
    meta = {}          # (i, j, fam) -> (school_i, school_j) for college edges (used by the measured split)

    seen = {}          # (i, j, fam) -> (index into edges, explicit): the same directed pair can be listed twice in the curated list

    def add(i, j, fam, t_ij, t_ji, schools_pair=None, explicit=False):
        for a, b, t in ((i, j, t_ij), (j, i, t_ji)):
            if t in (1, 2, 3):
                key = (a, b, fam)
                if key in seen:
                    k, was_explicit = seen[key]
                    if explicit and not was_explicit:        # an explicit per-sport override beats a derived tier; otherwise first listing stands
                        edges[k] = (a, b, fam, t)
                        seen[key] = (k, True)
                else:
                    seen[key] = (len(edges), explicit)
                    edges.append((a, b, fam, t))
                if schools_pair:
                    meta[key] = schools_pair if a == i else schools_pair[::-1]

    for fam, pairs in PRO.items():
        names = {e["entity_id"]: e["entity_name"].lower() for e in byfam[fam]}
        def find(spec):
            c = [i for i, n in names.items() if n.endswith(" " + spec) or n == spec or (" " + spec + " ") in n or n.startswith(spec + " ")]
            if len(c) > 1:
                c2 = [i for i in c if names[i].endswith(" " + spec)]
                c = c2 or c
            return c[0] if len(c) == 1 else None
        for a, b, tab, tba in pairs:
            ia, ib = find(a), find(b)
            if ia and ib:
                add(ia, ib, fam, tab, tba)
            else:
                edges.append(("UNRESOLVED", f"{fam}:{a}|{b}", fam, 0))
    # college
    schools = {}
    for fam, suf in SUFFIX.items():
        for e in byfam.get(fam, []):
            s = e["entity_name"][: -len(suf) - 1]
            schools.setdefault(s, {})[fam] = e["entity_id"]
    cfb_names = {e["entity_id"]: e["entity_name"][:-len(" Football")] for e in byfam["cfb"]}
    cfb_by_school = {}
    names_sorted = sorted(schools, key=lambda x: -len(x))
    for cid, nm in cfb_names.items():
        key = None
        for s in names_sorted:
            cand = ALIAS_CFB.get(s, s)
            if nm.lower().startswith(cand.lower() + " "):
                key = s
                break
        if key:
            cfb_by_school.setdefault(key, cid)
    for a, b, fa, fb_, bb, extra in COL:
        if a in cfb_by_school and b in cfb_by_school:
            add(cfb_by_school[a], cfb_by_school[b], "cfb", fa, fb_, (a, b))
        for fam in SUFFIX:
            if a in schools and b in schools and fam in schools[a] and fam in schools[b]:
                if fam in extra:
                    t = extra[fam]
                elif fam in ("cbb_m", "cbb_w"):
                    t = bb if bb != 4 else (4 if fa == 4 else min(3, fa + 1))
                else:
                    t = min(3, max(bb if bb != 4 else 3, fa if fa != 4 else 3) + 1) if fa != 4 or bb != 4 else 4
                    if fam in ("hky_m", "hky_w") and fam not in extra:
                        t = 4
                add(schools[a][fam], schools[b][fam], fam, t, t, (a, b), explicit=(fam in extra))
    out = []
    for e in edges:
        if e[0] == "UNRESOLVED":
            out.append(e)
            continue
        i, j, fam, t = e
        tt = 2 if flat else t
        out.append((i, j, fam, t, TIER_S[tt] * CLASS_FACTOR[fam], TIER_T[tt] * CLASS_FACTOR[fam]))
    if measured and not flat:
        out = apply_measured_split(out, ents, meta)
    return out


def apply_measured_split(edges, ents, meta):
    """Blend MEASURED co-search shares into how a team's prior rivalry salience is split among its rivals.

    For team i (or school) with measured shares m_ij over a rival set V, and prior salience S_ij, the row total over
    V is kept and redistributed: S_ij <- sum_V(S) * ((1-lam) * S_ij / sum_V(S) + lam * m_ij). lam comes from
    config/priors.yaml (cosearch_blend), set per league from the pilot's within-team agreement with the analyst tiers
    (docs/COSEARCH_PILOT.md), floored at 0 and capped at 0.4. Temperature T and the row totals are untouched, so the
    measurement only changes WHICH rival matters, never how much rivalry there is. Data: data/model/cosearch_pilot.csv.
    """
    path = MODEL / "cosearch_pilot.csv"
    lam_by = _PRI.get("cosearch_blend") or {}
    if not path.exists() or not lam_by:
        return edges
    by_name = {e["entity_name"]: e["entity_id"] for e in ents}
    meas = {}      # ("pro", team_id, rival_id) or ("col", school, rival_school) -> share, plus league
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            lg = r["league"]
            if lg == "col":
                meas[("col", r["team"], r["rival"])] = (lg, float(r["measured_share_among_rivals"]))
            else:
                a, b = by_name.get(r["team"]), by_name.get(r["rival"])
                if a and b:
                    meas[("pro", a, b)] = (lg, float(r["measured_share_among_rivals"]))
    groups = {}    # (row key, fam) -> list of edge indices whose rival has a measurement
    for k, e in enumerate(edges):
        if e[0] == "UNRESOLVED":
            continue
        i, j, fam = e[0], e[1], e[2]
        sch = meta.get((i, j, fam))
        key = ("col", sch[0], sch[1]) if sch else ("pro", i, j)
        if key in meas:
            groups.setdefault(((key[0], key[1]), fam), []).append((k, key))
    out = list(edges)
    for (_, fam), items in groups.items():
        lg = meas[items[0][1]][0]
        lam = max(0.0, min(0.4, float(lam_by.get(lg, 0.0))))
        if lam == 0 or len(items) < 2:
            continue
        tot_s = sum(edges[k][4] for k, _ in items)
        tot_m = sum(meas[key][1] for _, key in items)
        if tot_s <= 0 or tot_m <= 0:
            continue
        for k, key in items:
            i, j, f, t, s_, t_ = edges[k]
            new_s = tot_s * ((1 - lam) * s_ / tot_s + lam * meas[key][1] / tot_m)
            out[k] = (i, j, f, t, new_s, t_)
    return out


# ---------------------------------------------------------------- E priors
E_EXC = _PRI["e_entity_exceptions"]
E_SCHOOL = _PRI["e_school_exceptions"]
CAN = {"QC", "ON", "AB", "MB", "BC"}


def school_of(e):
    n = e["entity_name"]
    for suf in list(SUFFIX.values()) + ["Football"]:
        if n.endswith(" " + suf):
            return n[: -len(suf) - 1]
    return n


def build_E(ents, states, noise=None):
    """Return E (I x B) and bucket names. B = 50 states + DC + CAN + NATL."""
    buckets = list(states) + ["DC", "CAN", "NATL"]
    bi = {b: k for k, b in enumerate(buckets)}
    E = np.zeros((len(ents), len(buckets)))
    for r, e in enumerate(ents):
        eid, hs = e["entity_id"], e["home_state"]
        spec = E_EXC.get(eid)
        if spec is None and e["professional_college"] == "college":
            sch = school_of(e)
            if sch.endswith(" Baseball") or sch.endswith(" Softball"):
                pass
            if sch in E_SCHOOL:
                spec = E_SCHOOL[sch]
            else:
                # football names carry mascots: try matching prefix to E_SCHOOL keys
                for k, v in E_SCHOOL.items():
                    if sch.lower().startswith(k.lower() + " ") and len(sch.split()) <= len(k.split()) + 3:
                        spec = v
                        break
        if spec is None:
            tgt = "CAN" if hs in CAN else ("DC" if hs == "DC" else hs)
            spec = {tgt: 0.95}
        tot = sum(spec.values())
        for b, v in spec.items():
            if b in bi:
                E[r, bi[b]] = v
        E[r, bi["NATL"]] = max(0.0, 1.0 - tot)
    return E, buckets


# ---------------------------------------------------------------- core compute
def load_A(model_dir=None):
    with open((model_dir or MODEL) / "A_matrix.csv", newline="", encoding="utf-8") as f:
        rd = csv.reader(f)
        hdr = next(rd)
        rows = list(rd)
    states = [r[0] for r in rows]
    ents = hdr[1:-1]
    A = np.array([[float(x) for x in r[1:-1]] for r in rows])
    other = np.array([float(r[-1]) for r in rows])
    return states, ents, A, other


def build_R(ents, edges, s_noise=None, t_noise=None, cap=ROW_CAP):
    idx = {e: k for k, e in enumerate(ents)}
    n = len(ents)
    S = np.zeros((n, n))
    T = np.zeros((n, n))
    for ed in edges:
        if ed[0] == "UNRESOLVED":
            continue
        i, j, fam, tier, s, t = ed
        if i in idx and j in idx:
            S[idx[i], idx[j]] = s
            T[idx[i], idx[j]] = t
    if s_noise is not None:
        S = S * s_noise
        T = np.clip(T * t_noise, 0, 1)
    rs = S.sum(axis=1)
    scale = np.where(rs > cap, cap / np.maximum(rs, 1e-12), 1.0)
    S = S * scale[:, None]
    return S * T


PLACE_GAMMA = float(_PRI.get("place_gamma", 0.0))      # per 1,000 miles; protocol revision D-016 (see docs/RIVALRY_WEIGHT_DESIGN.md)


def place_distance(states, ids, ents):
    """Distance in thousands of miles from each state to each entity's home state (2.0 where unknown, e.g. Canada)."""
    cen = {}
    with open(CONFIG / "state_centroids.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            cen[r["state_id"]] = (math.radians(float(r["lat"])), math.radians(float(r["lon"])))

    def miles(a, b):
        (p1, l1), (p2, l2) = a, b
        h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin((l2 - l1) / 2) ** 2
        return 2 * 3958.8 * math.asin(math.sqrt(h))
    D = np.full((len(states), len(ids)), 2.0)
    for j, e in enumerate(ents):
        hs = cen.get(e["home_state"])
        if hs:
            for s, sid in enumerate(states):
                if sid in cen:
                    D[s, j] = miles(cen[sid], hs) / 1000.0
    return D


def place_matrix(states, ids, ents, gamma=None):
    """F[s, j] = exp(-gamma * miles(s, home state of entity j) / 1000): hostility from state s toward entity j shrinks with
    distance beyond what the team-level rivalry structure implies (estimated in scripts/gravity_distance.py). Entities whose home
    state is unknown (Canada) are placed 2,000 miles away. gamma = 0 gives the original model (F = 1)."""
    g = PLACE_GAMMA if gamma is None else gamma
    cen = {}
    with open(CONFIG / "state_centroids.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            cen[r["state_id"]] = (math.radians(float(r["lat"])), math.radians(float(r["lon"])))

    def miles(a, b):
        (p1, l1), (p2, l2) = a, b
        h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin((l2 - l1) / 2) ** 2
        return 2 * 3958.8 * math.asin(math.sqrt(h))
    F = np.ones((len(states), len(ids)))
    if g == 0:
        return F
    for j, e in enumerate(ents):
        hs = cen.get(e["home_state"])
        for s, sid in enumerate(states):
            d = miles(cen[sid], hs) if (hs and sid in cen) else 2000.0
            F[s, j] = math.exp(-g * d / 1000.0)
    return F


def compute_H(A, R, E, F=None):
    """H = A (S.T) E, optionally with the place factor: H[a, b] = sum_j (A R)[a, j] * F[a, j] * E[j, b]."""
    if F is None:
        return A @ (R @ E)
    return ((A @ R) * F) @ E


def pair_scores(H, states):
    """H: 50 x B (first 50 cols = states). Returns dict (a,b)->M for a<b, and M matrix."""
    n = len(states)
    Hs = H[:, :n].copy()
    np.fill_diagonal(Hs, 0.0)
    M = np.sqrt(np.maximum(Hs, 0) * np.maximum(Hs.T, 0))
    return Hs, M
