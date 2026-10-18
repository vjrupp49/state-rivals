"""Phase 4B steps 8-10, 14: anchored Trends -> G^C / G^P -> within-sport P_si|k.

P-tilde = P_G^(1-g) * P_C^g  (docs/PROTOCOL.md section 8; gamma weights are PROVISIONAL
per D-012: g=0.2 default, 0.1 for the older NHL map and state-level WNBA map).
Where only one source exists the other is dropped and the remaining one is
renormalized (never inserting zero). Entities with neither source are imputed
at a floor and flagged Low confidence with wide uncertainty.

Output: data/model/attention_team.csv
"""
import csv
import math
import sys
import pathlib
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import lib_trends as L

ROOT = L.ROOT
OUT = ROOT / "data" / "model" / "attention_team.csv"
GAMMA_C = {"nhl": 0.1, "wnba": 0.1}
DEFAULT_GAMMA_C = 0.2
C_FLOOR = 0.02
EPS = 1e-4
C_FAMILIES = {"nfl", "mlb", "nba", "mls", "nhl", "wnba", "cfb"}
GAMMA_OVERRIDE = {}


def load_entities():
    with open(ROOT / "data" / "registries" / "entities.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    fams = defaultdict(list)
    for r in rows:
        fams[fam_of(r["entity_id"])].append(r)
    return fams


def fam_of(eid):
    p = eid.split("_")
    return "_".join(p[:2]) if p[0] in ("cbb", "hky") else p[0]


def load_C():
    C = {}
    with open(ROOT / "data" / "observations" / "observations.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["metric"] == "county_plurality_pop_share":
                C[(r["state_id"], r["entity_id"])] = float(r["value"])
    return C


def main(gamma_c_scale=1.0, out=OUT, window='P', quiet=False):
    smap = L.state_map()
    fams = load_entities()
    C = load_C()
    rows = []
    cover = {}
    for fam, ents in fams.items():
        jobs = L.load_jobs(family=fam)
        est = L.estimate(jobs, smap) if jobs else {}
        ids = [e["entity_id"] for e in ents]
        n_cov = 0
        for sid in smap.values():
            G = {i: L.blend_windows(est, i, sid) for i in ids}
            gs = {i: g for i, g in G.items() if g["G_P"] is not None or g["G_C"] is not None}
            n_cov += len(gs)
            tot_gc = sum(g["G_C"] for g in gs.values() if g["G_C"] is not None) or None
            tot_gp = sum(g["G_P"] for g in gs.values() if g["G_P"] is not None) or None
            have_c = fam in C_FAMILIES
            cp = {i: max(C.get((sid, i), 0.0), C_FLOOR) for i in ids} if have_c else {}
            tot_c = sum(cp.values()) if have_c else None
            g_c = GAMMA_C.get(fam, DEFAULT_GAMMA_C) * gamma_c_scale
            # partial Trends coverage: keep the covered subset's total mass equal to its county-signal mass,
            # so covered and uncovered entities stay on one scale instead of covered ones inflating
            sub = [i for i in ids if i in gs]
            sub_scale = 1.0
            if have_c and tot_c and 0 < len(sub) < len(ids):
                sub_scale = sum(cp[i] for i in sub) / tot_c
            tilde, meta = {}, {}
            for i in ids:
                g = G[i]
                # primary Google signal: blend persistent (70%) and current (30%)? keep simple: persistent baseline
                pg = None
                if window == "C" and g["G_C"] is not None and tot_gc:
                    pg = g["G_C"] / tot_gc
                elif window == "P" and g["G_P"] is not None and tot_gp:
                    pg = g["G_P"] / tot_gp
                pc = cp[i] / tot_c if have_c and tot_c else None
                if pg is not None and sub_scale != 1.0:
                    pg = pg * sub_scale
                if pg is not None and pc is not None:
                    t = math.exp((1 - g_c) * math.log(pg) + g_c * math.log(pc))
                    disagree = abs(math.log(pg / pc))
                elif pg is not None:
                    t, disagree = pg, None
                elif pc is not None:
                    t, disagree = pc, None
                else:
                    t, disagree = EPS, None
                tilde[i] = t
                var = g["var_C"] if g["var_C"] is not None else 2.0
                flag = g["flag_C"]
                if pg is None and pc is None:
                    conf, flag, sd = "Low", "imputed", 1.5
                elif pg is None:
                    conf, flag, sd = "Low", "county_only", 1.0
                else:
                    sd = max(math.sqrt(var), 0.15)
                    if disagree is not None:
                        sd = math.sqrt(sd ** 2 + (0.5 * disagree) ** 2)
                    if flag in ("below_detection", "low_anchor", "missing"):
                        conf = "Low"
                        sd = max(sd, 0.8) if flag == "below_detection" else max(sd, 0.5)
                    elif pc is not None and disagree is not None and disagree < math.log(3):
                        conf = "High"
                    else:
                        conf = "Moderate"
                meta[i] = (g, pc, conf, flag, sd)
            tot = sum(tilde.values())
            for i in ids:
                g, pc, conf, flag, sd = meta[i]
                rows.append({
                    "state_id": sid, "family": fam, "entity_id": i,
                    "P": tilde[i] / tot, "G_C": g["G_C"] if g["G_C"] is not None else "",
                    "G_P": g["G_P"] if g["G_P"] is not None else "",
                    "C_si": C.get((sid, i), "") if fam in C_FAMILIES else "",
                    "confidence": conf, "logsd": round(sd, 3), "flag": flag,
                })
        cover[fam] = (len(ids), n_cov)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    if quiet:
        return cover
    print(f"wrote {len(rows)} rows -> {out}")
    for fam, (n_ent, n_cov) in cover.items():
        print(f"  {fam}: entities={n_ent} entity-state cells with Trends={n_cov}/{n_ent * 50}")


if __name__ == "__main__":
    main()
