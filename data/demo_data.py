"""
Hard-coded demo data for offline testing.

Simulates what the live ESPN/MLB APIs would return for a mixed slate.
Used by `python main.py run --demo` to verify output format without network.
"""

from datetime import date
from typing import Dict, List, Optional


def demo_schedule(league: str, game_date: date) -> List[dict]:
    """Return a realistic fake schedule for the given league/date."""
    d = int(game_date.strftime("%Y%m%d"))
    schedules = {
        "nba": [
            {"id": "401700001", "home": "BOS", "away": "NYK",
             "home_score": None, "away_score": None, "status": "Scheduled",
             "is_completed": False, "doubleheader_seq": 0},
            {"id": "401700002", "home": "LAL", "away": "GSW",
             "home_score": None, "away_score": None, "status": "Scheduled",
             "is_completed": False, "doubleheader_seq": 0},
            {"id": "401700003", "home": "MIL", "away": "IND",
             "home_score": None, "away_score": None, "status": "Scheduled",
             "is_completed": False, "doubleheader_seq": 0},
        ],
        "nfl": [
            {"id": "401700100", "home": "KC", "away": "BUF",
             "home_score": None, "away_score": None, "status": "Scheduled",
             "is_completed": False, "doubleheader_seq": 0},
            {"id": "401700101", "home": "PHI", "away": "DAL",
             "home_score": None, "away_score": None, "status": "Scheduled",
             "is_completed": False, "doubleheader_seq": 0},
        ],
        "mlb": [
            {"game_pk": 740001, "home": "NYY", "away": "BOS",
             "home_pitcher_id": 543037, "home_pitcher_name": "G. Cole",
             "away_pitcher_id": 605400, "away_pitcher_name": "B. Sale",
             "status": "Scheduled", "is_completed": False, "doubleheader_seq": 0},
            {"game_pk": 740002, "home": "LAD", "away": "SD",
             "home_pitcher_id": 477132, "home_pitcher_name": "C. Kershaw",
             "away_pitcher_id": 661403, "away_pitcher_name": "D. Snell",
             "status": "Scheduled", "is_completed": False, "doubleheader_seq": 0},
            {"game_pk": 740003, "home": "HOU", "away": "TEX",
             "home_pitcher_id": 543135, "home_pitcher_name": "J. Verlander",
             "away_pitcher_id": 622072, "away_pitcher_name": "J. Gray",
             "status": "Scheduled", "is_completed": False, "doubleheader_seq": 0},
        ],
        "wnba": [
            {"id": "401700200", "home": "LVA", "away": "NYL",
             "home_score": None, "away_score": None, "status": "Scheduled",
             "is_completed": False, "doubleheader_seq": 0},
            {"id": "401700201", "home": "IND", "away": "CON",
             "home_score": None, "away_score": None, "status": "Scheduled",
             "is_completed": False, "doubleheader_seq": 0},
        ],
        "epl": [
            {"id": "401700300", "home": "LIV", "away": "MCI",
             "home_score": None, "away_score": None, "status": "Scheduled",
             "is_completed": False, "doubleheader_seq": 0},
            {"id": "401700301", "home": "ARS", "away": "CHE",
             "home_score": None, "away_score": None, "status": "Scheduled",
             "is_completed": False, "doubleheader_seq": 0},
        ],
    }
    return schedules.get(league, [])


def demo_team_stats(league: str) -> Dict[str, dict]:
    """Return realistic per-game offensive/defensive averages."""
    if league == "nba":
        return {
            "BOS": {"avgPoints": 121.2, "avgPointsAllowed": 109.8},
            "NYK": {"avgPoints": 113.5, "avgPointsAllowed": 113.0},
            "LAL": {"avgPoints": 116.8, "avgPointsAllowed": 115.2},
            "GSW": {"avgPoints": 117.4, "avgPointsAllowed": 116.9},
            "MIL": {"avgPoints": 118.3, "avgPointsAllowed": 114.5},
            "IND": {"avgPoints": 119.7, "avgPointsAllowed": 119.1},
        }
    elif league == "nfl":
        return {
            "KC":  {"avgPoints": 27.2, "avgPointsAllowed": 17.1},
            "BUF": {"avgPoints": 28.5, "avgPointsAllowed": 20.3},
            "PHI": {"avgPoints": 25.8, "avgPointsAllowed": 21.4},
            "DAL": {"avgPoints": 24.1, "avgPointsAllowed": 22.0},
        }
    elif league == "mlb":
        return {
            "NYY": {"off_runs_per_game": 5.1, "def_runs_allowed_per_game": 3.9},
            "BOS": {"off_runs_per_game": 4.7, "def_runs_allowed_per_game": 4.6},
            "LAD": {"off_runs_per_game": 5.3, "def_runs_allowed_per_game": 3.7},
            "SD":  {"off_runs_per_game": 4.4, "def_runs_allowed_per_game": 4.1},
            "HOU": {"off_runs_per_game": 4.8, "def_runs_allowed_per_game": 4.0},
            "TEX": {"off_runs_per_game": 4.5, "def_runs_allowed_per_game": 4.4},
        }
    elif league == "wnba":
        return {
            "LVA": {"avgPoints": 87.4, "avgPointsAllowed": 77.2},
            "NYL": {"avgPoints": 85.1, "avgPointsAllowed": 79.8},
            "IND": {"avgPoints": 83.7, "avgPointsAllowed": 80.5},
            "CON": {"avgPoints": 82.3, "avgPointsAllowed": 81.1},
        }
    elif league == "epl":
        return {
            "LIV": {"goalsPerGame": 2.3, "goalsAllowedPerGame": 0.9},
            "MCI": {"goalsPerGame": 2.5, "goalsAllowedPerGame": 1.0},
            "ARS": {"goalsPerGame": 2.1, "goalsAllowedPerGame": 0.9},
            "CHE": {"goalsPerGame": 1.7, "goalsAllowedPerGame": 1.3},
        }
    return {}


