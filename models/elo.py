"""
Elo rating engine.

Ratings are persisted per league in a JSON file and updated after each game.
The expected win probability formula is the standard Elo logistic:

    P(A beats B) = 1 / (1 + 10 ^ ((B_elo - A_elo) / 400))

Home advantage is applied by adding home_advantage Elo points to the home
team before computing the probability. This keeps the ratings themselves
"neutral venue" so they transfer correctly across home/away contexts.
"""

import math
from typing import Dict, Optional, Tuple


INITIAL_ELO = 1500.0


def expected_win_prob(elo_a: float, elo_b: float) -> float:
    """
    P(A wins) given neutral-venue Elo ratings.
    Call with elo_a = home_elo + home_advantage for a home-game prediction.
    """
    return 1.0 / (1.0 + 10.0 ** ((elo_b - elo_a) / 400.0))


def elo_from_win_pct(win_pct: float, mean: float = INITIAL_ELO) -> float:
    """
    Estimate a starting Elo from a team's win percentage.
    Useful for bootstrapping from current-season records.

    Derivation: solve P(team beats average) = win_pct for elo_team.
        win_pct = 1 / (1 + 10^((mean - elo) / 400))
        elo = mean + 400 * log10(win_pct / (1 - win_pct))
    """
    if win_pct <= 0.0:
        win_pct = 0.01
    elif win_pct >= 1.0:
        win_pct = 0.99
    return mean + 400.0 * math.log10(win_pct / (1.0 - win_pct))


def update_elo(
    elo_winner: float,
    elo_loser: float,
    k: float = 20.0,
    margin: Optional[float] = None,
    margin_base: Optional[float] = None,
) -> Tuple[float, float]:
    """
    Update Elo ratings after a completed game.

    When margin and margin_base are provided, applies a margin-of-victory
    multiplier (FiveThirtyEight-style) to weight convincing wins more.

    Returns (new_winner_elo, new_loser_elo).
    """
    p_winner = expected_win_prob(elo_winner, elo_loser)
    delta = 1.0 - p_winner  # winner earned 1, expected p_winner

    if margin is not None and margin_base is not None and margin_base > 0:
        # Multiplier dampens large-margin games to reduce overcorrection
        mov_mult = math.log(abs(margin) + 1.0) / math.log(margin_base + 1.0)
        mov_mult = min(mov_mult, 2.0)  # cap at 2×
    else:
        mov_mult = 1.0

    adjustment = k * mov_mult * delta
    return elo_winner + adjustment, elo_loser - adjustment


def regress_to_mean(elo: float, fraction: float = 0.33, mean: float = INITIAL_ELO) -> float:
    """Pull a rating toward the league mean between seasons."""
    return elo + fraction * (mean - elo)
