"""
MLB Stats API client (official, free, no key required).

Docs: https://github.com/toddrob99/MLB-StatsAPI/wiki/Endpoints

Used for:
  - Today's MLB schedule with probable pitchers
  - Pitcher season stats (ERA, K/9, WHIP)
  - Batter season and game-log stats (for player props)
  - Team offensive / defensive ratings
"""

import logging
import os
import json
import time
import hashlib
from datetime import date
from typing import Dict, List, Optional, Tuple

import requests

log = logging.getLogger(__name__)

BASE = "https://statsapi.mlb.com/api/v1"
CACHE_TTL = 3600


def _cache_path(url: str, params: dict, cache_dir: str) -> str:
    key = url + json.dumps(params, sort_keys=True)
    digest = hashlib.md5(key.encode()).hexdigest()
    return os.path.join(cache_dir, f"mlb_{digest}.json")


def _get(url: str, params: dict = None, cache_dir: Optional[str] = None, ttl: int = CACHE_TTL) -> dict:
    params = params or {}
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        cp = _cache_path(url, params, cache_dir)
        if os.path.exists(cp):
            if time.time() - os.path.getmtime(cp) < ttl:
                with open(cp) as f:
                    return json.load(f)

    time.sleep(0.2)
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if cache_dir:
        with open(cp, "w") as f:
            json.dump(data, f)
    return data


# ---------------------------------------------------------------------------
# Schedule
# ---------------------------------------------------------------------------

def fetch_schedule(game_date: date, cache_dir: Optional[str] = None) -> List[dict]:
    """
    Return today's MLB games with probable pitchers.

    Each item: {home, away, home_pitcher_id, away_pitcher_id,
                game_pk, status, doubleheader_seq}
    """
    url = f"{BASE}/schedule"
    params = {
        "date": game_date.strftime("%Y-%m-%d"),
        "sportId": 1,
        "hydrate": "probablePitcher,team",
    }
    try:
        data = _get(url, params=params, cache_dir=cache_dir)
    except Exception as e:
        log.error("MLB schedule fetch failed: %s", e)
        return []

    games = []
    for date_entry in data.get("dates", []):
        for game in date_entry.get("games", []):
            status = game.get("status", {}).get("detailedState", "")
            home_team = game.get("teams", {}).get("home", {})
            away_team = game.get("teams", {}).get("away", {})

            home_code = home_team.get("team", {}).get("abbreviation", "")
            away_code = away_team.get("team", {}).get("abbreviation", "")
            home_code = _mlb_abbrev(home_code)
            away_code = _mlb_abbrev(away_code)

            home_pitcher = home_team.get("probablePitcher", {})
            away_pitcher = away_team.get("probablePitcher", {})

            dh = game.get("doubleHeader", "N")
            dh_seq = int(game.get("gameNumber", 1)) if dh != "N" else 0

            games.append({
                "game_pk": game.get("gamePk"),
                "home": home_code,
                "away": away_code,
                "home_pitcher_id": home_pitcher.get("id"),
                "home_pitcher_name": home_pitcher.get("fullName", "TBD"),
                "away_pitcher_id": away_pitcher.get("id"),
                "away_pitcher_name": away_pitcher.get("fullName", "TBD"),
                "status": status,
                "doubleheader_seq": dh_seq,
                "is_completed": "Final" in status,
            })
    return games


# ---------------------------------------------------------------------------
# Pitcher stats
# ---------------------------------------------------------------------------

def fetch_pitcher_stats(pitcher_id: int, season: int, cache_dir: Optional[str] = None) -> dict:
    """
    Return season pitching stats for one pitcher.
    Keys: era, whip, strikeoutsPer9Inn, walks, strikeouts, inningsPitched, gamesStarted
    """
    url = f"{BASE}/people/{pitcher_id}/stats"
    params = {"stats": "season", "group": "pitching", "season": season}
    try:
        data = _get(url, params=params, cache_dir=cache_dir)
    except Exception as e:
        log.warning("Pitcher stats fetch failed for %s: %s", pitcher_id, e)
        return {}

    for split in data.get("stats", [{}])[0].get("splits", []):
        s = split.get("stat", {})
        return {
            "era": _f(s.get("era")),
            "whip": _f(s.get("whip")),
            "k_per_9": _f(s.get("strikeoutsPer9Inn")),
            "bb_per_9": _f(s.get("walksPer9Inn")),
            "strikeouts": _f(s.get("strikeOuts")),
            "walks": _f(s.get("baseOnBalls")),
            "innings": _f(s.get("inningsPitched")),
            "games_started": _f(s.get("gamesStarted")),
            "hits_per_9": _f(s.get("hitsPer9Inn")),
        }
    return {}


