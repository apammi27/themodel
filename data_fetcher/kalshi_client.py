import requests

class KalshiClient:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.base_url = "https://api.elections.kalshi.com/trade-api/v2"

    def get_markets(self, limit=250, target_rows=None):
        headers = {'Accept': 'application/json'}
        if self.api_key and self.api_key.strip():
            headers['Authorization'] = f"Bearer {self.api_key.strip()}"
            headers['Authorization-Key'] = self.api_key.strip()

        markets = []
        error = None

        if target_rows and isinstance(target_rows, list):
            series_to_query = set()
            for r in target_rows:
                league = (r.get('league') or 'NFL').upper()
                market = (r.get('market') or 'h2h').lower()
                section = (r.get('section') or '').lower()

                # Game line series
                if section in ['head_to_head', 'spread', 'total'] or market in ['h2h', 'spread', 'total']:
                    if league == 'NFL': series_to_query.update(['KXNFLGAME', 'KXNFLTOTAL', 'KXNFLSPREAD'])
                    elif league == 'MLB': series_to_query.update(['KXMLBGAME', 'KXMLBTOTAL', 'KXMLBSPREAD'])
                    elif league == 'NBA': series_to_query.update(['KXNBAGAME', 'KXNBATOTAL', 'KXNBASPREAD'])
                    elif league == 'NHL': series_to_query.update(['KXNHLGAME', 'KXNHLTOTAL', 'KXNHLSPREAD'])
                    elif league in ['EPL', 'SOCCER']: series_to_query.update(['KXEPLGAME', 'KXSOCCERSPREAD', 'KXEPLTOTAL'])

                # Player prop series
                if 'passing' in market: series_to_query.update(['KXNFLPASSYDS', 'KXNFLPASSTDS'])
                elif 'rushing' in market: series_to_query.update(['KXNFLRUSHYDS', 'KXNFLRUSHTDS'])
                elif 'receiving' in market or 'reception' in market: series_to_query.update(['KXNFLRECYDS', 'KXNFLRECTDS', 'KXNFLREC'])
                elif 'touchdown' in market: series_to_query.update(['KXNFLTD'])
                elif 'strikeout' in market or market == 'ks': series_to_query.update(['KXMLBKS'])
                elif 'hit' in market: series_to_query.update(['KXMLBHITS'])
                elif 'home_run' in market or market == 'hr': series_to_query.update(['KXMLBHR'])
                elif 'rbi' in market: series_to_query.update(['KXMLBRBI'])
                elif 'point' in market or market == 'pts':
                    if league == 'NFL': series_to_query.add('KXNFLFFPTS')
                    elif league == 'NBA': series_to_query.add('KXNBAPTS')
                    elif league == 'NHL': series_to_query.add('KXNHLPTS')
                elif 'rebound' in market: series_to_query.add('KXNBAREB')
                elif 'assist' in market:
                    if league == 'NBA': series_to_query.add('KXNBAAST')
                    elif league == 'NHL': series_to_query.add('KXNHLAST')
                elif 'goal' in market: series_to_query.add('KXNHLGOALS')

            sports_series = list(series_to_query) if series_to_query else [
                'KXNFLGAME', 'KXMLBGAME', 'KXNBAGAME', 'KXNHLGAME', 'KXEPLGAME',
                'KXNFLTOTAL', 'KXMLBTOTAL', 'KXNBATOTAL', 'KXNHLTOTAL',
                'KXNFLSPREAD', 'KXMLBSPREAD', 'KXNBASPREAD', 'KXNHLSPREAD'
            ]
        else:
            sports_series = [
                'KXNFLGAME', 'KXMLBGAME', 'KXNBAGAME', 'KXNHLGAME', 'KXEPLGAME',
                'KXNFLTOTAL', 'KXMLBTOTAL', 'KXNBATOTAL', 'KXNHLTOTAL',
                'KXNFLSPREAD', 'KXMLBSPREAD', 'KXNBASPREAD', 'KXNHLSPREAD',
                'KXNFLPASSYDS', 'KXNFLRUSHYDS', 'KXNFLRECYDS', 'KXNFLTD',
                'KXNBAPTS', 'KXMLBKS', 'KXNHLPTS'
            ]

        for s in sports_series:
            try:
                url = f"{self.base_url}/markets?series_ticker={s}&status=open&limit=200"
                res = requests.get(url, headers=headers, timeout=6)
                if res.status_code == 200:
                    markets.extend(res.json().get('markets', []))
            except Exception:
                pass

        unique = {}
        for m in markets:
            if m and m.get('ticker'):
                unique[m['ticker']] = m

        normalized = []
        for m in unique.values():
            ticker = m.get('ticker', '')
            title = m.get('title', '')
            event_ticker = m.get('event_ticker', '')
            series_ticker = m.get('series_ticker') or (ticker.split('-')[0] if '-' in ticker else '')
            floor_strike = m.get('floor_strike')
            cap_strike = m.get('cap_strike')

            price = None
            for key in ['yes_ask_dollars', 'last_price_dollars', 'yes_bid_dollars']:
                val = m.get(key)
                if val is not None and float(val) > 0:
                    price = float(val)
                    break
            if price is None:
                for key in ['yes_ask', 'last_price', 'yes_bid']:
                    val = m.get(key)
                    if val is not None and float(val) > 0:
                        v = float(val)
                        price = v / 100.0 if v > 1.0 else v
                        break

            if series_ticker and event_ticker:
                url = f"https://kalshi.com/markets/{series_ticker.lower()}/{event_ticker.lower()}"
            else:
                url = f"https://kalshi.com/markets/{ticker.lower()}"

            normalized.append({
                'id': f"kalshi-{ticker}",
                'exchange': 'kalshi',
                'ticker': ticker,
                'series_ticker': series_ticker.upper(),
                'event_ticker': event_ticker.upper(),
                'title': title,
                'subtitle': m.get('subtitle', ''),
                'floor_strike': floor_strike,
                'cap_strike': cap_strike,
                'price': price,
                'yes_ask_dollars': price,
                'url': url
            })

        return {
            'markets': normalized,
            'count': len(normalized),
            'error': error if len(normalized) == 0 else None
        }

def fetch_kalshi_markets(api_key=None, target_rows=None):
    client = KalshiClient(api_key=api_key)
    res = client.get_markets(target_rows=target_rows)
    return res['markets']
