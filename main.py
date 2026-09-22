#!/usr/bin/env python3
"""
8rain Station Advantage Betting Model
======================================
Daily-use CLI that produces 8rain Station–formatted CSV predictions.

Usage examples
--------------
# All sports for today:
    python main.py run

# Specific sports:
    python main.py run --sports nba,mlb

# Specific date:
    python main.py run --date 2025-04-15

# MLB with player props (provide batter & pitcher IDs):
    python main.py run --sports mlb --batters 592450,660271 --pitchers 543037

# Update Elo ratings from yesterday's completed games:
    python main.py update-elo

# Print the current Elo ratings table:
    python main.py ratings

# Reset (re-bootstrap) Elo for a league:
    python main.py reset --sports nba
"""

import json
import logging
import os
import sys
from datetime import date, timedelta
from typing import List, Optional

import click
from dotenv import load_dotenv

load_dotenv()

from config import LEAGUES
from models.daily_runner import run_daily
from models.demo_runner import run_demo
from output.formatter import write_csv, rows_to_csv
from storage import ratings_store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("main")

# --- Defaults from environment ---
DEFAULT_OUTPUT = os.getenv("OUTPUT_DIR", "./output")
DEFAULT_CACHE = os.getenv("CACHE_DIR", "./.cache")
DEFAULT_RATINGS = os.getenv("RATINGS_FILE", "./storage/ratings.json")
DEFAULT_LOOKBACK = int(os.getenv("PROP_LOOKBACK", "15"))
ALL_LEAGUES = list(LEAGUES.keys())


def parse_date(d: str) -> date:
    from datetime import datetime
    return datetime.strptime(d, "%Y-%m-%d").date()


@click.group()
def cli():
    """8rain Station advantage betting model."""


@cli.command()
@click.option("--sports", default="nba,nfl,mlb,wnba,epl",
              help="Comma-separated list of sports (nba, nfl, mlb, wnba, epl)")
@click.option("--date", "game_date", default=None,
              help="Date in YYYY-MM-DD format (default: today)")
@click.option("--output", default=DEFAULT_OUTPUT, help="Output directory for CSV files")
@click.option("--cache", default=DEFAULT_CACHE, help="Cache directory")
@click.option("--ratings", default=DEFAULT_RATINGS, help="Ratings JSON file path")
@click.option("--lookback", default=DEFAULT_LOOKBACK, type=int,
              help="Games to look back for player props")
@click.option("--batters", default="",
              help="Comma-separated MLB batter IDs (mlbids) for player props")
@click.option("--pitchers", default="",
              help="Comma-separated MLB pitcher IDs (mlbids) for player props")
@click.option("--print", "print_csv", is_flag=True,
              help="Print CSV to stdout instead of writing to file")
@click.option("--demo", is_flag=True,
              help="Use built-in demo data (no network required)")
def run(sports, game_date, output, cache, ratings, lookback, batters, pitchers, print_csv, demo):
    """Generate predictions for a given date and write CSV output."""
    leagues = [s.strip().lower() for s in sports.split(",") if s.strip()]
    target_date = parse_date(game_date) if game_date else date.today()

    # Build player ID dict for MLB props
    mlb_player_ids = None
    batter_list = [int(x) for x in batters.split(",") if x.strip().isdigit()]
    pitcher_list = [int(x) for x in pitchers.split(",") if x.strip().isdigit()]
    if batter_list or pitcher_list:
        mlb_player_ids = {"batters": batter_list, "pitchers": pitcher_list}

    if demo:
        log.info("DEMO MODE — using built-in sample data (no network calls)")
    log.info("Running model for %s | sports: %s", target_date, leagues)

    if demo:
        rows = run_demo(leagues=leagues, game_date=target_date, ratings_path=ratings)
    else:
        rows = run_daily(
            leagues=leagues,
            game_date=target_date,
            ratings_path=ratings,
            cache_dir=cache,
            prop_lookback=lookback,
            mlb_player_ids=mlb_player_ids,
        )

    if not rows:
        log.warning("No predictions generated. Are there games scheduled for %s?", target_date)
        return

    log.info("Generated %d prediction rows.", len(rows))

    if print_csv:
        click.echo(rows_to_csv(rows))
        return

    # Write one CSV per league
    by_league = {}
    for row in rows:
        by_league.setdefault(row.league.lower(), []).append(row)

    os.makedirs(output, exist_ok=True)
    for league, league_rows in by_league.items():
        fname = os.path.join(output, f"{league}_{target_date.strftime('%Y%m%d')}.csv")
        write_csv(league_rows, fname)
        click.echo(f"  ✓  {league.upper():5s}  →  {fname}  ({len(league_rows)} rows)")


