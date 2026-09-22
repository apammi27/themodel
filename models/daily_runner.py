"""
Daily prediction runner.

For each league, this module:
  1. Loads persistent Elo ratings (initialising from standings on first run).
  2. Fetches today's schedule.
  3. Produces game-level predictions (moneyline, spread, total).
  4. Produces player props where data is available.
  5. Returns a list of BrainRow objects ready for CSV serialisation.
  6. Optionally updates Elo ratings from yesterday's completed games.

Sport-specific logic lives in the helper functions at the bottom of this file.
"""

import logging
import math
import os
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from config import LEAGUES, LeagueConfig, MLB_RUN_LINE, PROP_STD_DEV
from data import espn_client, mlb_client
from models.elo import update_elo, INITIAL_ELO
from models.game_model import GameModel
from models.prop_model import (
    prop_over_probability, prop_yes_probability, opponent_adjustment
)
from output.formatter import (
    BrainRow, moneyline_rows, spread_rows, total_rows,
    player_prop_rows, yes_no_prop_rows, team_prop_rows,
)
from storage import ratings_store

log = logging.getLogger(__name__)
game_model = GameModel()

# Typical MLB line points for team props
_MLB_TEAM_RUN_LINES = [2.5, 3.5, 4.5]
_NBA_TEAM_PTS_LINES_OFFSET = [0.0]  # use expected score ± 0 as the line

LEAGUE_AVERAGE_ERA = 4.20  # MLB 2024 league average


def run_daily(
    leagues: List[str],
    game_date: date,
    ratings_path: str,
    cache_dir: Optional[str] = None,
    update_elo: bool = True,
    prop_lookback: int = 15,
    mlb_player_ids: Optional[Dict[str, List[int]]] = None,
) -> List[BrainRow]:
    """
    Generate all predictions for game_date across the given leagues.

    mlb_player_ids: optional dict {game_home_code: [batter_mlbids, ...]}
                    for generating MLB player props. If omitted, only
                    game-level markets are produced for MLB.
    """
    store = ratings_store.load(ratings_path)
    all_rows: List[BrainRow] = []

    for league_code in leagues:
        if league_code not in LEAGUES:
            log.warning("Unknown league: %s — skipping.", league_code)
            continue
        cfg = LEAGUES[league_code]
        log.info("Processing %s for %s", cfg.name, game_date)

        try:
            rows = _process_league(
                cfg=cfg,
                game_date=game_date,
                store=store,
                ratings_path=ratings_path,
                cache_dir=cache_dir,
                prop_lookback=prop_lookback,
                mlb_player_ids=mlb_player_ids,
            )
            all_rows.extend(rows)
        except Exception as e:
            log.error("Failed to process %s: %s", league_code, e, exc_info=True)

    ratings_store.save(store, ratings_path)
    return all_rows


