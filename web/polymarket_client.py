"""
Polymarket market client.

Uses the Gamma API (metadata layer) to find sports prediction markets.
Each market has an `outcomePrices` array of decimal strings (0.0–1.0)
aligned with the `outcomes` array.

Gamma API: https://gamma-api.polymarket.com/markets
CLOB API:  https://clob.polymarket.com
"""

import logging
import time
from typing import Optional
import requests
from .team_names import team_in_text, get_aliases

log = logging.getLogger(__name__)

GAMMA_BASE = "https://gamma-api.polymarket.com"
_cache: dict = {}
_cache_ts: float = 0.0
CACHE_TTL = 300  # 5 minutes

def fetch_all_sports_markets(league: Optional[str] = None) -> list[dict]:
    """Return Polymarket sports markets.

    Polymarket does not offer individual game-winner markets for major US sports
    leagues (NFL, NBA, MLB). It focuses on politics, crypto, and season-level
    futures. Return empty list so the edge table shows '—' for Polymarket columns
    without making unnecessary API calls.
    """
    log.info("Polymarket: per-game markets not available; skipping fetch")
    return []


def match_game(
    league: str, home: str, away: str, game_date: str,
    markets: list[dict],
) -> dict:
    """
    Find a Polymarket market for this game.
    Returns dict with home_prob, away_prob, url, title, matched.
    """
    result = {"home_prob": None, "away_prob": None, "url": None, "title": None, "matched": False}

    try:
        from datetime import datetime
        d = datetime.strptime(str(game_date), "%Y%m%d")
        date_variants = [
            d.strftime("%b %d").lstrip("0"),
            d.strftime("%B %d").lstrip("0"),
            d.strftime("%m/%d"),
        ]
    except Exception:
        date_variants = []

    home_aliases = get_aliases(league, home)
    away_aliases = get_aliases(league, away)

    for m in markets:
        question = m.get("question") or ""
        desc = (m.get("description") or "") + " " + question

        home_hit = team_in_text(league, home, desc)
        away_hit = team_in_text(league, away, desc)
        if not (home_hit and away_hit):
            continue

        outcomes = m.get("outcomes") or []
        prices_raw = m.get("outcomePrices") or []

        if not outcomes or not prices_raw:
            continue

        try:
            prices = [float(p) for p in prices_raw]
        except (TypeError, ValueError):
            continue

        if len(outcomes) != len(prices):
            continue

        # Find which outcome index corresponds to home vs away
        home_idx, away_idx = None, None
        for i, outcome in enumerate(outcomes):
            if any(a.lower() in outcome.lower() for a in home_aliases):
                home_idx = i
            elif any(a.lower() in outcome.lower() for a in away_aliases):
                away_idx = i

        if home_idx is None or away_idx is None:
            # Binary Yes/No market — determine which team the "Yes" refers to
            if len(outcomes) == 2 and outcomes[0].lower() == "yes":
                q_lower = question.lower()
                home_pos = min(
                    (q_lower.find(a.lower()) for a in home_aliases if q_lower.find(a.lower()) >= 0),
                    default=9999,
                )
                away_pos = min(
                    (q_lower.find(a.lower()) for a in away_aliases if q_lower.find(a.lower()) >= 0),
                    default=9999,
                )
                if home_pos < away_pos:
                    home_prob = prices[0]  # Yes = home
                else:
                    home_prob = prices[1]  # No = home (Yes = away)
            else:
                continue
        else:
            home_prob = prices[home_idx]

        slug = m.get("slug") or m.get("conditionId") or ""
        url = f"https://polymarket.com/event/{slug}" if slug else "https://polymarket.com"

        result.update(
            home_prob=round(home_prob, 4),
            away_prob=round(1.0 - home_prob, 4),
            url=url,
            title=question.strip(),
            matched=True,
        )
        return result

    return result


def build_odds_map(
    games: list[tuple],  # list of (league, home, away, game_date)
) -> dict[str, dict]:
    """
    Returns dict keyed by "{LEAGUE}|{date}|{home}|{away}" with Polymarket odds.
    Always returns unmatched entries since Polymarket has no per-game NFL markets.
    """
    markets = fetch_all_sports_markets()
    result = {}
    for league, home, away, game_date in games:
        key = f"{league.upper()}|{game_date}|{home}|{away}"
        result[key] = match_game(league, home, away, game_date, markets)
    return result
