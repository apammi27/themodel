"""
8rain Station CSV formatter.

Converts internal prediction objects into rows in the exact CSV schema
required by the 8rain Station upload format.

Reference spec: https://docs.google.com/spreadsheets/d/...
  LEAGUE, DATE, HOME, AWAY, DOUBLEHEADER, SECTION, MARKET, SELECTOR, POINT, SIDE, WIN %
"""

import csv
import io
import os
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional


@dataclass
class BrainRow:
    """One row of the 8rain Station upload format."""
    league: str
    date: int                    # YYYYMMDD
    home: str
    away: str
    section: str
    market: str
    side: str
    win_pct: float               # decimal probability, e.g. 0.537
    selector: str = ""           # player ID or team code (blank for game-level)
    point: str = ""              # spread/total line or blank
    doubleheader: int = 0


def _fmt_pct(p: float) -> str:
    """Format win probability to 4 decimal places."""
    return f"{p:.4f}"


def _fmt_point(p) -> str:
    if p is None or p == "":
        return ""
    val = float(p)
    return f"{val:g}"


def rows_to_csv(rows: List[BrainRow]) -> str:
    """Serialize a list of BrainRow objects to CSV string."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["LEAGUE", "DATE", "HOME", "AWAY", "DOUBLEHEADER",
                     "SECTION", "MARKET", "SELECTOR", "POINT", "SIDE", "WIN %"])
    for r in rows:
        writer.writerow([
            r.league.upper(),
            r.date,
            r.home,
            r.away,
            r.doubleheader if r.doubleheader else "",
            r.section,
            r.market,
            r.selector,
            _fmt_point(r.point) if r.point != "" else "",
            r.side,
            _fmt_pct(r.win_pct),
        ])
    return buf.getvalue()


def write_csv(rows: List[BrainRow], path: str) -> None:
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w", newline="") as f:
        f.write(rows_to_csv(rows))


# ---------------------------------------------------------------------------
# Convenience builders
# ---------------------------------------------------------------------------

def moneyline_rows(
    league: str, game_date: int, home: str, away: str,
    p_home: float, doubleheader: int = 0,
    market: str = "h2h", section: str = "head_to_head",
) -> List[BrainRow]:
    """Two rows (home + away) for a moneyline market."""
    p_away = 1.0 - p_home
    return [
        BrainRow(league=league, date=game_date, home=home, away=away,
                 section=section, market=market, side="home",
                 win_pct=p_home, doubleheader=doubleheader),
        BrainRow(league=league, date=game_date, home=home, away=away,
                 section=section, market=market, side="away",
                 win_pct=p_away, doubleheader=doubleheader),
    ]


def spread_rows(
    league: str, game_date: int, home: str, away: str,
    home_point: float, p_home_cover: float,
    doubleheader: int = 0, market: str = "spread", section: str = "spread",
) -> List[BrainRow]:
    """Two rows (home + away) for a spread market."""
    away_point = -home_point
    p_away_cover = 1.0 - p_home_cover
    return [
        BrainRow(league=league, date=game_date, home=home, away=away,
                 section=section, market=market, side="home",
                 point=home_point, win_pct=p_home_cover, doubleheader=doubleheader),
        BrainRow(league=league, date=game_date, home=home, away=away,
                 section=section, market=market, side="away",
                 point=away_point, win_pct=p_away_cover, doubleheader=doubleheader),
    ]


def total_rows(
    league: str, game_date: int, home: str, away: str,
    line: float, p_over: float,
    doubleheader: int = 0, market: str = "total", section: str = "total",
) -> List[BrainRow]:
    """Two rows (over + under) for a totals market."""
    p_under = 1.0 - p_over
    return [
        BrainRow(league=league, date=game_date, home=home, away=away,
                 section=section, market=market, side="over",
                 point=line, win_pct=p_over, doubleheader=doubleheader),
        BrainRow(league=league, date=game_date, home=home, away=away,
                 section=section, market=market, side="under",
                 point=line, win_pct=p_under, doubleheader=doubleheader),
    ]


def player_prop_rows(
    league: str, game_date: int, selector: str,
    market: str, line: float, p_over: float,
    home: str = "", away: str = "",
    side_over: str = "over", side_under: str = "under",
) -> List[BrainRow]:
    """Two rows (over + under) for a player prop."""
    p_under = 1.0 - p_over
    return [
        BrainRow(league=league, date=game_date, home=home, away=away,
                 section="player_prop", market=market, selector=selector,
                 side=side_over, point=line, win_pct=p_over),
        BrainRow(league=league, date=game_date, home=home, away=away,
                 section="player_prop", market=market, selector=selector,
                 side=side_under, point=line, win_pct=p_under),
    ]


def yes_no_prop_rows(
    league: str, game_date: int, selector: str,
    market: str, p_yes: float,
    home: str = "", away: str = "",
) -> List[BrainRow]:
    """Two rows (yes + no) for a binary player prop."""
    return [
        BrainRow(league=league, date=game_date, home=home, away=away,
                 section="player_prop", market=market, selector=selector,
                 side="yes", win_pct=p_yes),
        BrainRow(league=league, date=game_date, home=home, away=away,
                 section="player_prop", market=market, selector=selector,
                 side="no", win_pct=1.0 - p_yes),
    ]


def team_prop_rows(
    league: str, game_date: int, selector: str,
    market: str, line: float, p_over: float,
    home: str = "", away: str = "",
    section: str = "team_prop",
) -> List[BrainRow]:
    """Two rows (over + under) for a team prop."""
    return [
        BrainRow(league=league, date=game_date, home=home, away=away,
                 section=section, market=market, selector=selector,
                 side="over", point=line, win_pct=p_over),
        BrainRow(league=league, date=game_date, home=home, away=away,
                 section=section, market=market, selector=selector,
                 side="under", point=line, win_pct=1.0 - p_over),
    ]
