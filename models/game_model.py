"""
Game-level probability model.

Converts Elo ratings into:
  - Win probability (moneyline)
  - Spread/run-line probability at a given point
  - Total probability at a given line

All distributions are approximated as normal. For soccer and baseball,
a Poisson approximation is also available but the normal form is used
by default since 8rain Station accepts decimal probabilities and the
differences are small at typical lines.
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy.stats import norm

from config import LeagueConfig
from models.elo import expected_win_prob, INITIAL_ELO


@dataclass
class GamePrediction:
    """All probabilities for a single game."""
    league: str
    home: str
    away: str
    home_elo: float
    away_elo: float

    # Win probabilities (moneyline)
    p_home_win: float
    p_away_win: float

    # Expected margin (positive = home team leads)
    expected_margin: float

    # Expected total (combined score)
    expected_total: float

    # Individual expected scores
    expected_home_score: float
    expected_away_score: float

    def spread_prob(self, line: float, cfg: LeagueConfig) -> float:
        """
        P(home covers 'line' spread).
        line is from home's perspective: -3.5 means home gives 3.5 points.
        P = P(actual_margin > line) = 1 - cdf((line - expected_margin) / std)
        """
        return float(1.0 - norm.cdf((line - self.expected_margin) / cfg.margin_std))

    def total_prob(self, line: float, cfg: LeagueConfig) -> float:
        """P(over 'line')."""
        return float(1.0 - norm.cdf((line - self.expected_total) / cfg.total_std))

    def home_score_prob(self, line: float, cfg: LeagueConfig) -> float:
        """P(home team scores over 'line')."""
        single_std = cfg.margin_std * 0.75  # rough single-team std
        return float(1.0 - norm.cdf((line - self.expected_home_score) / single_std))

    def away_score_prob(self, line: float, cfg: LeagueConfig) -> float:
        single_std = cfg.margin_std * 0.75
        return float(1.0 - norm.cdf((line - self.expected_away_score) / single_std))


class GameModel:
    """Produce a GamePrediction from Elo ratings and league config."""

    def predict(
        self,
        cfg: LeagueConfig,
        home: str,
        away: str,
        home_elo: float,
        away_elo: float,
        home_off_rating: Optional[float] = None,  # runs/pts/goals per game
        away_off_rating: Optional[float] = None,
        home_def_rating: Optional[float] = None,  # runs/pts/goals allowed per game
        away_def_rating: Optional[float] = None,
    ) -> GamePrediction:
        """
        Build a complete game prediction.

        Offensive/defensive ratings refine the expected total but are optional.
        When absent the model falls back to league-typical scores scaled by Elo.
        """
        adjusted_home_elo = home_elo + cfg.home_advantage
        p_home = expected_win_prob(adjusted_home_elo, away_elo)
        p_away = 1.0 - p_home

        elo_diff = adjusted_home_elo - away_elo
        expected_margin = elo_diff / cfg.spread_divisor

        # --- Expected scores ---
        if (home_off_rating is not None and away_def_rating is not None
                and away_off_rating is not None and home_def_rating is not None):
            # Simple log5-style blend: team offensive vs opponent defensive ratings
            league_avg_off = cfg.typical_total / 2.0
            # Pythagorean blending: expected_score = team_off * opp_def / league_avg
            # Clamp to avoid bizarre numbers from sparse data
            home_exp = np.clip(
                (home_off_rating + away_def_rating) / 2.0, 0.5 * cfg.typical_home_score, 2.0 * cfg.typical_home_score
            )
            away_exp = np.clip(
                (away_off_rating + home_def_rating) / 2.0, 0.5 * cfg.typical_away_score, 2.0 * cfg.typical_away_score
            )
        else:
            # Fall back: split typical totals, then tilt by expected_margin
            home_exp = cfg.typical_home_score + expected_margin * 0.5
            away_exp = cfg.typical_away_score - expected_margin * 0.5
            home_exp = max(home_exp, 0.0)
            away_exp = max(away_exp, 0.0)

        expected_total = home_exp + away_exp

        return GamePrediction(
            league=cfg.brain_code,
            home=home,
            away=away,
            home_elo=home_elo,
            away_elo=away_elo,
            p_home_win=p_home,
            p_away_win=p_away,
            expected_margin=expected_margin,
            expected_total=expected_total,
            expected_home_score=float(home_exp),
            expected_away_score=float(away_exp),
        )
