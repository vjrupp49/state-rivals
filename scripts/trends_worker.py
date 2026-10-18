"""Phase 4B steps 6-8 worker: resolve Google Trends topics, then pull anchored
interest_by_region batches for every registry entity (and sport-level terms).

Design (validated by Gate 1 on 2026-10-08): interest_by_region returns, per US
state, each of up to 5 terms as an integer percent SHARE of the 5 terms
within that state (rows sum to ~100). Ratios between terms inside a batch
are therefore batch-invariant, so two anchor terms are included in every
batch and later used to put all batches of a family on one scale
(see build_P_from_trends.py).

Resumable and idempotent: every request is cached in SQLite under
%LOCALAPPDATA%/StateRivals/work (kept OUT of OneDrive on purpose). Safe to
kill and restart at any time. Backs off on rate limits and never tries to
evade a block -- it just waits.

    python scripts/trends_worker.py            # run until done / pull-stop
    python scripts/trends_worker.py --status   # print progress and exit
    python scripts/trends_worker.py --only nfl,mlb --max-jobs 5   # test
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import pathlib
import random
import sqlite3
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
from paths import WORK
WORK.mkdir(parents=True, exist_ok=True)
DB_PATH = WORK / "trends.sqlite"
STATE_PATH = WORK / "STATE.json"
LOG_PATH = WORK / "worker.log"
MIRROR_PATH = ROOT / "logs" / "STATE_mirror.json"
ENTITIES = ROOT / "data" / "registries" / "entities.csv"

PULL_STOP = dt.datetime.fromisoformat(os.environ.get("SR_PULL_STOP", "2026-10-25T00:00:00"))
TODAY = dt.date(2026, 10, 8)

# (label, timeframe) newest first. Half-life weighting is applied downstream.
WINDOWS = [
    ("W0", "2025-10-08 2026-10-08"),
    ("W1", "2024-10-08 2025-10-08"),
    ("W2", "2023-10-08 2024-10-08"),
    ("W3", "2021-10-08 2023-10-08"),
]

WINDOW_5Y = ("W5", "2021-10-08 2026-10-08")
TIER_A = {"nfl", "mlb", "nba", "nhl", "mls", "wnba", "nwsl", "pwhl", "cfb"}   # 4 windows; others get W0 + W5
BASE_PACE = 60.0

ANCHORS = {
    "nfl": ["nfl_cowboys", "nfl_chiefs"], "mlb": ["mlb_yankees", "mlb_dodgers"],
    "nba": ["nba_lakers", "nba_warriors"], "nhl": ["nhl_blackhawks", "nhl_penguins"],
    "mls": ["mls_miami", "mls_seattle"], "wnba": ["wnba_fever", "wnba_liberty"],
    "nwsl": ["nwsl_portlandthorns", "nwsl_angelcity"], "pwhl": ["pwhl_minnesota", "pwhl_toronto"],
    "cfb": ["cfb_alabama_crimson_tide", "cfb_ohio_state_buckeyes"],
    "cbb_m": ["cbb_m_duke", "cbb_m_kentucky"], "cbb_w": ["cbb_w_uconn", "cbb_w_iowa"],
    "hky_m": ["hky_m_minnesota", "hky_m_michigan"], "hky_w": ["hky_w_wisconsin", "hky_w_minnesota"],
    "bsb": ["bsb_lsu", "bsb_texas"], "sfb": ["sfb_oklahoma", "sfb_florida"],
    "vbw": ["vbw_nebraska", "vbw_wisconsin"], "lax": ["lax_m_maryland", "lax_m_duke"], "wrs": ["wrs_iowa", "wrs_penn_state"],
}
COS_ANCHORS = {"nfl": ["Packers vs Bears", "Cowboys vs Eagles"], "mlb": ["Yankees vs Red Sox", "Dodgers vs Giants"],
               "nba": ["Lakers vs Celtics", "Warriors vs Lakers"], "nhl": ["Bruins vs Canadiens", "Blackhawks vs Red Wings"],
               "col": ["Ohio State vs Michigan", "Alabama vs Auburn"]}


def _cap(w):
    return w if w[:1].isdigit() else w.capitalize()


def _cosearch_pairs(league):
    """Unordered curated rivalry pairs of a pro league as 'A vs B' terms (order: strongest tiers first)."""
    import yaml
    cur = yaml.safe_load(open(ROOT / "config" / "rivalry_curated.yaml", encoding="utf-8"))
    if league == "col":    # college: school-level pairs, hottest football/basketball tier first
        rows = sorted(cur["college"], key=lambda r: min(r[2], r[3], r[4]))
        rows = [(a, b, 0, 0) for a, b, *_ in rows]
        out = []
        for a, b, _, _ in rows:
            t = f"{a} vs {b}"
            if t not in out:
                out.append(t)
        return [t for t in COS_ANCHORS[league] if t not in out] + out
    rows = sorted(cur["pro"][league], key=lambda r: min(r[2], r[3]))
    out = []
    for a, b, _, _ in rows:
        t = " ".join(_cap(x) for x in a.split()) + " vs " + " ".join(_cap(x) for x in b.split())
        if t not in out:
            out.append(t)
    return [t for t in COS_ANCHORS[league] if t not in out] + out


HATE_ANCHORS = {"nfl": ["Cowboys suck", "Patriots suck"], "mlb": ["Yankees suck", "Red Sox suck"],
                "nba": ["Lakers suck", "Celtics suck"], "nhl": ["Bruins suck", "Maple Leafs suck"], "cfb": ["Alabama sucks", "Ohio State sucks"], "sch": ["Duke sucks", "Kentucky sucks"]}
_POOL = ("nfl", "mlb", "nba", "nhl", "mls")


# schools outside FBS football whose peak state attention clears the 0.25% active-universe bar (computed 2026-10-16)
EXTRA_SCHOOLS = ["Marquette", "Brown", "Dartmouth", "Denver", "Yale", "Cornell"]
BRIDGE_TERMS = {"mlb": "Yankees suck", "nba": "Lakers suck", "nhl": "Bruins suck", "cfb": "Ohio State sucks"}   # league anchor bridged to Cowboys


def _hate_terms_cfb():
    """'<School> sucks' for FBS programs; school = longest prefix of the entity name that is a D-I basketball school name."""
    ents = list(csv.DictReader(open(ENTITIES, newline="", encoding="utf-8")))
    schools = sorted({e["entity_name"].replace(" Men's Basketball", "") for e in ents if e["entity_id"].startswith("cbb_m_")}, key=lambda x: -len(x))
    out = {}
    for e in ents:
        if not e["entity_id"].startswith("cfb_") or e["level"] != "FBS":
            continue
        nm = e["entity_name"].replace(" Football", "")
        sch = next((x for x in schools if nm.startswith(x + " ") or nm == x), " ".join(nm.split()[:-1]) or nm)
        out[e["entity_id"]] = sch + " sucks"
    return out


def _hate_terms(league):
    """'<nickname> suck' per team of a pro league; the full 'City Nickname suck' where the nickname is shared
    across leagues (Giants, Jets, Kings, Rangers, Cardinals, Panthers, ...). Returns {entity_id: term}."""
    ents = [e for e in csv.DictReader(open(ENTITIES, newline="", encoding="utf-8")) if family_of(e["entity_id"]) in _POOL]
    nick = {}
    for e in ents:
        nick[e["entity_id"]] = e["entity_name"].split()[-1] if e["entity_name"].split()[-1].lower() not in ("sox", "leafs", "jackets", "knights", "wings", "jays") else " ".join(e["entity_name"].split()[-2:])
    from collections import Counter
    cnt = Counter(nick.values())
    out = {}
    for e in ents:
        if family_of(e["entity_id"]) != league:
            continue
        n = nick[e["entity_id"]]
        out[e["entity_id"]] = (e["entity_name"] if cnt[n] > 1 else n) + " suck"
    return out


FAMILY_ORDER = ["nfl", "mlb", "nba", "nhl", "mls", "wnba", "nwsl", "pwhl", "SPORT",
                "cfb", "cbb_m", "cbb_w", "hky_m", "hky_w", "bsb", "sfb", "vbw", "wrs", "lax", "COS_nfl", "COS_mlb", "COS_nba", "COS_nhl", "COS_col", "COSB_mlb", "COSB_nba", "COSB_nhl", "HATE_nfl", "HATE_mlb", "HATE_nba", "HATE_nhl", "BRIDGE_mlb", "BRIDGE_nba", "BRIDGE_nhl", "BRIDGE_cfb", "HATE_cfb", "HATE_sch", "TOPDOWN"]

# Sport-level (W_sk) batches: NFL + MLB anchor every batch.
SPORT_BATCHES = [
    ["NFL", "MLB", "college football", "NBA", "men's college basketball"],
    ["NFL", "MLB", "NHL", "MLS", "WNBA"],
    ["NFL", "MLB", "NWSL", "PWHL", "men's college hockey"],
    ["NFL", "MLB", "women's college hockey", "college baseball", "college softball"],
    ["NFL", "MLB", "women's college basketball", "college volleyball", "college wrestling"],
    ["NFL", "MLB", "lacrosse", "college volleyball", "college wrestling"],
    # topic-based terms (review finding: literal phrases such as "men's college basketball" gave college sports almost no weight).
    # Topic ids resolved with the suggestions endpoint on 2026-10-16; same NFL and MLB anchors so the scale carries over.
    ["NFL", "MLB", "/m/01zff", "/m/02jp2w", "/m/04xc_d"],            # college football, men's basketball tournament, college baseball
    ["NFL", "MLB", "/g/11dxbvlspv", "/m/05v_4b", "/m/0wxw0fp"],      # D-I women's basketball, college softball, women's volleyball tournament
    ["NFL", "MLB", "/m/05gvj2", "/m/02qdfyt", "/g/11spflhcxj"],      # D-I wrestling championships, college lacrosse, men's ice hockey tournament
    ["NFL", "MLB", "/m/02p5ty", "/m/0wxw0fp", "/m/05gvj2"],          # women's ice hockey tournament (again with volleyball and wrestling as cross-checks)
]

SPORT_WORD = {"cfb": "football", "nfl": "football", "mlb": "baseball", "bsb": "baseball",
              "nba": "basketball", "wnba": "basketball", "cbb_m": "basketball",
              "cbb_w": "basketball", "nhl": "hockey", "hky_m": "hockey", "hky_w": "hockey",
              "pwhl": "hockey", "mls": "soccer", "nwsl": "soccer", "sfb": "softball",
              "vbw": "volleyball", "lax": "lacrosse", "wrs": "wrestling"}


def log(msg):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')} {msg}"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)


def family_of(entity_id):
    p = entity_id.split("_")
    return "_".join(p[:2]) if p[0] in ("cbb", "hky") else p[0]


def db():
    con = sqlite3.connect(DB_PATH, timeout=60)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("""CREATE TABLE IF NOT EXISTS sugg(entity_id TEXT PRIMARY KEY, query TEXT, mid TEXT,
                   title TEXT, type TEXT, status TEXT, ts TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS jobs(key TEXT PRIMARY KEY, family TEXT, kind TEXT, win TEXT,
                   terms TEXT, columns TEXT, payload TEXT, status TEXT, attempts INTEGER DEFAULT 0, ts TEXT)""")
    return con


def backoff_for(n):
    return {1: 1200}.get(n, 1800)


def pid_alive(pid):
    try:
        import ctypes
        h = ctypes.windll.kernel32.OpenProcess(0x1000, False, int(pid))
        if not h:
            return False
        code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(h)
        return code.value == 259
    except Exception:
        return True


def keep_awake():
    if os.environ.get("SR_KEEP_AWAKE") != "1":
        return
    try:
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)
    except Exception as e:
        log(f"keep_awake unavailable: {e}")


class Worker:
    def __init__(self, only=None, max_jobs=None):
        self.con = db()
        self.only = set(only) if only else None
        self.max_jobs = max_jobs
        self.pace = BASE_PACE
        self.consec_fail = 0
        self.ok_streak = 0
        self.jobs_run = 0
        self.last_error = ""
        self.started = dt.datetime.now().isoformat(timespec="seconds")
        self.phase = "init"
        self.family = ""
        self._py = None
        self._last_mirror = 0
        self.last_fail_epoch = 0.0

    # ---------- pytrends plumbing ----------
    def py(self, fresh=False):
        from pytrends.request import TrendReq
        if self._py is None or fresh:
            self._py = TrendReq(hl="en-US", tz=360, timeout=(10, 30))
        return self._py

    def wait(self, secs):
        end = time.time() + secs
        while time.time() < end:
            time.sleep(min(30, max(0.5, end - time.time())))
            self.heartbeat()
            if dt.datetime.now() >= PULL_STOP:
                return

    def call(self, fn, pace=None, soft=False):
        """Run a Trends call with adaptive pacing / backoff. Returns result or None."""
        while dt.datetime.now() < PULL_STOP:
            try:
                res = fn()
                self.consec_fail = 0
                self._5xx = 0
                self.ok_streak += 1
                self.heartbeat()
                if self.ok_streak >= 40 and self.pace > BASE_PACE:
                    self.pace = max(BASE_PACE, self.pace * 0.85)
                    self.ok_streak = 0
                time.sleep((pace if pace else self.pace) + random.uniform(0, 1.0))
                return res
            except Exception as e:
                msg = str(e)[:200]
                if soft and ("404" in msg or "400" in msg):
                    return "SOFTFAIL"
                if ("code 500" in msg or "code 502" in msg or "code 503" in msg) and getattr(self, "_5xx", 0) < 6:
                    self._5xx = getattr(self, "_5xx", 0) + 1
                    log(f"transient server error ({msg[:60]}); retry {self._5xx}/6 in 60s")
                    self._py = None
                    self.wait(60)
                    continue
                net = ("NameResolutionError" in msg or "Max retries exceeded" in msg or "Failed to resolve" in msg
                       or "Connection aborted" in msg or "timed out" in msg or "ConnectionError" in msg)
                if net and "429" not in msg:
                    # our own network is down (travel, wifi): not a Google block, so do not escalate the throttle streak
                    log(f"network unavailable ({msg[:60]}); retry in 120s")
                    self._py = None
                    self.wait(120)
                    continue
                self.last_error = msg
                self.consec_fail += 1
                self.ok_streak = 0
                is429 = "429" in msg or "Too" in msg
                if is429:
                    self.pace = min(max(BASE_PACE, 15.0) * 2, self.pace * 1.5)
                back = backoff_for(self.consec_fail) + random.uniform(0, 30)
                self.last_fail_epoch = time.time()
                log(f"BLOCK/ERR #{self.consec_fail} ({msg[:80]}) pace={self.pace:.1f}s sleeping {back:.0f}s")
                self._py = None
                self.wait(back)
        return None

    # ---------- topic resolution ----------
    def load_entities(self):
        with open(ENTITIES, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def resolve(self, ent):
        row = self.con.execute("SELECT mid,status FROM sugg WHERE entity_id=?", (ent["entity_id"],)).fetchone()
        if row:
            return
        fam = family_of(ent["entity_id"])
        q = ent["entity_name"]
        qq = q.replace("/", " ")
        res = self.call(lambda: self.py().suggestions(qq), pace=6.0, soft=True)
        if res is None:
            return
        if res == "SOFTFAIL":
            self.con.execute("INSERT OR REPLACE INTO sugg VALUES(?,?,?,?,?,?,?)",
                             (ent["entity_id"], q, "", "", "", "term_fallback", dt.datetime.now().isoformat()))
            self.con.commit()
            return
        want_w = "women" in q.lower()
        school_tok = q.split()[0].lower()
        sw = SPORT_WORD.get(fam, "")
        pick = None
        for c in res[:6]:
            t, ty = c.get("title", "").lower(), c.get("type", "").lower()
            if not ("team" in ty or "club" in ty):
                continue
            if sw and sw not in t and sw not in ty:
                continue
            if fam in ("cbb_m", "cbb_w", "hky_m", "hky_w", "lax"):
                if want_w != ("women" in t):
                    continue
            if school_tok not in t and fam not in ("cbb_m", "cbb_w", "hky_m", "hky_w"):
                continue
            pick = c
            break
        if pick:
            self.con.execute("INSERT OR REPLACE INTO sugg VALUES(?,?,?,?,?,?,?)",
                             (ent["entity_id"], q, pick["mid"], pick["title"], pick["type"], "topic",
                              dt.datetime.now().isoformat()))
        else:
            self.con.execute("INSERT OR REPLACE INTO sugg VALUES(?,?,?,?,?,?,?)",
                             (ent["entity_id"], q, "", "", "", "term_fallback", dt.datetime.now().isoformat()))
        self.con.commit()

    def term_for(self, ent):
        row = self.con.execute("SELECT mid,status FROM sugg WHERE entity_id=?", (ent["entity_id"],)).fetchone()
        if row and row[1] == "topic" and row[0]:
            return row[0]
        return ent["entity_name"]

    # ---------- planning ----------
    def plan_family(self, fam, ents, wins):
        """Plan only entities not already covered by an OK job in the same window; higher tiers first
        (FBS before FCS before D-II) so family coverage crosses 50% as early as possible."""
        rank = {"FBS": 0, "FCS": 1, "D-II": 2}
        by_id = {e["entity_id"]: e for e in ents}
        anchors = ANCHORS[fam]
        n = 0
        for wl, tf in wins:
            covered = set()
            for (cj,) in self.con.execute("SELECT columns FROM jobs WHERE family=? AND win=? AND status='ok'", (fam, wl)):
                covered.update(json.loads(cj))
            self.con.execute("DELETE FROM jobs WHERE family=? AND win=? AND status='pending'", (fam, wl))
            todo = sorted((i for i in by_id if i not in anchors and i not in covered),
                          key=lambda i: (rank.get(by_id[i]["level"], 0), i))
            if not covered:
                todo = sorted((i for i in by_id if i not in anchors), key=lambda i: (rank.get(by_id[i]["level"], 0), i))
            for k in range(0, len(todo), 3):
                b = anchors + todo[k:k + 3]
                terms = [self.term_for(by_id[i]) for i in b]
                key = hashlib.sha1(json.dumps([terms, tf]).encode()).hexdigest()
                self.con.execute("INSERT OR IGNORE INTO jobs(key,family,kind,win,terms,columns,status,ts) VALUES(?,?,?,?,?,?,?,?)",
                                 (key, fam, "entities", wl, json.dumps(terms), json.dumps(b), "pending", dt.datetime.now().isoformat()))
                n += 1
        self.con.commit()
        return n

    def plan_sport(self, wins):
        for b in SPORT_BATCHES:
            for wl, tf in wins:
                key = hashlib.sha1(json.dumps([b, tf]).encode()).hexdigest()
                self.con.execute("INSERT OR IGNORE INTO jobs(key,family,kind,win,terms,columns,status,ts) VALUES(?,?,?,?,?,?,?,?)",
                                 (key, "SPORT", "sport", wl, json.dumps(b), json.dumps(b), "pending", dt.datetime.now().isoformat()))
        self.con.commit()

    def plan_topdown(self):
        """Independent top-down signal: state-vs-state 'X sucks' searches (docs/PROTOCOL.md section 11, Phase 9)."""
        with open(ROOT / "data" / "registries" / "states.csv", newline="", encoding="utf-8") as f:
            names = [r["state_name"] for r in csv.DictReader(f) if r["is_contest_state"] == "TRUE"]
        terms = [f"{n} sucks" for n in names]
        anchors = ["California sucks", "Texas sucks"]
        rest = [t for t in terms if t not in anchors]
        for i in range(0, len(rest), 3):
            b = anchors + rest[i:i + 3]
            key = hashlib.sha1(json.dumps([b, WINDOW_5Y[1]]).encode()).hexdigest()
            self.con.execute("INSERT OR IGNORE INTO jobs(key,family,kind,win,terms,columns,status,ts) VALUES(?,?,?,?,?,?,?,?)",
                             (key, "TOPDOWN", "topdown", "W5", json.dumps(b), json.dumps(b), "pending", dt.datetime.now().isoformat()))
        self.con.commit()

    def plan_cosearch(self, fam_key):
        """M3 pilot: co-search interest for curated rivalry pairs ("Bears vs Packers"), 5-year window, by state.
        Terms are plain strings (no topic lookup). Two anchor pairs per batch put batches on one scale per league."""
        league = fam_key[4:]
        pairs = _cosearch_pairs(league)
        anchors = COS_ANCHORS[league]
        rest = [t for t in pairs if t not in anchors]
        n = 0
        for i in range(0, len(rest), 3):
            b = anchors + rest[i:i + 3]
            key = hashlib.sha1(json.dumps([b, WINDOW_5Y[1]]).encode()).hexdigest()
            self.con.execute("INSERT OR IGNORE INTO jobs(key,family,kind,win,terms,columns,status,ts) VALUES(?,?,?,?,?,?,?,?)",
                             (key, fam_key, "cosearch", "W5", json.dumps(b), json.dumps(b), "pending", dt.datetime.now().isoformat()))
            n += 1
        self.con.commit()
        return n

    def plan_cosbridge(self, fam_key):
        """Two-term bridge for co-search shares: [NFL anchor pair, league anchor pair]. Puts each league's co-search scale on the NFL one."""
        b = [COS_ANCHORS["nfl"][0], COS_ANCHORS[fam_key[5:]][0]]
        key = hashlib.sha1(json.dumps([b, WINDOW_5Y[1]]).encode()).hexdigest()
        self.con.execute("INSERT OR IGNORE INTO jobs(key,family,kind,win,terms,columns,status,ts) VALUES(?,?,?,?,?,?,?,?)",
                         (key, fam_key, "cosbridge", "W5", json.dumps(b), json.dumps(b), "pending", dt.datetime.now().isoformat()))
        self.con.commit()
        return 1

    def plan_bridge(self, fam_key):
        """Two-term bridge batch [Cowboys suck, <league anchor>]: a pair of similar volume resolves far better than one
        five-term batch dominated by the biggest term. Gives each league's anchor in units of 'Cowboys suck' per state."""
        term = BRIDGE_TERMS[fam_key[7:]]
        b = ["Cowboys suck", term]
        key = hashlib.sha1(json.dumps([b, WINDOW_5Y[1]]).encode()).hexdigest()
        self.con.execute("INSERT OR IGNORE INTO jobs(key,family,kind,win,terms,columns,status,ts) VALUES(?,?,?,?,?,?,?,?)",
                         (key, fam_key, "bridge", "W5", json.dumps(b), json.dumps(b), "pending", dt.datetime.now().isoformat()))
        self.con.commit()
        return 1

    def plan_hate(self, fam_key):
        """M3: team-level antipathy searches ('Packers suck') by state, W5. Within one state the anchor cancels, so the
        values give each state's relative hostility across teams: a direct, independent measure of H toward each team."""
        league = fam_key[5:]
        terms = _hate_terms_cfb() if league == "cfb" else ({x: x + " sucks" for x in EXTRA_SCHOOLS} if league == "sch" else _hate_terms(league))
        anchors = HATE_ANCHORS[league]
        rest = [t for t in terms.values() if t not in anchors]
        n = 0
        for i in range(0, len(rest), 3):
            b = anchors + rest[i:i + 3]
            key = hashlib.sha1(json.dumps([b, WINDOW_5Y[1]]).encode()).hexdigest()
            self.con.execute("INSERT OR IGNORE INTO jobs(key,family,kind,win,terms,columns,status,ts) VALUES(?,?,?,?,?,?,?,?)",
                             (key, fam_key, "hate", "W5", json.dumps(b), json.dumps(b), "pending", dt.datetime.now().isoformat()))
            n += 1
        self.con.commit()
        return n

    # ---------- execution ----------
    def run_family_jobs(self, fam, win_labels=None):
        tf = dict(WINDOWS + [WINDOW_5Y])
        wl = win_labels or ["W0", "W1", "W2", "W3", "W5"]
        q = "SELECT key,win,terms,columns,attempts FROM jobs WHERE family=? AND status='pending' AND win IN (%s) ORDER BY win, key" % ",".join("?" * len(wl))
        rows = self.con.execute(q, [fam] + wl).fetchall()
        for key, win, terms_j, cols_j, attempts in rows:
            if dt.datetime.now() >= PULL_STOP:
                return False
            if self.max_jobs is not None and self.jobs_run >= self.max_jobs:
                return False
            terms = json.loads(terms_j)

            def fn():
                p = self.py()
                p.build_payload(terms, cat=0, timeframe=tf[win], geo="US")
                df = p.interest_by_region(resolution="REGION", inc_low_vol=True, inc_geo_code=False)
                return {str(i): [int(df.loc[i, c]) for c in df.columns] for i in df.index}, list(df.columns)

            res = self.call(fn)
            if res is None:
                return False
            payload, cols = res
            if cols != terms:
                log(f"WARN column order differs for {key[:8]}: {cols} vs {terms}")
            self.con.execute("UPDATE jobs SET payload=?, status='ok', attempts=?, ts=? WHERE key=?",
                             (json.dumps({"columns": cols, "rows": payload}), attempts + 1, dt.datetime.now().isoformat(), key))
            self.con.commit()
            self.jobs_run += 1
            self.heartbeat()
            if self.jobs_run % 25 == 0:
                log(f"PROGRESS {self.progress_str()}")
        return True

    def progress(self):
        tot = self.con.execute("SELECT count(*) FROM jobs").fetchone()[0]
        ok = self.con.execute("SELECT count(*) FROM jobs WHERE status='ok'").fetchone()[0]
        return ok, tot

    def progress_str(self):
        ok, tot = self.progress()
        return f"family={self.family} jobs_ok={ok}/{tot} pace={self.pace:.1f}s"

    def heartbeat(self, force=False):
        ok, tot = self.progress()
        st = {"ts": dt.datetime.now().isoformat(timespec="seconds"), "phase": self.phase, "family": self.family,
              "jobs_ok": ok, "jobs_planned": tot, "pace_s": round(self.pace, 2), "consec_fail": self.consec_fail,
              "last_error": self.last_error, "started": self.started, "pull_stop": PULL_STOP.isoformat(),
              "pid": os.getpid(), "last_fail_epoch": self.last_fail_epoch}
        STATE_PATH.write_text(json.dumps(st, indent=1), encoding="utf-8")
        if force or time.time() - self._last_mirror > 600:
            try:
                MIRROR_PATH.parent.mkdir(exist_ok=True)
                MIRROR_PATH.write_text(json.dumps(st, indent=1), encoding="utf-8")
                self._last_mirror = time.time()
            except Exception:
                pass

    def run(self):
        lock = WORK / "worker.pid"
        try:
            old = int(lock.read_text().strip())
            if old != os.getpid() and pid_alive(old):
                log(f"another worker (pid {old}) is alive; exiting")
                return
        except Exception:
            pass
        lock.write_text(str(os.getpid()))
        try:
            prev = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            if prev.get("consec_fail", 0) > 0 and time.time() - prev.get("last_fail_epoch", 0) < 4 * 3600:
                self.consec_fail = prev["consec_fail"]
                self.last_fail_epoch = prev["last_fail_epoch"]
                wait_s = backoff_for(self.consec_fail) - (time.time() - self.last_fail_epoch)
                if wait_s > 0:
                    log(f"resuming block streak #{self.consec_fail}; waiting {wait_s:.0f}s before the next probe")
                    self.wait(wait_s)
        except Exception:
            pass
        keep_awake()
        ents = self.load_entities()
        fams = {}
        for e in ents:
            fams.setdefault(family_of(e["entity_id"]), []).append(e)
        log(f"MILESTONE worker start pid={os.getpid()} pull_stop={PULL_STOP} entities={len(ents)}")
        pass1 = ["SPORT", "nfl", "mlb", "nba", "nhl", "mls", "wnba", "nwsl", "pwhl", "hky_m", "hky_w", "TOPDOWN",
                 "cfb", "bsb", "cbb_m", "sfb", "cbb_w", "COS_nfl", "COS_mlb", "COS_nba", "COS_nhl", "COS_col", "COSB_mlb", "COSB_nba", "COSB_nhl", "HATE_nfl", "HATE_mlb", "HATE_nba", "HATE_nhl", "BRIDGE_mlb", "BRIDGE_nba", "BRIDGE_nhl", "BRIDGE_cfb", "HATE_cfb", "HATE_sch", "vbw", "wrs", "lax"]
        pass2 = pass1 + []
        pass3 = ["SPORT", "nfl", "mlb", "nba", "nhl", "mls", "wnba", "nwsl", "pwhl", "cfb"]
        stop = False
        for pno, order, wins in ((1, pass1, [WINDOWS[0]]), (2, pass2, [WINDOW_5Y]), (3, pass3, WINDOWS[1:])):
            for fam in order:
                if self.only and fam not in self.only:
                    continue
                if dt.datetime.now() >= PULL_STOP:
                    stop = True
                    break
                self.family = fam
                if fam == "SPORT":
                    self.phase = f"p{pno}:sport_level"
                    self.plan_sport(wins)
                elif fam == "TOPDOWN":
                    self.phase = "topdown"
                    self.plan_topdown()
                elif fam.startswith("COS_"):
                    if pno != 1:
                        continue          # co-search is a one-window (W5) pilot; plan and run it once, in pass 1
                    self.phase = f"cosearch:{fam}"
                    log(f"MILESTONE planned {fam}: {self.plan_cosearch(fam)} jobs")
                elif fam.startswith("COSB_"):
                    if pno != 1:
                        continue
                    self.phase = f"cosbridge:{fam}"
                    log(f"MILESTONE planned {fam}: {self.plan_cosbridge(fam)} jobs")
                elif fam.startswith("BRIDGE_"):
                    if pno != 1:
                        continue
                    self.phase = "bridge"
                    log(f"MILESTONE planned {fam}: {self.plan_bridge(fam)} jobs")
                elif fam.startswith("HATE_"):
                    if pno != 1:
                        continue
                    self.phase = f"hate:{fam}"
                    log(f"MILESTONE planned {fam}: {self.plan_hate(fam)} jobs")
                else:
                    self.phase = f"p{pno}:resolve:{fam}"
                    for e in fams.get(fam, []):
                        if dt.datetime.now() >= PULL_STOP:
                            break
                        self.resolve(e)
                    self.phase = f"p{pno}:pull:{fam}"
                    n = self.plan_family(fam, fams[fam], wins)
                    log(f"MILESTONE planned pass{pno} {fam}: {n} jobs")
                if not self.run_family_jobs(fam, ["W5"] if (fam == "TOPDOWN" or fam.startswith(("COS_", "COSB_", "HATE_", "BRIDGE_"))) else [w for w, _ in wins]):
                    stop = True
                    break
                log(f"MILESTONE pass{pno} family done: {fam} {self.progress_str()}")
            if stop:
                break
        self.phase = "finished" if dt.datetime.now() < PULL_STOP and (self.max_jobs is None or self.jobs_run < self.max_jobs) else "stopped"
        self.heartbeat(force=True)
        log(f"DONE worker phase={self.phase} {self.progress_str()}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--max-jobs", type=int, default=None)
    a = ap.parse_args()
    if a.status:
        w = Worker()
        ok, tot = w.progress()
        print(f"jobs ok {ok}/{tot}")
        for r in w.con.execute("SELECT family,count(*),sum(status='ok') FROM jobs GROUP BY family"):
            print(r)
        print(STATE_PATH.read_text() if STATE_PATH.exists() else "no state")
        return
    Worker(only=[x for x in a.only.split(",") if x], max_jobs=a.max_jobs).run()


if __name__ == "__main__":
    main()