def _process_league(
    cfg: LeagueConfig,
    game_date: date,
    store: dict,
    ratings_path: str,
    cache_dir: Optional[str],
    prop_lookback: int,
    mlb_player_ids: Optional[Dict],
) -> List[BrainRow]:
    """Process a single league for game_date."""
    rows: List[BrainRow] = []
    date_int = int(game_date.strftime("%Y%m%d"))

    # --- Bootstrap Elo if needed ---
    _ensure_elo_initialized(cfg, store, ratings_path, cache_dir)

    # --- Fetch today's schedule ---
    if cfg.brain_code == "mlb":
        games = mlb_client.fetch_schedule(game_date, cache_dir)
    else:
        games = espn_client.fetch_schedule(cfg, game_date, cache_dir)

    if not games:
        log.info("No games found for %s on %s", cfg.name, game_date)
        return []

    log.info("Found %d %s game(s) on %s", len(games), cfg.name, game_date)

    # --- Fetch team stats for total predictions ---
    team_off: Dict[str, float] = {}
    team_def: Dict[str, float] = {}

    if cfg.brain_code == "mlb":
        team_stats = mlb_client.fetch_team_stats_mlb(game_date.year, cache_dir)
        for team, stats in team_stats.items():
            team_off[team] = stats.get("off_runs_per_game", cfg.typical_home_score)
            team_def[team] = stats.get("def_runs_allowed_per_game", cfg.typical_away_score)
    else:
        espn_stats = espn_client.fetch_all_team_stats(cfg, cache_dir)
        for team, stats in espn_stats.items():
            # ESPN stat name varies by sport; try common names
            team_off[team] = (
                stats.get("avgPoints")
                or stats.get("pointsPerGame")
                or stats.get("goalsPerGame")
                or stats.get("runsPerGame")
                or cfg.typical_home_score
            )
            team_def[team] = (
                stats.get("avgPointsAllowed")
                or stats.get("opponentPointsPerGame")
                or stats.get("goalsAllowedPerGame")
                or cfg.typical_away_score
            )

    # --- Process each game ---
    for game in games:
        try:
            game_rows = _predict_game(
                cfg=cfg,
                game=game,
                date_int=date_int,
                store=store,
                team_off=team_off,
                team_def=team_def,
                cache_dir=cache_dir,
                prop_lookback=prop_lookback,
                mlb_player_ids=mlb_player_ids,
            )
            rows.extend(game_rows)
        except Exception as e:
            log.warning("Skipping game %s vs %s: %s",
                        game.get("home"), game.get("away"), e)

    # --- Update Elo from completed games ---
    for game in games:
        if game.get("is_completed"):
            hs = game.get("home_score")
            as_ = game.get("away_score")
            if hs is not None and as_ is not None and hs != as_:
                home = game["home"]
                away = game["away"]
                h_elo = ratings_store.get_rating(store, cfg.brain_code, home)
                a_elo = ratings_store.get_rating(store, cfg.brain_code, away)
                if hs > as_:
                    new_h, new_a = update_elo(h_elo, a_elo, cfg.elo_k,
                                               margin=hs - as_, margin_base=cfg.typical_total / 5)
                else:
                    new_a, new_h = update_elo(a_elo, h_elo, cfg.elo_k,
                                               margin=as_ - hs, margin_base=cfg.typical_total / 5)
                ratings_store.set_rating(store, cfg.brain_code, home, new_h)
                ratings_store.set_rating(store, cfg.brain_code, away, new_a)

    return rows


def _predict_game(
    cfg: LeagueConfig,
    game: dict,
    date_int: int,
    store: dict,
    team_off: Dict[str, float],
    team_def: Dict[str, float],
    cache_dir: Optional[str],
    prop_lookback: int,
    mlb_player_ids: Optional[Dict],
) -> List[BrainRow]:
    """Build all prediction rows for one game."""
    rows: List[BrainRow] = []
    home = game["home"]
    away = game["away"]
    dh = game.get("doubleheader_seq", 0)

    h_elo = ratings_store.get_rating(store, cfg.brain_code, home)
    a_elo = ratings_store.get_rating(store, cfg.brain_code, away)

    h_off = team_off.get(home)
    a_off = team_off.get(away)
    h_def = team_def.get(home)
    a_def = team_def.get(away)

    # MLB: adjust for starting pitchers
    if cfg.brain_code == "mlb":
        h_off, a_off, h_def, a_def = _mlb_pitcher_adjustment(
            game, h_off, a_off, h_def, a_def, date_int // 10000, cache_dir
        )

    pred = game_model.predict(
        cfg=cfg, home=home, away=away,
        home_elo=h_elo, away_elo=a_elo,
        home_off_rating=h_off, away_off_rating=a_off,
        home_def_rating=h_def, away_def_rating=a_def,
    )

    # --- Moneyline ---
    rows.extend(moneyline_rows(
        league=cfg.brain_code, game_date=date_int,
        home=home, away=away,
        p_home=pred.p_home_win, doubleheader=dh,
    ))

    # --- Spread ---
    spread_line = _round_half(pred.expected_margin)
    rows.extend(spread_rows(
        league=cfg.brain_code, game_date=date_int,
        home=home, away=away,
        home_point=spread_line,
        p_home_cover=pred.spread_prob(spread_line, cfg),
        doubleheader=dh,
        market=_spread_market(cfg),
    ))

    # MLB: also output the standard ±1.5 run line
    if cfg.brain_code == "mlb":
        fav_line = -MLB_RUN_LINE if pred.expected_margin > 0 else MLB_RUN_LINE
        rows.extend(spread_rows(
            league=cfg.brain_code, game_date=date_int,
            home=home, away=away,
            home_point=fav_line,
            p_home_cover=pred.spread_prob(fav_line, cfg),
            doubleheader=dh,
        ))

    # --- Total ---
    total_line = _round_half(pred.expected_total)
    rows.extend(total_rows(
        league=cfg.brain_code, game_date=date_int,
        home=home, away=away,
        line=total_line,
        p_over=pred.total_prob(total_line, cfg),
        doubleheader=dh,
        market=_total_market(cfg),
    ))

    # --- Team props (NBA, MLB) ---
    if cfg.brain_code in ("nba", "wnba"):
        rows.extend(_nba_team_props(cfg, date_int, home, away, pred, dh))
    elif cfg.brain_code == "mlb":
        rows.extend(_mlb_team_props(cfg, date_int, home, away, pred, dh))

    # --- Player props (MLB only in base version) ---
    if cfg.brain_code == "mlb" and mlb_player_ids:
        rows.extend(_mlb_player_props(
            cfg, date_int, home, away, dh,
            mlb_player_ids, cache_dir, prop_lookback
        ))

    return rows


