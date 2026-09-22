"""
ESPN unofficial API client.

ESPN exposes a public JSON API at site.api.espn.com that requires no key.
We use it for:
  - Today's schedule (scoreboard endpoint)
  - Team season statistics (offensive/defensive ratings)
  - Team win-loss records (for Elo bootstrapping)

Rate limit: the API is public but not officially documented.  We add a small
delay between calls and cache responses for the session to be polite.
"""

import os
import json
import time
import hashlib
import logging
from datetime import date
from typing import Dict, List, Optional, Tuple

import requests

from config import LeagueConfig, normalize_team

log = logging.getLogger(__name__)

BASE_URL = "https://site.api.espn.com/apis/site/v2/sports"
STANDINGS_URL = "https://site.api.espn.com/apis/v2/sports"

DEFAULT_CACHE = os.path.join(os.path.dirname(__file__), "..", ".cache")
REQUEST_DELAY = 0.3  # seconds between API calls


def _cache_path(url: str, params: dict, cache_dir: str) -> str:
    key = url + json.dumps(params, sort_keys=True)
    digest = hashlib.md5(key.encode()).hexdigest()
    return os.path.join(cache_dir, f"{digest}.json")


def _get(url: str, params: dict = None, cache_dir: Optional[str] = None, ttl: int = 3600) -> dict:
    """GET with optional file caching. Returns parsed JSON."""
    params = params or {}
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        cp = _cache_path(url, params, cache_dir)
        if os.path.exists(cp):
            age = time.time() - os.path.getmtime(cp)
            if age < ttl:
                with open(cp) as f:
                    return json.load(f)

    time.sleep(REQUEST_DELAY)
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if cache_dir:
        with open(cp, "w") as f:
            json.dump(data, f)

    return data


# ---------------------------------------------------------------------------
# Schedule / scoreboard
# ---------------------------------------------------------------------------

def fetch_schedule(cfg: LeagueConfig, game_date: date, cache_dir: Optional[str] = None) -> List[dict]:
    """
    Return a list of games scheduled for game_date.

    Each item is a dict with:
        id, home, away, home_score, away_score, status, is_completed
    """
    url = f"{BASE_URL}/{cfg.espn_sport}/{cfg.espn_league}/scoreboard"
    data = _get(url, params={"dates": game_date.strftime("%Y%m%d")}, cache_dir=cache_dir)

    games = []
    for event in data.get("events", []):
        competitions = event.get("competitions", [])
        if not competitions:
            continue
        comp = competitions[0]

        competitors = comp.get("competitors", [])
        home = next((c for c in competitors if c.get("homeAway") == "home"), None)
        away = next((c for c in competitors if c.get("homeAway") == "away"), None)
        if not home or not away:
            continue

        status_info = comp.get("status", {}).get("type", {})
        is_completed = status_info.get("completed", False)

        home_code = normalize_team(cfg.brain_code, home.get("team", {}).get("abbreviation", ""))
        away_code = normalize_team(cfg.brain_code, away.get("team", {}).get("abbreviation", ""))

        games.append({
            "id": event.get("id"),
            "home": home_code,
            "away": away_code,
            "home_score": _safe_float(home.get("score")),
            "away_score": _safe_float(away.get("score")),
            "status": status_info.get("description", ""),
            "is_completed": is_completed,
        })

    return games


# ---------------------------------------------------------------------------
# Team statistics
# ---------------------------------------------------------------------------

def fetch_team_stats(cfg: LeagueConfig, team_id: str, cache_dir: Optional[str] = None) -> dict:
    """
    Fetch season stats for a team. Returns a flat dict of stat_name → value.
    """
    url = f"{BASE_URL}/{cfg.espn_sport}/{cfg.espn_league}/teams/{team_id}/statistics"
    try:
        data = _get(url, cache_dir=cache_dir)
    except Exception as e:
        log.warning("Could not fetch stats for team %s: %s", team_id, e)
        return {}

    stats = {}
    results = data.get("results", data)
    # Navigate: results → stats → splits → categories → stats
    splits = (
        results.get("stats", {})
        .get("splits", {})
        .get("categories", [])
    )
    for category in splits:
        for stat in category.get("stats", []):
            name = stat.get("name") or stat.get("displayName", "")
            val = stat.get("value")
            if name and val is not None:
                stats[name] = val
    return stats