def demo_standings(league: str) -> Dict[str, tuple]:
    """Return (wins, losses) per team for Elo bootstrapping."""
    if league == "nba":
        return {
            "BOS": (64, 18), "NYK": (51, 31), "LAL": (47, 35),
            "GSW": (46, 36), "MIL": (49, 33), "IND": (47, 35),
            "PHI": (47, 35), "MIA": (46, 36), "CHI": (39, 43),
            "CLE": (48, 34), "DEN": (57, 25), "OKC": (57, 25),
            "MIN": (56, 26), "DAL": (50, 32), "LAC": (51, 31),
            "PHO": (49, 33), "NOP": (49, 33), "SAC": (46, 36),
            "POR": (21, 61), "UTA": (31, 51), "TOR": (25, 57),
            "BKN": (32, 50), "DET": (14, 68), "CHA": (21, 61),
            "WAS": (15, 67), "ATL": (36, 46), "HOU": (41, 41),
            "SAS": (22, 60), "MEM": (27, 55), "ORL": (47, 35),
        }
    elif league == "nfl":
        return {
            "KC":  (11, 6), "BUF": (11, 6), "PHI": (11, 6), "DAL": (10, 7),
            "SF":  (12, 5), "DET": (12, 5), "BAL": (13, 4), "HOU": (10, 7),
            "LAR": (10, 7), "MIN": (7, 10),  "GB": (9, 8),  "ATL": (8, 9),
            "SEA": (9, 8),  "ARI": (4, 13), "NE": (4, 13), "NYJ": (7, 10),
            "CIN": (9, 8),  "CLE": (11, 6), "PIT": (10, 7), "TEN": (6, 11),
            "JAX": (9, 8),  "IND": (9, 8),  "CAR": (2, 15), "MIA": (11, 6),
            "LV":  (8, 9),  "LAC": (5, 12), "DEN": (8, 9),  "NYG": (6, 11),
            "WAS": (4, 13), "TB":  (9, 8),  "NO": (9, 8),  "CHI": (7, 10),
        }
    elif league == "mlb":
        return {
            "NYY": (92, 70), "BOS": (78, 84), "LAD": (100, 62), "SD": (82, 80),
            "HOU": (90, 72), "TEX": (90, 72), "ATL": (89, 73), "PHI": (90, 72),
            "BAL": (91, 71), "TB":  (80, 82), "MIL": (88, 74), "CHC": (83, 79),
            "NYM": (75, 87), "WSH": (71, 91), "MIA": (84, 78), "BRK": (75, 87),
            "MIN": (87, 75), "CLE": (76, 86), "DET": (86, 76), "KC":  (86, 76),
            "CWS": (61, 101),"STL": (83, 79), "CIN": (82, 80), "PIT": (76, 86),
            "AZ":  (94, 68), "COL": (59, 103),"SF":  (80, 82), "SEA": (85, 77),
            "LAA": (63, 99), "OAK": (69, 93), "ATH": (69, 93),
        }
    elif league == "wnba":
        return {
            "LVA": (26, 8), "NYL": (32, 8), "CON": (24, 16),
            "MIN": (22, 18), "IND": (20, 20), "SEA": (19, 21),
            "ATL": (14, 26), "CHI": (13, 27), "LAS": (11, 29),
            "PHX": (9, 31), "WAS": (10, 30), "DAL": (8, 32),
            "GSV": (6, 34),
        }
    elif league == "epl":
        return {
            "LIV": (22, 5), "MCI": (20, 7), "ARS": (21, 5),
            "CHE": (14, 10), "TOT": (15, 11), "AVL": (20, 6),
            "MUN": (12, 15), "NEW": (14, 11), "WOL": (13, 13),
            "WHU": (12, 14), "BHA": (12, 14), "FUL": (11, 14),
            "BRE": (10, 15), "CRY": (9, 16), "EVE": (8, 17),
            "NFO": (8, 20), "LEE": (8, 18), "BRN": (5, 22),
            "SUN": (7, 19), "WOL": (13, 13),
        }
    return {}


def demo_pitcher_stats(pitcher_id: int, season: int) -> dict:
    """Return fake pitcher stats for demo mode."""
    stats_map = {
        543037: {"era": 3.20, "k_per_9": 9.5, "whip": 1.08, "strikeouts": 180, "innings": 180.0},
        605400: {"era": 4.10, "k_per_9": 8.8, "whip": 1.22, "strikeouts": 160, "innings": 155.0},
        477132: {"era": 3.75, "k_per_9": 8.2, "whip": 1.15, "strikeouts": 145, "innings": 150.0},
        661403: {"era": 3.38, "k_per_9": 10.2, "whip": 1.18, "strikeouts": 170, "innings": 165.0},
        543135: {"era": 3.30, "k_per_9": 9.8, "whip": 1.05, "strikeouts": 185, "innings": 185.0},
        622072: {"era": 4.40, "k_per_9": 7.9, "whip": 1.28, "strikeouts": 140, "innings": 145.0},
    }
    return stats_map.get(pitcher_id, {"era": 4.20, "k_per_9": 8.0, "whip": 1.20})
