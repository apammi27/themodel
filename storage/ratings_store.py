"""
Persistent storage for Elo ratings.

Ratings are stored per-league in a JSON file so they accumulate across
daily runs. On first run for a league the ratings are bootstrapped from
ESPN's current standings (win %).
"""

import json
import os
from datetime import date
from typing import Dict, Optional

from models.elo import INITIAL_ELO, elo_from_win_pct, regress_to_mean

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "ratings.json")


def _default_store() -> dict:
    return {"ratings": {}, "last_updated": {}, "initialized": {}}


def load(path: str = DEFAULT_PATH) -> dict:
    """Load the full ratings store from disk."""
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return _default_store()


def save(store: dict, path: str = DEFAULT_PATH) -> None:
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(store, f, indent=2)


def get_rating(store: dict, league: str, team: str) -> float:
    return store.get("ratings", {}).get(league, {}).get(team, INITIAL_ELO)


def set_rating(store: dict, league: str, team: str, elo: float) -> None:
    store.setdefault("ratings", {}).setdefault(league, {})[team] = round(elo, 2)


def bootstrap_from_records(
    store: dict,
    league: str,
    records: Dict[str, tuple],  # team_code -> (wins, losses)
    path: str = DEFAULT_PATH,
    force: bool = False,
) -> None:
    """
    Initialize Elo ratings for a league from season win-loss records.

    Only runs once per league (unless force=True). After bootstrap, subsequent
    calls are no-ops so daily updates don't overwrite accumulated ratings.
    """
    if store.get("initialized", {}).get(league) and not force:
        return

    for team, (wins, losses) in records.items():
        total = wins + losses
        if total == 0:
            elo = INITIAL_ELO
        else:
            win_pct = wins / total
            elo = elo_from_win_pct(win_pct)
        set_rating(store, league, team, elo)

    store.setdefault("initialized", {})[league] = True
    save(store, path)


def apply_season_regression(store: dict, league: str, fraction: float = 0.33) -> None:
    """Regress all team Elos toward the mean. Call at the start of a new season."""
    league_ratings = store.get("ratings", {}).get(league, {})
    for team, elo in league_ratings.items():
        store["ratings"][league][team] = round(regress_to_mean(elo, fraction), 2)
