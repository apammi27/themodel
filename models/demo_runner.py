"""
Demo runner: identical logic to daily_runner but uses demo_data instead of live APIs.
Used for offline testing / format verification.
"""

import logging
from datetime import date
from typing import List

from config import LEAGUES, LeagueConfig, MLB_RUN_LINE, PROP_STD_DEV
from data.demo_data import (
    demo_schedule, demo_team_stats, demo_standings, demo_pitcher_stats
)
from models.elo import update_elo, INITIAL_ELO
from models.game_model import GameModel
from output.formatter import (
    BrainRow, moneyline_rows, spread_rows, total_rows, team_prop_rows,
)
from storage import ratings_store

log = logging.getLogger(__name__)
game_model = GameModel()

LEAGUE_AVERAGE_ERA = 4.20


def run_demo(leagues: List[str], game_date: date, ratings_path: str) -> List[BrainRow]:
    store = ratings_store.load(ratings_path)
    all_rows: List[BrainRow] = []

    for league_code in leagues:
        if league_code not in LEAGUES:
            log.warning("Unknown league: %s", league_code)
            continue
        cfg = LEAGUES[league_code]

        # Bootstrap Elo from demo standings
        if not store.get("initialized", {}).get(cfg.brain_code):
            records = demo_standings(cfg.brain_code)
            ratings_store.bootstrap_from_records(store, cfg.brain_code, records, ratings_path)

        date_int = int(game_date.strftime("%Y%m%d"))
        games = demo_schedule(cfg.brain_code, game_date)
        if not games:
            log.info("No demo games for %s", cfg.name)
            continue

        team_stats = demo_team_stats(cfg.brain_code)
        team_off, team_def = {}, {}

        if cfg.brain_code == "mlb":
            for team, s in team_stats.items():
                team_off[team] = s.get("off_runs_per_game", cfg.typical_home_score)
                team_def[team] = s.get("def_runs_allowed_per_game", cfg.typical_away_score)
        else:
            for team, s in team_stats.items():
                team_off[team] = (s.get("avgPoints") or s.get("goalsPerGame") or cfg.typical_home_score)
                team_def[team] = (s.get("avgPointsAllowed") or s.get("goalsAllowedPerGame") or cfg.typical_away_score)

        for game in games:
            home, away = game["home"], game["away"]
            dh = game.get("doubleheader_seq", 0)

            h_elo = ratings_store.get_rating(store, cfg.brain_code, home)
            a_elo = ratings_store.get_rating(store, cfg.brain_code, away)

            h_off = team_off.get(home)
            a_off = team_off.get(away)
            h_def = team_def.get(home)
            a_def = team_def.get(away)

            if cfg.brain_code == "mlb":
                h_pid = game.get("home_pitcher_id")
                a_pid = game.get("away_pitcher_id")
                season = date_int // 10000
                if h_pid:
                    ps = demo_pitcher_stats(h_pid, season)
                    factor = (ps.get("era") or LEAGUE_AVERAGE_ERA) / LEAGUE_AVERAGE_ERA
                    if a_off is not None:
                        a_off = a_off * factor
                if a_pid:
                    ps = demo_pitcher_stats(a_pid, season)
                    factor = (ps.get("era") or LEAGUE_AVERAGE_ERA) / LEAGUE_AVERAGE_ERA
                    if h_off is not None:
                        h_off = h_off * factor

            pred = game_model.predict(
                cfg=cfg, home=home, away=away,
                home_elo=h_elo, away_elo=a_elo,
                home_off_rating=h_off, away_off_rating=a_off,
                home_def_rating=h_def, away_def_rating=a_def,
            )

            all_rows.extend(moneyline_rows(
                league=cfg.brain_code, game_date=date_int,
                home=home, away=away, p_home=pred.p_home_win, doubleheader=dh,
            ))

            spread_line = _round_half(pred.expected_margin)
            all_rows.extend(spread_rows(
                league=cfg.brain_code, game_date=date_int,
                home=home, away=away,
                home_point=spread_line,
                p_home_cover=pred.spread_prob(spread_line, cfg),
                doubleheader=dh,
            ))

            if cfg.brain_code == "mlb":
                fav_line = -MLB_RUN_LINE if pred.expected_margin >= 0 else MLB_RUN_LINE
                all_rows.extend(spread_rows(
                    league=cfg.brain_code, game_date=date_int,
                    home=home, away=away,
                    home_point=fav_line,
                    p_home_cover=pred.spread_prob(fav_line, cfg),
                    doubleheader=dh,
                ))

            total_line = _round_half(pred.expected_total)
            all_rows.extend(total_rows(
                league=cfg.brain_code, game_date=date_int,
                home=home, away=away,
                line=total_line,
                p_over=pred.total_prob(total_line, cfg),
                doubleheader=dh,
            ))

            # Team props
            if cfg.brain_code in ("nba", "wnba"):
                for tc, exp in [(home, pred.expected_home_score), (away, pred.expected_away_score)]:
                    line = _round_half(exp)
                    p_over = (pred.home_score_prob(line, cfg) if tc == home
                              else pred.away_score_prob(line, cfg))
                    all_rows.extend(team_prop_rows(
                        league=cfg.brain_code, game_date=date_int,
                        home=home, away=away, selector=tc,
                        market="points", line=line, p_over=p_over,
                    ))
            elif cfg.brain_code == "mlb":
                for tc, exp in [(home, pred.expected_home_score), (away, pred.expected_away_score)]:
                    line = _round_half(exp)
                    p_over = (pred.home_score_prob(line, cfg) if tc == home
                              else pred.away_score_prob(line, cfg))
                    all_rows.extend(team_prop_rows(
                        league=cfg.brain_code, game_date=date_int,
                        home=home, away=away, selector=tc,
                        market="runs", line=line, p_over=p_over,
                    ))

    ratings_store.save(store, ratings_path)
    return all_rows


def _round_half(x: float) -> float:
    return round(x * 2) / 2
