"""
League configurations and team code mappings.

Model parameters are calibrated to historical margin-of-victory distributions
for each league. Elo K-factor, home advantage, spread divisor, and standard
deviations are tuned per sport.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class LeagueConfig:
    name: str
    brain_code: str          # 8rain Station league code
    espn_sport: str          # ESPN API sport segment
    espn_league: str         # ESPN API league segment
    elo_k: float             # How fast ratings update (larger = more volatile)
    home_advantage: float    # Home Elo boost (in Elo points)
    spread_divisor: float    # expected_margin = elo_diff / spread_divisor
    margin_std: float        # Std dev of game margin (points/runs/goals)
    total_std: float         # Std dev of game total
    typical_total: float     # League-average total for the sport
    typical_home_score: float
    typical_away_score: float
    elo_mean: float = 1500.0
    season_regression: float = 0.33  # Fraction of Elo regressed to mean between seasons


LEAGUES: Dict[str, LeagueConfig] = {
    "nba": LeagueConfig(
        name="NBA",
        brain_code="nba",
        espn_sport="basketball",
        espn_league="nba",
        elo_k=20,
        home_advantage=50,       # Modern NBA HCA is small (~2-3 pts)
        spread_divisor=28.6,     # 100 Elo diff ≈ 3.5 pt expected margin
        margin_std=12.0,
        total_std=21.0,
        typical_total=225.0,
        typical_home_score=114.0,
        typical_away_score=111.0,
    ),
    "nfl": LeagueConfig(
        name="NFL",
        brain_code="nfl",
        espn_sport="football",
        espn_league="nfl",
        elo_k=20,
        home_advantage=48,       # ~2-2.5 pt HCA
        spread_divisor=25.0,     # 100 Elo diff ≈ 4 pt expected margin
        margin_std=13.5,
        total_std=23.0,
        typical_total=44.0,
        typical_home_score=22.5,
        typical_away_score=21.5,
    ),
    "mlb": LeagueConfig(
        name="MLB",
        brain_code="mlb",
        espn_sport="baseball",
        espn_league="mlb",
        elo_k=6,                 # Low K — small sample each game
        home_advantage=24,       # ~0.3 runs HCA
        spread_divisor=71.4,     # Narrower scale; runs are scarce
        margin_std=3.0,
        total_std=3.2,
        typical_total=8.5,
        typical_home_score=4.4,
        typical_away_score=4.1,
    ),
    "wnba": LeagueConfig(
        name="WNBA",
        brain_code="wnba",
        espn_sport="basketball",
        espn_league="wnba",
        elo_k=20,
        home_advantage=40,
        spread_divisor=28.6,
        margin_std=10.0,
        total_std=17.0,
        typical_total=163.0,
        typical_home_score=83.0,
        typical_away_score=80.0,
    ),
    "epl": LeagueConfig(
        name="EPL",
        brain_code="epl",
        espn_sport="soccer",
        espn_league="eng.1",
        elo_k=20,
        home_advantage=60,       # Soccer has strong HCA
        spread_divisor=100.0,
        margin_std=1.5,
        total_std=1.4,
        typical_total=2.7,
        typical_home_score=1.5,
        typical_away_score=1.2,
    ),
}

# ---------------------------------------------------------------------------
# Team code mappings  (ESPN abbreviation → 8rain Station code)
# Only entries that DIFFER are listed; identical ones fall through unchanged.
# ---------------------------------------------------------------------------

ESPN_TO_BRAIN: Dict[str, Dict[str, str]] = {
    "nba": {
        "GS": "GSW",
        "SA": "SAS",
        "NO": "NOP",
        "PHX": "PHO",
        "WSH": "WAS",
        "OKC": "OKC",
        "NY": "NYK",
    },
    "nfl": {
        "WSH": "WAS",
    },
    "mlb": {
        "ARI": "AZ",
        "OAK": "ATH",   # Athletics relocated
        "SAC": "ATH",   # Sacramento Athletics
        "WSH": "WSH",
    },
    "wnba": {
        "LA": "LAS",
        "NY": "NYL",
        "WAS": "WAS",
        "PHX": "PHX",
    },
    "epl": {
        "Brighton": "BHA",
        "Man City": "MCI",
        "Man United": "MUN",
        "Newcastle": "NEW",
        "Nottingham Forest": "NFO",
        "Tottenham": "TOT",
        "West Ham": "WHU",
        "Wolves": "WOL",
        "Aston Villa": "AVL",
        "Brentford": "BRE",
        "Burnley": "BRN",
        "Sunderland": "SUN",
        "Leeds": "LEE",
    },
}


def normalize_team(league: str, espn_code: str) -> str:
    """Convert ESPN team abbreviation to 8rain Station code."""
    mapping = ESPN_TO_BRAIN.get(league, {})
    return mapping.get(espn_code, espn_code)


# Prop stat standard deviations (per-game, used for normal distribution approximation)
PROP_STD_DEV: Dict[str, Dict[str, float]] = {
    "nba": {
        "player-points-ou": 7.5,
        "player-rebounds-ou": 2.8,
        "player-assists-ou": 2.4,
        "player-threePointersMade-ou": 1.2,
        "player-steals-ou": 0.8,
        "player-blocks-ou": 0.9,
        "player-turnovers-ou": 1.1,
        "player-points+rebounds-ou": 8.5,
        "player-points+assists-ou": 8.0,
        "player-rebounds+assists-ou": 3.5,
        "player-points+rebounds+assists-ou": 9.5,
        "player-freeThrowsMade-ou": 1.5,
        "player-freeThrowsAttempted-ou": 1.7,
        "player-fieldGoalsMade-ou": 2.5,
        "player-blocks+steals-ou": 1.1,
    },
    "nfl": {
        "player-passing_yards-ou": 55.0,
        "player-rushing_yards-ou": 30.0,
        "player-receiving_yards-ou": 25.0,
        "player-passing_touchdowns-ou": 0.9,
        "player-receiving_receptions-ou": 2.0,
        "player-rushing+receiving_yards-ou": 35.0,
    },
    "mlb": {
        "batter_hits": 0.75,
        "batter_runs": 0.55,
        "batter_rbis": 0.60,
        "batter_bases": 1.0,
        "batter_strikeouts": 0.65,
        "batter_walks": 0.45,
        "batter_home_runs": 0.30,
        "pitcher_strikeouts": 2.5,
        "pitcher_hits": 2.0,
        "pitcher_earned_runs": 1.5,
        "pitcher_outs": 3.0,
        "pitcher_walks": 1.2,
    },
}


# Standard lines for display when market lines are unavailable
# NBA/NFL/WNBA: use model-implied margin. MLB always uses ±1.5 run line.
MLB_RUN_LINE = 1.5
