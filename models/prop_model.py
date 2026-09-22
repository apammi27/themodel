"""
Player prop probability model.

Uses a weighted rolling average over recent games as the expected value,
then applies a normal distribution (or Poisson for integer count stats)
to produce an over/under probability at a given line.

For binary props (yes/no) the probability is returned directly from
the rolling frequency.
"""

from typing import List, Optional
import numpy as np
from scipy.stats import norm, poisson


def weighted_average(values: List[float], lookback: int = 15) -> float:
    """
    Exponentially weighted mean of recent game values.
    More recent games receive higher weight.
    """
    if not values:
        return 0.0
    recent = values[-lookback:]
    n = len(recent)
    weights = np.exp(np.linspace(0, 1, n))  # exponential ramp
    weights /= weights.sum()
    return float(np.dot(weights, recent))


def rolling_std(values: List[float], lookback: int = 20, min_std: float = 0.5) -> float:
    """Standard deviation of recent games, floored at min_std."""
    if len(values) < 3:
        return min_std
    recent = values[-lookback:]
    return max(float(np.std(recent, ddof=1)), min_std)


def prop_over_probability(
    game_values: List[float],
    line: float,
    lookback: int = 15,
    use_poisson: bool = False,
    stat_std_override: Optional[float] = None,
) -> float:
    """
    P(player goes OVER 'line') given their recent game log.

    game_values: chronological list of stat values (most recent last).
    line: the prop line (e.g., 24.5 points).
    use_poisson: use Poisson distribution (better for low-count integer stats).
    stat_std_override: supply a known std dev (from config) instead of computing it.
    """
    if not game_values:
        return 0.5  # no data, return even odds

    mu = weighted_average(game_values, lookback)

    if use_poisson and mu > 0:
        # P(X > line) where X ~ Poisson(mu). For half-integer lines, floor to int.
        k = int(line)  # P(X > line) = P(X >= k+1) = 1 - P(X <= k)
        return float(1.0 - poisson.cdf(k, mu))

    # Normal approximation
    if stat_std_override is not None:
        sigma = stat_std_override
    else:
        sigma = rolling_std(game_values, lookback)

    return float(1.0 - norm.cdf(line, loc=mu, scale=sigma))


def prop_yes_probability(game_values: List[float], lookback: int = 20) -> float:
    """
    P(yes) for binary props (e.g., pitcher_win, anytime goal scorer).
    game_values should be 1.0 (occurred) or 0.0 (did not occur).
    """
    if not game_values:
        return 0.5
    recent = game_values[-lookback:]
    return float(np.mean(recent))


def opponent_adjustment(
    player_avg: float,
    league_avg: float,
    opp_allowed_avg: float,
    weight: float = 0.3,
) -> float:
    """
    Adjust expected prop value based on opponent's tendency to allow that stat.

    player_avg: player's rolling average for the stat.
    league_avg: league-wide average for the stat.
    opp_allowed_avg: how much the opponent allows of this stat per game.
    weight: how much to weight the opponent adjustment (0 = ignore opponent).
    """
    if league_avg <= 0:
        return player_avg
    opp_factor = opp_allowed_avg / league_avg
    adjusted = player_avg * (1.0 + weight * (opp_factor - 1.0))
    return max(adjusted, 0.0)
