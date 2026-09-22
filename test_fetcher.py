import sys
import json
import re
import requests

# Canonical Team Mappings for Sports
TEAM_MAPPINGS = {
    'KC': {'name': 'Kansas City Chiefs', 'city': 'Kansas City', 'mascot': 'Chiefs', 'aliases': ['KC', 'CHIEFS', 'KANSAS CITY']},
    'BUF': {'name': 'Buffalo Bills', 'city': 'Buffalo', 'mascot': 'Bills', 'aliases': ['BUF', 'BILLS', 'BUFFALO']},
    'PIT': {'name': 'Pittsburgh Steelers', 'city': 'Pittsburgh', 'mascot': 'Steelers', 'aliases': ['PIT', 'STEELERS', 'PITTSBURGH']},
    'CIN': {'name': 'Cincinnati Bengals', 'city': 'Cincinnati', 'mascot': 'Bengals', 'aliases': ['CIN', 'BENGALS', 'CINCINNATI']},
    'SF': {'name': 'San Francisco 49ers', 'city': 'San Francisco', 'mascot': '49ers', 'aliases': ['SF', '49ERS', 'NINERS', 'SAN FRANCISCO']},
    'ARI': {'name': 'Arizona Cardinals', 'city': 'Arizona', 'mascot': 'Cardinals', 'aliases': ['ARI', 'CARDINALS', 'ARIZONA']},
    'IND': {'name': 'Indianapolis Colts', 'city': 'Indianapolis', 'mascot': 'Colts', 'aliases': ['IND', 'COLTS', 'INDIANAPOLIS']},
    'HOU': {'name': 'Houston Texans', 'city': 'Houston', 'mascot': 'Texans', 'aliases': ['HOU', 'TEXANS', 'HOUSTON']},
    'LAC': {'name': 'Los Angeles Chargers', 'city': 'Los Angeles', 'mascot': 'Chargers', 'aliases': ['LAC', 'CHARGERS', 'LA CHARGERS']},
    'CLE': {'name': 'Cleveland Browns', 'city': 'Cleveland', 'mascot': 'Browns', 'aliases': ['CLE', 'BROWNS', 'CLEVELAND']},
    'CAR': {'name': 'Carolina Panthers', 'city': 'Carolina', 'mascot': 'Panthers', 'aliases': ['CAR', 'PANTHERS', 'CAROLINA']},
    'COL': {'name': 'Colorado Rockies', 'city': 'Colorado', 'mascot': 'Rockies', 'aliases': ['COL', 'ROCKIES', 'COLORADO']},
    'MIL': {'name': 'Milwaukee Brewers', 'city': 'Milwaukee', 'mascot': 'Brewers', 'aliases': ['MIL', 'BREWERS', 'MILWAUKEE']},
    'BOS': {'name': 'Boston Celtics', 'city': 'Boston', 'mascot': 'Celtics', 'aliases': ['BOS', 'CELTICS', 'BOSTON']},
}

def get_team_info(code):
    if not code:
        return None
    code_upper = code.strip().upper()
    return TEAM_MAPPINGS.get(code_upper, {'name': code_upper, 'city': code_upper, 'mascot': code_upper, 'aliases': [code_upper]})

class KalshiClient:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.base_url = "https://api.elections.kalshi.com/trade-api/v2"

    def get_markets(self, limit=200):
        headers = {'Accept': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f"Bearer {self.api_key}"
            headers['Authorization-Key'] = self.api_key

        markets = []
        # Query general active markets
        try:
            url = f"{self.base_url}/markets?limit={limit}&status=active"
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                markets.extend(res.json().get('markets', []))
        except Exception as e:
            print(f"[Kalshi Error] {e}")

        # Query specific sports series
        series_list = ['KXNFLGAME', 'KXMLBGAME', 'KXNBAGAME', 'KXNHLGAME', 'KXNFL', 'KXMLB', 'KXNBA', 'KXNHL']
        for s in series_list:
            try:
                url = f"{self.base_url}/markets?series_ticker={s}"
                res = requests.get(url, headers=headers, timeout=5)
                if res.status_code == 200:
                    markets.extend(res.json().get('markets', []))
            except Exception:
                pass

        # Deduplicate
        unique = {}
        for m in markets:
            if m.get('ticker'):
                unique[m['ticker']] = m
        return list(unique.values())

class PolymarketClient:
    def __init__(self):
        self.gamma_url = "https://gamma-api.polymarket.com"

    def get_markets(self, limit=300):
        markets = []
        try:
            url = f"{self.gamma_url}/markets?limit={limit}&active=true&closed=false"
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list):
                    markets.extend(data)
        except Exception as e:
            print(f"[Polymarket Markets Error] {e}")

        try:
            url = f"{self.gamma_url}/events?limit=200&closed=false"
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                events = res.json()
                if isinstance(events, list):
                    for ev in events:
                        sub = ev.get('markets', [])
                        if isinstance(sub, list):
                            markets.extend(sub)
        except Exception as e:
            print(f"[Polymarket Events Error] {e}")

        return markets

