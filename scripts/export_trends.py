"""Export the Trends cache into the project (traceability requirement, docs/PROTOCOL.md section 9).

Writes
  data/raw/trends_raw.csv                 long table of every OK job response (git-ignored: raw third-party data)
  data/observations/observations.csv      derived rows, metric 'trends_ratio_to_anchor' (idempotent: old trends rows replaced)

Value = exp(ln r): the entity's regional search interest in units of the family anchor A1 (dimensionless),
after batch-rescaling in lib_trends.estimate. Zero shares are 'below_detection', never true zero (D-007).

    python scripts/export_trends.py
"""
import csv
import gzip
import io
import json
import math
import sqlite3
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import lib_trends as lt  # noqa: E402

ROOT = lt.ROOT
RAW = ROOT / "data" / "raw" / "trends_raw.csv"
OBS = ROOT / "data" / "observations" / "observations.csv"
OBS_TRENDS = ROOT / "data" / "observations" / "observations_trends.csv.gz"
PUB = "Google Trends (unofficial endpoint via pytrends; interest_by_region, REGION resolution)"
URL = "https://trends.google.com/trends/explore"
QUALITY = {"ok": "Moderate", "low_anchor": "Low", "below_detection": "Low", "anchor": "High"}
MISS = {"ok": "observed", "low_anchor": "observed", "anchor": "observed", "below_detection": "below_detection"}


def export_raw():
    con = sqlite3.connect(lt.DB, timeout=60)
    n = 0
    last = ""
    with open(RAW, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["job_key", "family", "kind", "window", "state_name", "term", "entity_id", "share_pct", "retrieved_at"])
        for key, fam, kind, win, terms, cols, payload, ts in con.execute(
                "SELECT key,family,kind,win,terms,columns,payload,ts FROM jobs WHERE status='ok' ORDER BY key"):
            p = json.loads(payload)
            t2id = dict(zip(json.loads(terms), json.loads(cols)))
            for state, vals in p["rows"].items():
                for term, v in zip(p["columns"], vals):
                    w.writerow([key, fam, kind, win, state, term, t2id.get(term, ""), v, ts])
                    n += 1
            last = max(last, ts or "")
    con.close()
    return n, last[:10]


def export_obs(retrieved):
    jobs = [j for j in lt.load_jobs() if j["family"] != "TOPDOWN"]
    smap = lt.state_map()
    est = {}
    anchors = {}
    for fam in sorted({j["family"] for j in jobs}):
        fj = [j for j in jobs if j["family"] == fam]
        anchors[fam] = fj[0]["names"][0]
        est.update(lt.estimate(fj, smap))
    fam_of = {}
    for j in jobs:
        for nme in j["names"]:
            fam_of.setdefault(nme, j["family"])
    with open(OBS, newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        cols = rd.fieldnames
        rows = [r for r in rd if not r["metric"].startswith("trends_")]
    new = []
    for (name, sid, win), (ln, var, flag) in sorted(est.items()):
        new.append({
            "observation_id": f"TRENDS_{len(new) + 1:06d}", "entity_id": name, "state_id": sid,
            "metric": "trends_ratio_to_anchor", "value": f"{math.exp(ln):.6g}", "unit": "ratio_to_family_anchor",
            "source_url": URL, "publisher": PUB, "publication_date": retrieved,
            "measurement_window": win, "geography": "US state", "sample_size": "",
            "quality_class": QUALITY[flag], "missingness_type": MISS[flag], "retrieved_at": retrieved,
            "notes": f"anchor={anchors.get(fam_of.get(name, ''), '')}; ln_var={var:.4g}; flag={flag}"})
    with open(OBS, "w", newline="", encoding="utf-8") as f:       # non-Trends observations only (small)
        wr = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
        wr.writeheader()
        wr.writerows(rows)
    # Trends-derived observations are large (hundreds of thousands of rows), so they live in a gzip file of their own
    # (deterministic: no timestamp) to stay far below GitHub's 100 MB file limit.
    buf = io.StringIO()
    wr = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    wr.writeheader()
    wr.writerows(new)
    with open(OBS_TRENDS, "wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
        gz.write(buf.getvalue().encode("utf-8"))
    return len(new)


if __name__ == "__main__":
    n, retrieved = export_raw()
    m = export_obs(retrieved)
    print(f"trends_raw.csv: {n} rows; observations: +{m} trends rows (retrieved {retrieved})")