# ---------------------------------------------------------------------------
# MLB-specific helpers
# ---------------------------------------------------------------------------

def _mlb_pitcher_adjustment(
    game: dict, h_off, a_off, h_def, a_def, season: int, cache_dir
) -> Tuple:
    """Adjust expected runs based on starting pitcher ERA vs league average."""
    h_pid = game.get("home_pitcher_id")
    a_pid = game.get("away_pitcher_id")

    h_pitcher_factor = _pitcher_era_factor(h_pid, season, cache_dir)
    a_pitcher_factor = _pitcher_era_factor(a_pid, season, cache_dir)

    # Home pitcher ERA affects AWAY runs scored; away pitcher ERA affects HOME runs
    if a_off is not None:
        a_off = a_off * a_pitcher_factor  # away team expected to score against home pitcher
    if h_off is not None:
        h_off = h_off * h_pitcher_factor  # home team expected to score against away pitcher

    return h_off, a_off, h_def, a_def


def _pitcher_era_factor(pitcher_id: Optional[int], season: int, cache_dir) -> float:
    """Return ratio of pitcher ERA vs league average. >1 = pitcher easier to score on."""
    if not pitcher_id:
        return 1.0
    stats = mlb_client.fetch_pitcher_stats(pitcher_id, season, cache_dir)
    era = stats.get("era")
    if not era or era <= 0:
        return 1.0
    return era / LEAGUE_AVERAGE_ERA


def _mlb_team_props(cfg, date_int, home, away, pred, dh) -> List[BrainRow]:
    rows = []
    for team_code, exp_score in [(home, pred.expected_home_score), (away, pred.expected_away_score)]:
        line = _round_half(exp_score)
        for l in _MLB_TEAM_RUN_LINES:
            actual_line = _round_half(exp_score - (exp_score % 0.5 - l % 0.5))
        # Use predicted score as the line
        rows.extend(team_prop_rows(
            league=cfg.brain_code, game_date=date_int,
            home=home, away=away, selector=team_code,
            market="runs", line=line,
            p_over=pred.home_score_prob(line, cfg) if team_code == home
                   else pred.away_score_prob(line, cfg),
        ))
    return rows