@cli.command("update-elo")
@click.option("--date", "game_date", default=None,
              help="Date of completed games to update from (default: yesterday)")
@click.option("--sports", default=",".join(ALL_LEAGUES))
@click.option("--cache", default=DEFAULT_CACHE)
@click.option("--ratings", default=DEFAULT_RATINGS)
def update_elo_cmd(game_date, sports, cache, ratings):
    """Update Elo ratings from completed games on a given date."""
    target_date = parse_date(game_date) if game_date else date.today() - timedelta(days=1)
    leagues = [s.strip().lower() for s in sports.split(",") if s.strip()]
    log.info("Updating Elo from %s completed games...", target_date)

    # run_daily with today's date automatically updates Elo from any completed games
    run_daily(
        leagues=leagues,
        game_date=target_date,
        ratings_path=ratings,
        cache_dir=cache,
    )
    log.info("Elo ratings updated.")


@cli.command()
@click.option("--sports", default=",".join(ALL_LEAGUES))
@click.option("--ratings", default=DEFAULT_RATINGS)
@click.option("--top", default=0, type=int,
              help="Show top N teams per league (0 = all)")
def ratings(sports, ratings, top):
    """Print current Elo ratings for each league."""
    store = ratings_store.load(ratings)
    leagues = [s.strip().lower() for s in sports.split(",") if s.strip()]
    for league in leagues:
        team_ratings = store.get("ratings", {}).get(league, {})
        if not team_ratings:
            click.echo(f"\n{league.upper()}: no ratings (run `python main.py run` first)")
            continue
        sorted_teams = sorted(team_ratings.items(), key=lambda x: x[1], reverse=True)
        if top:
            sorted_teams = sorted_teams[:top]
        click.echo(f"\n{league.upper()} Elo Ratings:")
        click.echo(f"{'Team':6s}  {'Elo':>7s}")
        click.echo("-" * 16)
        for team, elo in sorted_teams:
            click.echo(f"{team:6s}  {elo:7.1f}")


@cli.command()
@click.option("--sports", default=",".join(ALL_LEAGUES))
@click.option("--ratings", default=DEFAULT_RATINGS)
@click.option("--cache", default=DEFAULT_CACHE)
def reset(sports, ratings, cache):
    """Re-bootstrap Elo ratings for leagues from current standings."""
    leagues = [s.strip().lower() for s in sports.split(",") if s.strip()]
    store = ratings_store.load(ratings)
    for league in leagues:
        store.setdefault("initialized", {})[league] = False
    ratings_store.save(store, ratings)
    log.info("Reset flags cleared; ratings will re-bootstrap on next `run`.")


@cli.command()
@click.option("--sports", default=",".join(ALL_LEAGUES))
@click.option("--ratings", default=DEFAULT_RATINGS)
def regress(sports, ratings):
    """Apply end-of-season regression to mean for all Elo ratings."""
    leagues = [s.strip().lower() for s in sports.split(",") if s.strip()]
    store = ratings_store.load(ratings)
    for league in leagues:
        ratings_store.apply_season_regression(store, league)
        log.info("Regressed %s Elo ratings to mean.", league.upper())
    ratings_store.save(store, ratings)


@cli.command()
@click.option("--port", default=5000, type=int, help="Port to listen on")
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--output", default=DEFAULT_OUTPUT, help="Model output directory to read CSVs from")
@click.option("--kalshi-key", default=None, envvar="KALSHI_API_KEY",
              help="Kalshi API key (optional; public market data works without one)")
def web(port, host, output, kalshi_key):
    """Start the edge-calculator web UI (reads model output + live Kalshi/Polymarket odds)."""
    from web.server import create_app
    app = create_app(output_dir=output, kalshi_api_key=kalshi_key)
    url = f"http://{host}:{port}"
    click.echo(f"\n  8rain Weightings running at  {url}\n")
    click.echo("  → Run the model first:  python main.py run")
    click.echo("  → Then open the URL above to see predictions + live market odds.\n")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    cli()
