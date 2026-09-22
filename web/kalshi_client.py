"""
Kalshi market client.

Fetches open sports markets and matches them to model game predictions.
Kalshi uses binary yes/no markets; yes_ask is in cents (0–100) and represents
the cost to win $1 if yes — i.e. the implied probability of yes.

API docs: https://trading-api.readme.io/reference/getmarkets
"""

import logging
import os
import time
from typing import Optional
import requests
from .team_names import team_in_text

log = logging.getLogger(__name__)

KALSHI_BASE = "https://trading-api.kalshi.com/trade-api/v2"
_cache: dict = {}
_cache_ts: float = 0.0
CACHE_TTL = 300  # 5 minutes


def _headers(api_key: Optional[str] = None) -> dict:
    h = {"accept": "application/json"}
    if api_key:
        h["Authorization"] = f"Bearer {api_key}"
    return h


def fetch_all_sports_markets(api_key: Optional[str] = None) -> list[dict]:
    """Return all open Kalshi sports markets (cached 5 min)."""
    global _cache, _cache_ts
    if time.time() - _cache_ts < CACHE_TTL and _cache.get("kalshi"):
        return _cache["kalshi"]

    markets: list[dict] = []
    cursor: Optional[str] = None
    hdrs = _headers(api_key)

    # Kalshi sports category slug may vary; try both
    for category in ("sports",):
        cur = None
        while True:
            params: dict = {"status": "open", "limit": 200, "category": category}
            if cur:
                params["cursor"] = cur
            try:
                r = requests.get(f"{KALSHI_BASE}/markets", params=params,
                                 headers=hdrs, timeout=10)
                r.raise_for_status()
                data = r.json()
                batch = data.get("markets", [])
                markets.extend(batch)
                cur = data.get("cursor")
                if not cur or not batch:
                    break
            except Exception as exc:
                log.warning("Kalshi fetch error: %s", exc)
                break

    _cache["kalshi"] = markets
    _cache_ts = time.time()
    log.info("Kalshi: fetched %d open sports markets", len(markets))
    return markets


def match_game(
    league: str, home: str, away: str, game_date: str,
    markets: list[dict],
) -> dict:
    """
    Try to find a Kalshi market for this game.

    Returns a dict with keys: home_prob, away_prob, url, title, matched
    (home_prob/away_prob are floats 0–1; may be None if no match).
    """
    result = {"home_prob": None, "away_prob": None, "url": None, "title": None, "matched": False}

    # Build a date string variants Kalshi might use in titles
    try:
        from datetime import datetime
        d = datetime.strptime(str(game_date), "%Y%m%d")
        date_variants = [
            d.strftime("%b %d").lstrip("0"),   # "Apr 15"
            d.strftime("%B %d").lstrip("0"),   # "April 15"
            d.strftime("%m/%d"),               # "04/15"
            str(game_date),                    # "20250415"
        ]
    except Exception:
        date_variants = []

    for m in markets:
        title = (m.get("title") or "") + " " + (m.get("subtitle") or "")

        home_hit = team_in_text(league, home, title)
        away_hit = team_in_text(league, away, title)
        if not (home_hit and away_hit):
            continue

        # Optionally require date match if date variants are known
        if date_variants:
            date_hit = any(dv.lower() in title.lower() for dv in date_variants)
            # Kalshi may not embed date in title; treat as match if within ~7 days
            # If market is open and teams match, accept it

        yes_ask = m.get("yes_ask")
        if yes_ask is None:
            continue

        # yes_ask is cents (0–100) → probability
        # Determine which team is "yes": look at which team name appears first
        title_lower = title.lower()
        from .team_names import get_aliases
        home_pos = min(
            (title_lower.find(n.lower()) for n in get_aliases(league, home)
             if title_lower.find(n.lower()) >= 0),
            default=9999,
        )
        away_pos = min(
            (title_lower.find(n.lower()) for n in get_aliases(league, away)
             if title_lower.find(n.lower()) >= 0),
            default=9999,
        )

        # The first team named is typically the "yes" outcome
        if home_pos <= away_pos:
            home_prob = yes_ask / 100.0
        else:
            home_prob = 1.0 - (yes_ask / 100.0)

        result.update(
            home_prob=round(home_prob, 4),
            away_prob=round(1.0 - home_prob, 4),
            url=f"https://kalshi.com/markets/{m.get('ticker', '')}",
            title=title.strip(),
            matched=True,
        )
        return result

    return result


def build_odds_map(
    games: list[tuple],  # list of (league, home, away, game_date)
    api_key: Optional[str] = None,
) -> dict[str, dict]:
    """
    Returns a dict keyed by game_key = "{league}|{date}|{home}|{away}"
    with matched Kalshi odds.
    """
    markets = fetch_all_sports_markets(api_key)
    result = {}
    for league, home, away, game_date in games:
        key = f"{league.upper()}|{game_date}|{home}|{away}"
        result[key] = match_game(league, home, away, game_date, markets)
    return result