# ---------------------------------------------------------------------------
# Batter stats (season averages and game log)
# ---------------------------------------------------------------------------

def fetch_batter_season_stats(player_id: int, season: int, cache_dir: Optional[str] = None) -> dict:
    """Return season batting stats."""
    url = f"{BASE}/people/{player_id}/stats"
    params = {"stats": "season", "group": "hitting", "season": season}
    try:
        data = _get(url, params=params, cache_dir=cache_dir)
    except Exception as e:
        log.warning("Batter stats fetch failed for %s: %s", player_id, e)
        return {}

    for split in data.get("stats", [{}])[0].get("splits", []):
        s = split.get("stat", {})
        games = max(_f(s.get("gamesPlayed")) or 1, 1)
        return {
            "avg": _f(s.get("avg")),
            "obp": _f(s.get("obp")),
            "slg": _f(s.get("slg")),
            "ops": _f(s.get("ops")),
            "hits_per_game": (_f(s.get("hits")) or 0) / games,
            "runs_per_game": (_f(s.get("runs")) or 0) / games,
            "rbi_per_game": (_f(s.get("rbi")) or 0) / games,
            "hr_per_game": (_f(s.get("homeRuns")) or 0) / games,
            "so_per_game": (_f(s.get("strikeOuts")) or 0) / games,
            "bb_per_game": (_f(s.get("baseOnBalls")) or 0) / games,
            "tb_per_game": (_f(s.get("totalBases")) or 0) / games,
            "sb_per_game": (_f(s.get("stolenBases")) or 0) / games,
            "games": games,
        }
    return {}


def fetch_batter_game_log(player_id: int, season: int, cache_dir: Optional[str] = None) -> List[dict]:
    """
    Return chronological game-by-game batting stats for a player.
    Each entry has hits, runs, rbi, hr, k, bb, tb, etc.
    """
    url = f"{BASE}/people/{player_id}/stats"
    params = {"stats": "gameLog", "group": "hitting", "season": season}
    try:
        data = _get(url, params=params, cache_dir=cache_dir, ttl=7200)
    except Exception as e:
        log.warning("Game log fetch failed for %s: %s", player_id, e)
        return []

    entries = []
    for split in data.get("stats", [{}])[0].get("splits", []):
        s = split.get("stat", {})
        entries.append({
            "date": split.get("date", ""),
            "hits": _f(s.get("hits")) or 0,
            "runs": _f(s.get("runs")) or 0,
            "rbi": _f(s.get("rbi")) or 0,
            "hr": _f(s.get("homeRuns")) or 0,
            "k": _f(s.get("strikeOuts")) or 0,
            "bb": _f(s.get("baseOnBalls")) or 0,
            "tb": _f(s.get("totalBases")) or 0,
            "sb": _f(s.get("stolenBases")) or 0,
            "singles": (_f(s.get("hits")) or 0)
                       - (_f(s.get("doubles")) or 0)
                       - (_f(s.get("triples")) or 0)
                       - (_f(s.get("homeRuns")) or 0),
            "doubles": _f(s.get("doubles")) or 0,
            "triples": _f(s.get("triples")) or 0,
            "h_r_rbi": ((_f(s.get("hits")) or 0)
                        + (_f(s.get("runs")) or 0)
                        + (_f(s.get("rbi")) or 0)),
        })
    return entries


