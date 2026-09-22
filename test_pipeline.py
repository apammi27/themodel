import sys
import os

from data_fetcher.kalshi_client import KalshiClient
from data_fetcher.polymarket_client import PolymarketClient
from data_fetcher.csv_parser import parse_csv_content
from data_fetcher.matcher import match_model_rows
from data_fetcher.sample_data import DEFAULT_NFL_CSV

def run_test():
    print("==========================================================================")
    print("    8RAIN STATION EV CHECKER — PYTHON DATA FETCH & MATCHING SUITE      ")
    print("==========================================================================\n")

    print("[1/4] Parsing CSV input rows...")
    rows = parse_csv_content(DEFAULT_NFL_CSV)
    print(f"      -> Parsed {len(rows)} model prediction rows.\n")

    print("[2/4] Querying Kalshi REST API endpoints (targeted)...")
    kalshi_client = KalshiClient()
    k_res = kalshi_client.get_markets(target_rows=rows)
    print(f"      -> Kalshi returned {k_res['count']} targeted market items.")
    if k_res['error']:
        print(f"      -> Status: Kalshi {k_res['error']}")
    print()

    print("[3/4] Querying Polymarket Gamma REST API endpoints (targeted)...")
    poly_client = PolymarketClient()
    p_res = poly_client.get_markets(target_rows=rows)
    print(f"      -> Polymarket returned {p_res['count']} targeted market items.")
    if p_res['error']:
        print(f"      -> Status: Poly {p_res['error']}")
    print()

    print("[4/4] Executing line matching & EV calculations...\n")
    matched_lines = match_model_rows(rows, k_res['markets'], p_res['markets'])

    header = f"{'DATE':<8} | {'MATCHUP':<22} | {'MARKET':<12} | {'SIDE':<12} | {'MODEL %':<8} | {'KALSHI %':<9} | {'K EDGE':<8} | {'POLY %':<8} | {'P EDGE':<8} | {'½ KELLY':<8}"
    print(header)
    print("-" * len(header))

    for line in matched_lines:
        matchup = f"{line['home_team']} vs {line['away_team']}"
        print(f"{line['date_formatted']:<8} | {matchup:<22} | {line['market_display']:<12} | {line['side_display']:<12} | {line['model_prob_pct']:<8} | {line['kalshi_prob_pct']:<9} | {line['kalshi_edge_pct']:<8} | {line['poly_prob_pct']:<8} | {line['poly_edge_pct']:<8} | {line['half_kelly_pct']:<8}")

    print("\n==========================================================================")
    print("                      DATA MATCHING PIPELINE OK                           ")
    print("==========================================================================")

if __name__ == '__main__':
    run_test()
