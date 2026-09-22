import requests
import json

FUTURES_KEYWORDS = [
    'winner', 'cup', 'champion', 'championship', 'futures', 'mvp', 'playoffs',
    'super-bowl', 'division', 'draft', 'award', 'season', 'series', 'outright',
    'relegation', 'top-scorer', 'ballon-dor', 'trophy'
]

class PolymarketClient:
    def __init__(self):
        self.base_url = "https://gamma-api.polymarket.com"
        self.data_v2_url = "https://data-api.polymarket.com/v2"

    def fetch_v2_trades_price(self, condition_id):
        if not condition_id:
            return None
        try:
            url = f"{self.data_v2_url}/trades?condition={condition_id}&limit=3"
            res = requests.get(url, timeout=3)
            if res.status_code == 200:
                trades = res.json().get('data', [])
                if trades and isinstance(trades, list):
                    last_trade = trades[0]
                    trade_price = last_trade.get('price')
                    if trade_price is not None:
                        return float(trade_price)
        except Exception:
            pass
        return None

    def get_markets(self, limit=500, target_rows=None):
        raw_markets = []
        error = None

        target_tags = set()
        target_players = set()

        if target_rows and isinstance(target_rows, list):
            for r in target_rows:
                league = (r.get('league') or 'nfl').lower()
                target_tags.add(league)
                if league == 'epl': target_tags.add('soccer')
                elif league in ['cfb', 'ncaaf']: target_tags.add('college-football')
                elif league in ['cbb', 'ncaab']: target_tags.add('college-basketball')

                selector = (r.get('selector') or '').strip()
                section = (r.get('section') or '').lower()
                if section == 'player_prop' and selector and len(selector) >= 3:
                    target_players.add(selector)

            sports_slugs = list(target_tags)
        else:
            sports_slugs = ['nfl', 'mlb', 'nba', 'soccer', 'epl', 'nhl', 'wnba', 'tennis', 'ufc']

        for tag in sports_slugs:
            try:
                url = f"{self.base_url}/events?tag_slug={tag}&active=true&closed=false&limit=100"
                res = requests.get(url, timeout=10)
                if res.status_code == 200:
                    events = res.json()
                    if isinstance(events, list):
                        for ev in events:
                            if ev.get('closed', False) or not ev.get('active', True):
                                continue
                            ev_title = ev.get('title', '')
                            ev_slug = ev.get('slug', '')
                            
                            mkts = ev.get('markets', [])
                            if isinstance(mkts, list):
                                for m in mkts:
                                    if m.get('closed', False) or not m.get('active', True):
                                        continue
                                    m['event_title'] = ev_title
                                    m['event_slug'] = ev_slug
                                    raw_markets.append(m)
            except Exception as e:
                error = str(e)

        # Query player-specific markets for player props
        for player in target_players:
            try:
                player_query = player.replace(' ', '+')
                url = f"{self.base_url}/events?query={player_query}&active=true&closed=false&limit=20"
                res = requests.get(url, timeout=5)
                if res.status_code == 200:
                    events = res.json()
                    if isinstance(events, list):
                        for ev in events:
                            ev_title = ev.get('title', '')
                            ev_slug = ev.get('slug', '')
                            for m in ev.get('markets', []):
                                m['event_title'] = ev_title
                                m['event_slug'] = ev_slug
                                raw_markets.append(m)
            except Exception:
                pass

        # Deduplicate and normalize
        unique = {}
        for m in raw_markets:
            m_id = m.get('id') or m.get('conditionId')
            if m_id and m_id not in unique:
                unique[m_id] = m

        normalized = []
        for m in unique.values():
            m_id = m.get('id') or m.get('conditionId')
            condition_id = m.get('conditionId') or m_id
            question = m.get('question') or m.get('groupItemTitle') or m.get('event_title') or ''
            slug = m.get('slug') or m.get('event_slug') or m_id
            event_title = m.get('event_title') or ''
            event_slug = m.get('event_slug') or ''

            outcomes = ['Yes', 'No']
            try:
                if isinstance(m.get('outcomes'), str):
                    outcomes = json.loads(m['outcomes'])
                elif isinstance(m.get('outcomes'), list):
                    outcomes = m['outcomes']
            except Exception:
                pass

            prices = []
            try:
                if isinstance(m.get('outcomePrices'), str):
                    prices = [float(x) for x in json.loads(m['outcomePrices'])]
                elif isinstance(m.get('outcomePrices'), list):
                    prices = [float(x) for x in m['outcomePrices']]
            except Exception:
                pass

            best_ask = float(m.get('bestAsk') or 0)

            # Clean working link for Polymarket event
            if event_slug:
                url = f"https://polymarket.com/event/{event_slug}"
            elif slug:
                url = f"https://polymarket.com/market/{slug}"
            else:
                url = "https://polymarket.com"

            normalized.append({
                'id': f"polymarket-{m_id}",
                'exchange': 'polymarket',
                'condition_id': condition_id,
                'ticker': slug,
                'event_title': event_title,
                'event_slug': event_slug,
                'question': question,
                'title': f"{event_title} — {question}" if event_title else question,
                'outcomes': outcomes,
                'outcome_prices': prices,
                'best_ask': best_ask,
                'url': url
            })

        return {
            'markets': normalized,
            'count': len(normalized),
            'error': error if len(normalized) == 0 else None
        }

def fetch_polymarket_markets(target_rows=None):
    client = PolymarketClient()
    res = client.get_markets(target_rows=target_rows)
    return res['markets']