def _mlb_player_props(
    cfg, date_int, home, away, dh,
    player_id_dict: Dict, cache_dir, lookback: int
) -> List[BrainRow]:
    """
    Generate MLB batter and pitcher props.

    player_id_dict: {
        "batters": [mlbid, ...],
        "pitchers": [mlbid, ...],
    }
    """
    rows = []
    season = date_int // 10000

    batter_ids = player_id_dict.get("batters", [])
    pitcher_ids = player_id_dict.get("pitchers", [])
    std = PROP_STD_DEV.get("mlb", {})

    for mlb_id in batter_ids:
        log_entries = mlb_client.fetch_batter_game_log(mlb_id, season, cache_dir)
        if not log_entries:
            continue

        hit_vals = [e["hits"] for e in log_entries]
        run_vals = [e["runs"] for e in log_entries]
        rbi_vals = [e["rbi"] for e in log_entries]
        hr_vals = [e["hr"] for e in log_entries]
        k_vals = [e["k"] for e in log_entries]
        bb_vals = [e["bb"] for e in log_entries]
        tb_vals = [e["tb"] for e in log_entries]
        sb_vals = [e["sb"] for e in log_entries]

        selector = str(mlb_id)

        # Hits
        hit_line = max(0.5, _round_half(
            sum(hit_vals[-lookback:]) / max(len(hit_vals[-lookback:]), 1)
        ) - 0.5)
        rows.extend(player_prop_rows(
            league="mlb", game_date=date_int, selector=selector,
            market="batter_hits", line=hit_line,
            p_over=prop_over_probability(hit_vals, hit_line, lookback,
                                         stat_std_override=std.get("batter_hits")),
            home=home, away=away,
        ))

        # Total bases
        tb_line = _round_half(sum(tb_vals[-lookback:]) / max(len(tb_vals[-lookback:]), 1))
        rows.extend(player_prop_rows(
            league="mlb", game_date=date_int, selector=selector,
            market="batter_bases", line=tb_line,
            p_over=prop_over_probability(tb_vals, tb_line, lookback,
                                         stat_std_override=std.get("batter_bases")),
            home=home, away=away,
        ))

        # Home runs (binary-ish)
        hr_line = 0.5
        rows.extend(player_prop_rows(
            league="mlb", game_date=date_int, selector=selector,
            market="batter_home_runs", line=hr_line,
            p_over=prop_over_probability(hr_vals, hr_line, lookback,
                                         use_poisson=True,
                                         stat_std_override=std.get("batter_home_runs")),
            home=home, away=away,
        ))

    for mlb_id in pitcher_ids:
        log_entries = mlb_client.fetch_pitcher_game_log(mlb_id, season, cache_dir)
        if not log_entries:
            continue

        k_vals = [e["strikeouts"] for e in log_entries]
        hit_vals = [e["hits"] for e in log_entries]
        er_vals = [e["earned_runs"] for e in log_entries]
        out_vals = [e["outs"] for e in log_entries]
        win_vals = [e["win"] for e in log_entries]

        selector = str(mlb_id)
        std = PROP_STD_DEV.get("mlb", {})

        # Strikeouts
        k_line = _round_half(
            sum(k_vals[-lookback:]) / max(len(k_vals[-lookback:]), 1)
        ) - 0.5
        k_line = max(k_line, 0.5)
        rows.extend(player_prop_rows(
            league="mlb", game_date=date_int, selector=selector,
            market="pitcher_strikeouts", line=k_line,
            p_over=prop_over_probability(k_vals, k_line, lookback,
                                         use_poisson=True,
                                         stat_std_override=std.get("pitcher_strikeouts")),
            home=home, away=away,
        ))

        # Pitcher win (yes/no)
        rows.extend(yes_no_prop_rows(
            league="mlb", game_date=date_int, selector=selector,
            market="pitcher_win", p_yes=prop_yes_probability(win_vals, lookback),
            home=home, away=away,
        ))

    return rows


# ---------------------------------------------------------------------------
# NBA / WNBA team props
# ---------------------------------------------------------------------------

def _nba_team_props(cfg, date_int, home, away, pred, dh) -> List[BrainRow]:
    rows = []
    for team_code, exp_pts in [(home, pred.expected_home_score), (away, pred.expected_away_score)]:
        line = _round_half(exp_pts)
        p_over = pred.home_score_prob(line, cfg) if team_code == home else pred.away_score_prob(line, cfg)
        rows.extend(team_prop_rows(
            league=cfg.brain_code, game_date=date_int,
            home=home, away=away, selector=team_code,
            market="points", line=line, p_over=p_over,
        ))
    return rows


# ---------------------------------------------------------------------------
# Elo bootstrap helpers
# ---------------------------------------------------------------------------

def _ensure_elo_initialized(cfg, store, ratings_path, cache_dir):
    if store.get("initialized", {}).get(cfg.brain_code):
        return
    log.info("Bootstrapping %s Elo ratings from standings...", cfg.name)
    try:
        records = espn_client.fetch_standings(cfg, cache_dir)
        if records:
            ratings_store.bootstrap_from_records(store, cfg.brain_code, records, ratings_path)
            log.info("Initialized %d %s teams.", len(records), cfg.name)
        else:
            log.warning("No standings data for %s — all teams start at %d.", cfg.name, INITIAL_ELO)
            store.setdefault("initialized", {})[cfg.brain_code] = True
    except Exception as e:
        log.warning("Standings bootstrap failed for %s: %s", cfg.name, e)
        store.setdefault("initialized", {})[cfg.brain_code] = True


# ---------------------------------------------------------------------------
# Misc helpers
# ---------------------------------------------------------------------------

def _round_half(x: float) -> float:
    """Round to nearest 0.5."""
    return round(x * 2) / 2


def _spread_market(cfg: LeagueConfig) -> str:
    return "spread"


def _total_market(cfg: LeagueConfig) -> str:
    if cfg.brain_code in ("nfl", "nba", "wnba"):
        return "total"
    if cfg.brain_code == "mlb":
        return "total"
    if cfg.brain_code == "epl":
        return "total"
    return "total"
