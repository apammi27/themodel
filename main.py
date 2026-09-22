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

# Run model + live Kalshi/Polymarket edge table (prints to terminal):
    python main.py edge --date 2025-04-15
    python main.py edge --date 2025-04-15 --sports nba,mlb
    python main.py edge --ev-only
    python main.py edge --min-edge 0.03
    python main.py edge --demo
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
@click.option("--sports", default="nba,nfl,mlb,wnba,epl")
@click.option("--date", "game_date", default=None, help="Date in YYYY-MM-DD format (default: today)")
@click.option("--ratings", default=DEFAULT_RATINGS)
@click.option("--cache", default=DEFAULT_CACHE)
@click.option("--lookback", default=DEFAULT_LOOKBACK, type=int)
@click.option("--demo", is_flag=True, help="Use built-in demo data (no network required for model)")
@click.option("--ev-only", is_flag=True, help="Only show rows with positive edge on at least one platform")
@click.option("--min-edge", default=0.0, type=float,
              help="Minimum edge threshold to display (e.g. 0.03 = show only 3 %+ edges)")
@click.option("--kalshi-key", default=None, envvar="KALSHI_API_KEY")
def edge(sports, game_date, ratings, cache, lookback, demo, ev_only, min_edge, kalshi_key):
    """Run model + fetch live Kalshi/Polymarket odds and print edge table to terminal."""
    from web.kalshi_client import build_odds_map as kalshi_map
    from web.polymarket_client import build_odds_map as poly_map

    leagues = [s.strip().lower() for s in sports.split(",") if s.strip()]
    target_date = parse_date(game_date) if game_date else date.today()

    log.info("Running model for %s | sports: %s", target_date, leagues)
    if demo:
        rows = run_demo(leagues=leagues, game_date=target_date, ratings_path=ratings)
    else:
        rows = run_daily(
            leagues=leagues, game_date=target_date, ratings_path=ratings,
            cache_dir=cache, prop_lookback=lookback,
        )

    if not rows:
        click.echo(f"No predictions generated for {target_date}.")
        return

    # Collect unique games for market lookup
    games: list[tuple] = []
    seen: set = set()
    for r in rows:
        key = (r.league.lower(), r.home, r.away, str(r.date))
        if key not in seen:
            seen.add(key)
            games.append(key)

    log.info("Fetching Kalshi markets…")
    try:
        k_odds = kalshi_map(games, api_key=kalshi_key)
    except Exception as exc:
        log.warning("Kalshi fetch failed: %s", exc)
        k_odds = {}

    log.info("Fetching Polymarket markets…")
    try:
        p_odds = poly_map(games)
    except Exception as exc:
        log.warning("Polymarket fetch failed: %s", exc)
        p_odds = {}

    def game_key(r):
        return f"{r.league.upper()}|{r.date}|{r.home}|{r.away}"

    def mkt_prob(oddsmap, r):
        m = oddsmap.get(game_key(r))
        if not m or not m.get("matched"):
            return None
        return m.get("home_prob") if r.side == "home" else m.get("away_prob") if r.side == "away" else None

    def edge_val(model_p, mkt_p):
        return round(model_p - mkt_p, 4) if mkt_p is not None else None

    def half_kelly(model_p, mkt_p):
        if mkt_p is None or mkt_p <= 0 or mkt_p >= 1:
            return None
        b = (1 / mkt_p) - 1
        f = (b * model_p - (1 - model_p)) / b
        return round(f / 2, 4) if f > 0 else None

    def fmt_pct(v):
        return f"{v*100:5.1f}%" if v is not None else "   — "

    def fmt_edge(v):
        if v is None:
            return "    — "
        sign = "+" if v >= 0 else ""
        return f"{sign}{v*100:.1f}%"

    def fmt_kelly(v):
        return f"{v*100:.1f}%" if v is not None else "—"

    # Filter and sort
    display_rows = []
    for r in rows:
        if r.market not in ("h2h", "spread", "total", "team_prop"):
            continue  # skip player props for now
        kp = mkt_prob(k_odds, r)
        pp = mkt_prob(p_odds, r)
        ke = edge_val(r.win_pct, kp)
        pe = edge_val(r.win_pct, pp)
        kk = half_kelly(r.win_pct, kp)
        pk = half_kelly(r.win_pct, pp)

        if ev_only:
            if not ((ke is not None and ke > 0) or (pe is not None and pe > 0)):
                continue
        if min_edge > 0:
            best = max((e for e in [ke, pe] if e is not None), default=None)
            if best is None or best < min_edge:
                continue

        display_rows.append((r, kp, ke, kk, pp, pe, pk))

    if not display_rows:
        click.echo("No rows match the filters. Try removing --ev-only or --min-edge.")
        return

    # Sort by best edge descending
    display_rows.sort(
        key=lambda x: max((e for e in [x[2], x[5]] if e is not None), default=-99),
        reverse=True,
    )

    # ── Print table ──────────────────────────────────────────────────────────
    MARKET_LABELS = {"h2h": "ML", "spread": "Spread", "total": "Total",
                     "team_prop": "Team", "player_prop": "Prop"}

    W_LEAGUE = 5
    W_GAME   = 14
    W_MKT    = 7
    W_SIDE   = 5
    W_LINE   = 6
    W_MODEL  = 7
    W_KPROB  = 7
    W_KEDGE  = 7
    W_KK     = 6
    W_PPROB  = 7
    W_PEDGE  = 7
    W_PK     = 6

    def col(s, w, align="<"):
        return f"{str(s):{align}{w}}"

    hdr = (
        col("LEAG",  W_LEAGUE) + "  " +
        col("GAME",  W_GAME)   + "  " +
        col("MKT",   W_MKT)    + "  " +
        col("SIDE",  W_SIDE)   + "  " +
        col("LINE",  W_LINE)   + "  " +
        col("MODEL", W_MODEL, ">") + "  " +
        col("K%",    W_KPROB,  ">") + "  " +
        col("K EDGE",W_KEDGE,  ">") + "  " +
        col("K ½K",  W_KK,     ">") + "  " +
        col("P%",    W_PPROB,  ">") + "  " +
        col("P EDGE",W_PEDGE,  ">") + "  " +
        col("P ½K",  W_PK,     ">")
    )
    divider = "─" * len(hdr)

    click.echo(f"\n  8rain Station® Edge Report — {target_date}  ({len(display_rows)} rows)\n")
    click.echo("  " + hdr)
    click.echo("  " + divider)

    for r, kp, ke, kk, pp, pe, pk in display_rows:
        game_str = f"{r.home}/{r.away}"
        line_str = f"{r.point:+g}" if r.point not in ("", None) else "—"
        mkt_label = MARKET_LABELS.get(r.market, r.market)

        def edge_str(e, k):
            if e is None:
                return col("—", W_KEDGE, ">"), col("—", W_KK, ">")
            sign = "+" if e >= 0 else ""
            ek = f"{sign}{e*100:.1f}%"
            kstr = fmt_kelly(k)
            return col(ek, W_KEDGE, ">"), col(kstr, W_KK, ">")

        k_edge_s, k_k_s = edge_str(ke, kk)
        p_edge_s, p_k_s = edge_str(pe, pk)

        line = (
            col(r.league.upper(), W_LEAGUE) + "  " +
            col(game_str[:W_GAME], W_GAME)  + "  " +
            col(mkt_label,  W_MKT)          + "  " +
            col(r.side[:W_SIDE], W_SIDE)    + "  " +
            col(line_str,   W_LINE)         + "  " +
            col(fmt_pct(r.win_pct), W_MODEL, ">") + "  " +
            col(fmt_pct(kp), W_KPROB, ">") + "  " +
            k_edge_s + "  " + k_k_s         + "  " +
            col(fmt_pct(pp), W_PPROB, ">") + "  " +
            p_edge_s + "  " + p_k_s
        )
        click.echo("  " + line)

    click.echo("  " + divider)

    # Summary
    k_ev = sum(1 for _, _, ke, _, _, _, _ in display_rows if ke is not None and ke > 0)
    p_ev = sum(1 for _, _, _, _, _, pe, _ in display_rows if pe is not None and pe > 0)
    k_matched = sum(1 for _, kp, _, _, _, _, _ in display_rows if kp is not None)
    p_matched = sum(1 for _, _, _, _, pp, _, _ in display_rows if pp is not None)
    click.echo(f"\n  Kalshi:     {k_matched} matched, {k_ev} +EV")
    click.echo(f"  Polymarket: {p_matched} matched, {p_ev} +EV")
    click.echo()


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