def fetch_pitcher_game_log(player_id: int, season: int, cache_dir: Optional[str] = None) -> List[dict]:
    """Chronological pitching game log."""
    url = f"{BASE}/people/{player_id}/stats"
    params = {"stats": "gameLog", "group": "pitching", "season": season}
    try:
        data = _get(url, params=params, cache_dir=cache_dir, ttl=7200)
    except Exception as e:
        log.warning("Pitcher game log failed for %s: %s", player_id, e)
        return []

    entries = []
    for split in data.get("stats", [{}])[0].get("splits", []):
        s = split.get("stat", {})
        ip_str = s.get("inningsPitched", "0")
        ip = _parse_innings(ip_str)
        outs = round(ip * 3)
        entries.append({
            "date": split.get("date", ""),
            "strikeouts": _f(s.get("strikeOuts")) or 0,
            "hits": _f(s.get("hits")) or 0,
            "earned_runs": _f(s.get("earnedRuns")) or 0,
            "walks": _f(s.get("baseOnBalls")) or 0,
            "outs": outs,
            "win": 1.0 if s.get("wins", 0) else 0.0,
        })
    return entries


# ---------------------------------------------------------------------------
# Team stats (for total/run-line modeling)
# ---------------------------------------------------------------------------

def fetch_team_stats_mlb(season: int, cache_dir: Optional[str] = None) -> Dict[str, dict]:
    """
    Return offensive and defensive stats for all MLB teams.
    Keyed by 8rain Station team code.
    """
    hitting = _get(
        f"{BASE}/teams/stats",
        params={"season": season, "sportId": 1, "group": "hitting"},
        cache_dir=cache_dir,
        ttl=3600,
    )
    pitching = _get(
        f"{BASE}/teams/stats",
        params={"season": season, "sportId": 1, "group": "pitching"},
        cache_dir=cache_dir,
        ttl=3600,
    )

    result: Dict[str, dict] = {}

    def _process(data, key_prefix):
        for team_stat in data.get("stats", [{}])[0].get("splits", []):
            abbrev = team_stat.get("team", {}).get("abbreviation", "")
            abbrev = _mlb_abbrev(abbrev)
            s = team_stat.get("stat", {})
            games = max(_f(s.get("gamesPlayed")) or 1, 1)
            result.setdefault(abbrev, {})
            result[abbrev][f"{key_prefix}_runs_per_game"] = (_f(s.get("runs")) or 0) / games
            result[abbrev][f"{key_prefix}_hits_per_game"] = (_f(s.get("hits")) or 0) / games
            result[abbrev][f"{key_prefix}_hr_per_game"] = (_f(s.get("homeRuns")) or 0) / games
            result[abbrev][f"{key_prefix}_k_per_game"] = (_f(s.get("strikeOuts")) or 0) / games
            result[abbrev][f"{key_prefix}_ops"] = _f(s.get("ops")) or 0
            result[abbrev]["games"] = games

    _process(hitting, "off")
    # Pitching stats represent runs ALLOWED
    for team_stat in pitching.get("stats", [{}])[0].get("splits", []):
        abbrev = _mlb_abbrev(team_stat.get("team", {}).get("abbreviation", ""))
        s = team_stat.get("stat", {})
        games = max(_f(s.get("gamesPlayed")) or 1, 1)
        result.setdefault(abbrev, {})
        result[abbrev]["def_runs_allowed_per_game"] = (_f(s.get("earnedRuns")) or 0) / games
        result[abbrev]["def_era"] = _f(s.get("era")) or 4.5

    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MLB_ABBREV_MAP = {
    "ARI": "AZ",
    "OAK": "ATH",
    "WSH": "WSH",
}


def _mlb_abbrev(code: str) -> str:
    return MLB_ABBREV_MAP.get(code, code)


def _f(val) -> Optional[float]:
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _parse_innings(ip_str: str) -> float:
    """Convert '6.2' (6 innings 2 outs) to 6.667 actual innings."""
    try:
        parts = str(ip_str).split(".")
        full = int(parts[0])
        frac = int(parts[1]) / 3.0 if len(parts) > 1 and parts[1] else 0.0
        return full + frac
    except (ValueError, IndexError):
        return 0.0