def fetch_all_team_stats(
    cfg: LeagueConfig, cache_dir: Optional[str] = None
) -> Dict[str, dict]:
    """
    Return stats for every team in the league, keyed by team abbreviation.
    Falls back to the team list endpoint to get IDs first.
    """
    url = f"{BASE_URL}/{cfg.espn_sport}/{cfg.espn_league}/teams"
    try:
        data = _get(url, cache_dir=cache_dir)
    except Exception as e:
        log.warning("Could not fetch team list for %s: %s", cfg.brain_code, e)
        return {}

    result = {}
    for sport_team in data.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", []):
        team = sport_team.get("team", {})
        team_id = team.get("id")
        abbrev = normalize_team(cfg.brain_code, team.get("abbreviation", ""))
        if team_id and abbrev:
            stats = fetch_team_stats(cfg, team_id, cache_dir)
            result[abbrev] = stats

    return result


# ---------------------------------------------------------------------------
# Standings / records  (used for Elo bootstrapping)
# ---------------------------------------------------------------------------

def fetch_standings(cfg: LeagueConfig, cache_dir: Optional[str] = None) -> Dict[str, Tuple[int, int]]:
    """
    Return {team_code: (wins, losses)} for the current season.
    """
    url = f"{BASE_URL}/{cfg.espn_sport}/{cfg.espn_league}/standings"
    try:
        data = _get(url, cache_dir=cache_dir, ttl=7200)
    except Exception as e:
        log.warning("Could not fetch standings for %s: %s", cfg.brain_code, e)
        return {}

    records: Dict[str, Tuple[int, int]] = {}

    # ESPN standings structure varies; try both common shapes
    for group in data.get("children", data.get("standings", {}).get("entries", [])):
        entries = group.get("standings", {}).get("entries", group if isinstance(group, list) else [])
        for entry in entries:
            team = entry.get("team", {})
            abbrev = normalize_team(cfg.brain_code, team.get("abbreviation", ""))
            wins = losses = 0
            for stat in entry.get("stats", []):
                if stat.get("name") == "wins":
                    wins = int(stat.get("value", 0))
                elif stat.get("name") == "losses":
                    losses = int(stat.get("value", 0))
            if abbrev:
                records[abbrev] = (wins, losses)

    return records


# ---------------------------------------------------------------------------
# Player stats (for props)
# ---------------------------------------------------------------------------

def fetch_player_game_log(
    cfg: LeagueConfig,
    player_id: str,
    season: Optional[int] = None,
    cache_dir: Optional[str] = None,
) -> List[dict]:
    """
    Fetch recent game log entries for a player.
    Returns a list of stat dicts, most recent last.
    """
    if season is None:
        season = date.today().year

    url = f"{BASE_URL}/{cfg.espn_sport}/{cfg.espn_league}/athletes/{player_id}/gamelog"
    try:
        data = _get(url, params={"season": season}, cache_dir=cache_dir, ttl=7200)
    except Exception as e:
        log.warning("Could not fetch game log for player %s: %s", player_id, e)
        return []

    entries = []
    categories = data.get("categories", [])
    stat_names = []
    for cat in categories:
        for label in cat.get("labels", []):
            stat_names.append(label)

    for event in data.get("events", []):
        row_stats = event.get("stats", [])
        game_stats = {}
        for i, val in enumerate(row_stats):
            if i < len(stat_names):
                try:
                    game_stats[stat_names[i]] = float(val)
                except (ValueError, TypeError):
                    pass
        if game_stats:
            entries.append(game_stats)

    return entries


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_float(val) -> Optional[float]:
    try:
        return float(val)
    except (TypeError, ValueError):
        return None