def match_row_to_exchange(row, exchange_markets, is_kalshi=True):
    home_info = get_team_info(row.get('home'))
    away_info = get_team_info(row.get('away'))

    best_match = None
    best_score = 0

    for m in exchange_markets:
        if is_kalshi:
            title = (m.get('title', '') + ' ' + m.get('ticker', '')).upper()
            sub = (m.get('no_sub_title', '') + ' ' + m.get('yes_sub_title', '')).upper()
            full_text = f"{title} {sub}"
        else:
            full_text = (m.get('question', '') + ' ' + m.get('slug', '') + ' ' + m.get('groupItemTitle', '')).upper()

        score = 0
        has_home = any(a in full_text for a in home_info['aliases']) if home_info else False
        has_away = any(a in full_text for a in away_info['aliases']) if away_info else False

        if has_home and has_away:
            score += 80
        elif has_home or has_away:
            score += 40

        if score > best_score and score >= 80:
            best_score = score;
            best_match = m

    if not best_match:
        return None

    # Extract price
    price = 0.5
    if is_kalshi:
        if best_match.get('yes_ask_dollars') is not None:
            price = float(best_match['yes_ask_dollars'])
        elif best_match.get('yes_ask') is not None:
            ask = float(best_match['yes_ask'])
            price = ask / 100.0 if ask > 1 else ask
        elif best_match.get('last_price_dollars') is not None:
            price = float(best_match['last_price_dollars'])
    else:
        prices = [0.5, 0.5]
        try:
            op = best_match.get('outcomePrices')
            if isinstance(op, str):
                prices = [float(x) for x in json.loads(op)]
            elif isinstance(op, list):
                prices = [float(x) for x in op]
        except Exception:
            pass

        best_ask = float(best_match.get('bestAsk') or 0)
        price = best_ask if best_ask > 0 else prices[0]

    return {
        'title': best_match.get('title') or best_match.get('question') or best_match.get('ticker'),
        'ticker': best_match.get('ticker') or best_match.get('slug'),
        'price': price,
        'implied_prob_pct': f"{price * 100:.1f}%",
        'url': f"https://kalshi.com/markets/{best_match.get('ticker')}" if is_kalshi else f"https://polymarket.com/market/{best_match.get('slug')}"
    }

def test_data_pipeline():
    print("==========================================================================")
    print("    PYTHON 8RAIN STATION LIVE MARKET DATA FETCH & VERIFICATION TEST    ")
    print("==========================================================================\n")

    print("[1/3] Initializing Kalshi and Polymarket Python API Clients...")
    kalshi = KalshiClient()
    polymarket = PolymarketClient()

    print("[2/3] Fetching live market feeds from Kalshi and Polymarket REST APIs...")
    k_markets = kalshi.get_markets()
    p_markets = polymarket.get_markets()
    print(f"      -> Kalshi returned {len(k_markets)} market items.")
    print(f"      -> Polymarket returned {len(p_markets)} market items.\n")

    # Sample 8rain CSV rows
    test_rows = [
        {'league': 'NFL', 'date': '20260927', 'home': 'Steelers', 'away': 'Bengals', 'market': 'h2h', 'side': 'home', 'model_prob': 0.626},
        {'league': 'NFL', 'date': '20260927', 'home': 'Steelers', 'away': 'Bengals', 'market': 'h2h', 'side': 'away', 'model_prob': 0.374},
        {'league': 'NFL', 'date': '20260927', 'home': '49ers', 'away': 'Cardinals', 'market': 'h2h', 'side': 'away', 'model_prob': 0.089},
        {'league': 'NFL', 'date': '20260927', 'home': '49ers', 'away': 'Cardinals', 'market': 'h2h', 'side': 'home', 'model_prob': 0.911},
        {'league': 'NFL', 'date': '20260927', 'home': 'Colts', 'away': 'Texans', 'market': 'h2h', 'side': 'home', 'model_prob': 0.509},
        {'league': 'MLB', 'date': '20250410', 'home': 'COL', 'away': 'MIL', 'market': 'h2h', 'side': 'away', 'model_prob': 0.580},
    ]

    print("[3/3] Cross-referencing model picks against live exchange contracts...\n")

    for i, row in enumerate(test_rows, 1):
        print(f"--- [ROW {i}] {row['league']} {row['date']} | {row['home']} vs {row['away']} | {row['market'].upper()} {row['side'].upper()} | Model Prob: {row['model_prob']*100:.1f}% ---")

        k_match = match_row_to_exchange(row, k_markets, is_kalshi=True)
        if k_match:
            edge = (row['model_prob'] - k_match['price']) * 100
            print(f"  ✓ KALSHI MATCH: {k_match['title']} | Price: ${k_match['price']:.2f} ({k_match['implied_prob_pct']}) | K Edge: {edge:+.1f}%")
        else:
            print("  ✗ KALSHI: Unmatched / Off-board")

        p_match = match_row_to_exchange(row, p_markets, is_kalshi=False)
        if p_match:
            edge = (row['model_prob'] - p_match['price']) * 100
            print(f"  ✓ POLYMARKET MATCH: {p_match['title']} | Price: ${p_match['price']:.3f} ({p_match['implied_prob_pct']}) | P Edge: {edge:+.1f}%")
        else:
            print("  ✗ POLYMARKET: Unmatched / Off-board")

        print()

if __name__ == '__main__':
    test_data_pipeline()
