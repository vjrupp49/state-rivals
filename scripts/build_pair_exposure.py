"""Pair exposure (regular-season meetings per season) and team success (win share) for the NFL and MLB, 2021-2025.

Sources (free, public): nflverse games.csv (github.com/nflverse/nfldata) and MLB's public stats API
(statsapi.mlb.com schedule). Raw responses are cached under data/raw/_cache (git-ignored); the derived aggregates
data/raw/pair_exposure.csv and data/raw/team_success.csv are committed. Used by gravity_exposure.py.

    python scripts/build_pair_exposure.py        # reads the cache; fetches if missing
"""
import csv
import json
import pathlib
import sys
from collections import defaultdict

import requests

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from paths import ROOT  # noqa: E402

CACHE = ROOT / "data" / "raw" / "_cache"
UA = {"User-Agent": "StateRivalsResearch/0.1 (academic research)"}
SEASONS = (2021, 2022, 2023, 2024, 2025)
NFL = {"ARI": "cardinals", "ATL": "falcons", "BAL": "ravens", "BUF": "bills", "CAR": "panthers", "CHI": "bears", "CIN": "bengals", "CLE": "browns",
       "DAL": "cowboys", "DEN": "broncos", "DET": "lions", "GB": "packers", "HOU": "texans", "IND": "colts", "JAX": "jaguars", "KC": "chiefs",
       "LV": "raiders", "OAK": "raiders", "LAC": "chargers", "SD": "chargers", "LA": "rams", "LAR": "rams", "STL": "rams", "MIA": "dolphins",
       "MIN": "vikings", "NE": "patriots", "NO": "saints", "NYG": "giants", "NYJ": "jets", "PHI": "eagles", "PIT": "steelers", "SF": "49ers",
       "SEA": "seahawks", "TB": "buccaneers", "TEN": "titans", "WAS": "commanders", "WSH": "commanders"}


def fetch(path, url):
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        path.write_bytes(requests.get(url, headers=UA, timeout=90).content)
    return path


def entity_index():
    ents = list(csv.DictReader(open(ROOT / "data/registries/entities.csv", encoding="utf-8")))
    return {e["entity_id"]: e for e in ents}


def main():
    reg = entity_index()
    pairs = defaultdict(float)
    wins, games = defaultdict(float), defaultdict(float)
    # NFL
    p = fetch(CACHE / "nfl_games.csv", "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv")
    for r in csv.DictReader(open(p, encoding="utf-8")):
        if r["game_type"] != "REG" or not r["season"].isdigit() or int(r["season"]) not in SEASONS or r["home_score"] == "":
            continue
        a, h = NFL.get(r["away_team"]), NFL.get(r["home_team"])
        if not (a and h):
            continue
        ia, ih = "nfl_" + a, "nfl_" + h
        pairs[("nfl",) + tuple(sorted((ia, ih)))] += 1
        for t, s_own, s_opp in ((ia, float(r["away_score"]), float(r["home_score"])), (ih, float(r["home_score"]), float(r["away_score"]))):
            games[t] += 1
            wins[t] += 1.0 if s_own > s_opp else (0.5 if s_own == s_opp else 0.0)
    # MLB: match by nickname (last word of the registry name, or last two for Sox/Jays)
    nick = {}
    for eid, e in reg.items():
        if eid.startswith("mlb_"):
            n = e["entity_name"].split()
            key = " ".join(n[-2:]) if n[-1] in ("Sox", "Jays") else n[-1]
            nick[key.lower()] = eid
    for yr in SEASONS:
        d = json.loads(fetch(CACHE / f"mlb_{yr}.json", f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&season={yr}&gameType=R&fields=dates,games,gamePk,status,detailedState,teams,away,home,team,name,score,isWinner").read_text(encoding="utf-8"))
        for day in d["dates"]:
            for g in day["games"]:
                if g["status"]["detailedState"] != "Final":
                    continue
                an, hn = g["teams"]["away"]["team"]["name"].split(), g["teams"]["home"]["team"]["name"].split()
                ka = (" ".join(an[-2:]) if an[-1] in ("Sox", "Jays") else an[-1]).lower()
                kh = (" ".join(hn[-2:]) if hn[-1] in ("Sox", "Jays") else hn[-1]).lower()
                ia, ih = nick.get(ka), nick.get(kh)
                if not (ia and ih):
                    continue
                pairs[("mlb",) + tuple(sorted((ia, ih)))] += 1
                for side, t in (("away", ia), ("home", ih)):
                    games[t] += 1
                    wins[t] += 1.0 if g["teams"][side].get("isWinner") else 0.0
    n = len(SEASONS)
    with open(ROOT / "data/raw/pair_exposure.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["league", "entity_a", "entity_b", "meetings_per_season", "window", "source"])
        for (lg, a, b), c in sorted(pairs.items()):
            w.writerow([lg, a, b, round(c / n, 3), "2021-2025 regular season", "nflverse games.csv" if lg == "nfl" else "MLB statsapi schedule"])
    with open(ROOT / "data/raw/team_success.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["entity_id", "win_share", "games", "window"])
        for t in sorted(games):
            w.writerow([t, round(wins[t] / games[t], 4), int(games[t]), "2021-2025 regular season"])
    print(f"{len(pairs)} pairs, {len(games)} teams")


if __name__ == "__main__":
    main()
