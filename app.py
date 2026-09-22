import os
import json
from flask import Flask, render_template, request, jsonify
from data_fetcher.csv_parser import parse_csv_content
from data_fetcher.sample_data import DEFAULT_NFL_CSV as DEFAULT_CSV
from data_fetcher.kalshi_client import fetch_kalshi_markets
from data_fetcher.polymarket_client import fetch_polymarket_markets
from data_fetcher.matcher import match_model_rows

app = Flask(__name__, static_folder='static', template_folder='templates')

# Cache markets in memory to reduce rate limiting during rapid UI filter tweaks
market_cache = {
    "kalshi": [],
    "polymarket": [],
    "kalshi_status": "disconnected",
    "poly_status": "disconnected",
    "last_fetched": None
}

@app.route('/')
def index():
    return render_template('index.html', default_csv=DEFAULT_CSV)

@app.route('/api/calculate', methods=['POST'])
def calculate_ev():
    data = request.get_json(silent=True) or {}
    csv_text = data.get('csv_text', DEFAULT_CSV)
    kalshi_key = data.get('kalshi_key', '')
    force_refresh = data.get('force_refresh', False)

    # Parse CSV rows
    rows = parse_csv_content(csv_text)

    # Fetch live targeted markets
    kalshi_markets = fetch_kalshi_markets(api_key=kalshi_key, target_rows=rows)
    poly_markets = fetch_polymarket_markets(target_rows=rows)
    
    market_cache["kalshi"] = kalshi_markets
    market_cache["polymarket"] = poly_markets
    market_cache["kalshi_status"] = "connected" if len(kalshi_markets) > 0 else "error"
    market_cache["poly_status"] = "connected" if len(poly_markets) > 0 else "error"

    # Run matching & EV calculations
    matched_lines = match_model_rows(rows, market_cache["kalshi"], market_cache["polymarket"])

    return jsonify({
        "success": True,
        "row_count": len(matched_lines),
        "kalshi_count": len(market_cache["kalshi"]),
        "poly_count": len(market_cache["polymarket"]),
        "kalshi_status": market_cache["kalshi_status"],
        "poly_status": market_cache["poly_status"],
        "lines": matched_lines
    })

@app.route('/api/health')
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"Starting 8rain Station EV Checker on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
