"""
Flask web server for the 8rain Station edge calculator.

Endpoints:
  GET /                  → serve the SPA (web/static/index.html)
  GET /api/predictions   → latest model CSV rows as JSON (all files in OUTPUT_DIR)
  GET /api/markets       → matched Kalshi + Polymarket odds keyed by game

Run via:
  python main.py web [--port 5000]
"""

import csv
import glob
import json
import logging
import os
from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from flask import request as flask_request

log = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"


def create_app(output_dir: str = "./output", kalshi_api_key: str | None = None) -> Flask:
    app = Flask(__name__, static_folder=str(STATIC_DIR))
    app.config["OUTPUT_DIR"] = output_dir
    app.config["KALSHI_API_KEY"] = kalshi_api_key

    @app.route("/")
    def index():
        return send_from_directory(str(STATIC_DIR), "index.html")

    @app.route("/api/predictions")
    def predictions():
        """Return all rows from the latest model CSV files as JSON."""
        out_dir = app.config["OUTPUT_DIR"]
        pattern = os.path.join(out_dir, "*.csv")
        files = sorted(glob.glob(pattern))

        rows = []
        for filepath in files:
            try:
                with open(filepath, newline="") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Normalise keys to lowercase with underscores
                        rows.append({
                            "league":     row.get("LEAGUE", "").lower(),
                            "date":       row.get("DATE", ""),
                            "home":       row.get("HOME", ""),
                            "away":       row.get("AWAY", ""),
                            "dh":         row.get("DOUBLEHEADER", ""),
                            "section":    row.get("SECTION", ""),
                            "market":     row.get("MARKET", ""),
                            "selector":   row.get("SELECTOR", ""),
                            "point":      row.get("POINT", ""),
                            "side":       row.get("SIDE", "").lower(),
                            "win_pct":    float(row.get("WIN %", 0) or 0),
                            "_file":      os.path.basename(filepath),
                        })
            except Exception as exc:
                log.warning("Could not read %s: %s", filepath, exc)

        return jsonify({"rows": rows, "files": [os.path.basename(f) for f in files]})

    @app.route("/api/markets")
    def markets():
        """
        Fetch Kalshi + Polymarket odds and match to today's games.

        Query params:
          ?leagues=nba,nfl,mlb  (filter; default all)
        """
        from web.kalshi_client import build_odds_map as kalshi_map
        from web.polymarket_client import build_odds_map as poly_map

        # Collect unique games from output directory
        out_dir = app.config["OUTPUT_DIR"]
        games: list[tuple] = []
        seen: set = set()
        for filepath in glob.glob(os.path.join(out_dir, "*.csv")):
            try:
                with open(filepath, newline="") as f:
                    for row in csv.DictReader(f):
                        league = row.get("LEAGUE", "").lower()
                        home = row.get("HOME", "")
                        away = row.get("AWAY", "")
                        game_date = row.get("DATE", "")
                        key = (league, home, away, game_date)
                        if key not in seen:
                            seen.add(key)
                            games.append(key)
            except Exception:
                pass

        api_key = app.config.get("KALSHI_API_KEY")
        try:
            k_odds = kalshi_map(games, api_key=api_key)
        except Exception as exc:
            log.error("Kalshi odds fetch failed: %s", exc)
            k_odds = {}

        try:
            p_odds = poly_map(games)
        except Exception as exc:
            log.error("Polymarket odds fetch failed: %s", exc)
            p_odds = {}

        return jsonify({"kalshi": k_odds, "polymarket": p_odds})

    @app.after_request
    def add_cors(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response

    return app
