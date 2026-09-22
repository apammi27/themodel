import re
from .team_mapper import resolve_team

def format_date(date_str):
    if not date_str or len(str(date_str)) < 8:
        return 'Sep 27'
    s = str(date_str)
    months = {'01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr', '05': 'May', '06': 'Jun',
              '07': 'Jul', '08': 'Aug', '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'}
    m = s[4:6]
    d = int(s[6:8]) if s[6:8].isdigit() else 27
    return f"{months.get(m, 'Sep')} {d}"

def parse_point_val(point_str):
    if not point_str:
        return None
    try:
        clean = str(point_str).replace('+', '').replace('-', '').strip()
        return float(clean)
    except Exception:
        return None

def match_strike_point(mkt, target_point):
    target_val = parse_point_val(target_point)
    if target_val is None:
        return True

    for field in ['floor_strike', 'cap_strike']:
        val = mkt.get(field)
        if val is not None:
            try:
                if abs(float(val) - target_val) <= 0.1:
                    return True
            except Exception:
                pass

    title_q_str = f"{mkt.get('title', '')} {mkt.get('question', '')}"
    nums = re.findall(r'\d+(?:\.\d+)?', title_q_str)
    for num in nums:
        try:
            if abs(float(num) - target_val) <= 0.1:
                return True
        except Exception:
            pass

    return False

def check_alias_match(full_text, ticker, alias_list):
    if not alias_list:
        return False
    for alias in alias_list:
        if not alias: continue
        alias_clean = alias.strip()
        if ticker and len(alias_clean) >= 2 and alias_clean.upper() in ticker.upper():
            return True
        if full_text:
            pattern = r'\b' + re.escape(alias_clean) + r'\b'
            if re.search(pattern, full_text, re.IGNORECASE):
                return True
    return False

def match_model_rows(rows, kalshi_markets, poly_markets):
    matched_lines = []

    for r in rows:
        league = (r.get('league') or 'NFL').upper()
        home_code = r.get('home', '')
        away_code = r.get('away', '')
        date_raw = r.get('date')
        market_raw = (r.get('market') or 'h2h').lower()
        point_raw = r.get('point')
        side_raw = (r.get('side') or 'home').lower()
        
        home_info = resolve_team(home_code)
        away_info = resolve_team(away_code)

        p_model = r.get('model_prob', 0.5)

        # 1. Match Kalshi
        k_matched = find_exchange_match(r, home_info, away_info, kalshi_markets, is_kalshi=True)

        # 2. Match Polymarket
        p_matched = find_exchange_match(r, home_info, away_info, poly_markets, is_kalshi=False)

        # Format display properties
        date_formatted = format_date(date_raw)
        
        if market_raw in ['h2h', 'moneyline']:
            market_display = 'H2H'
        elif market_raw in ['spread', 'run_line', 'puck_line', 'handicap']:
            market_display = f"SPREAD ({point_raw})" if point_raw else "SPREAD"
        elif market_raw in ['total', 'runs', 'score', 'points', 'goals', 'rounds']:
            market_display = f"TOTAL ({point_raw})" if point_raw else "TOTAL"
        else:
            market_display = market_raw.upper()

        if side_raw == 'home':
            side_display = home_code or 'Home'
        elif side_raw == 'away':
            side_display = away_code or 'Away'
        elif side_raw == 'over':
            side_display = 'Over'
        elif side_raw == 'under':
            side_display = 'Under'
        else:
            side_display = side_raw.capitalize()

        # Kalshi Edge Calculation
        kalshi_prob_pct = '—'
        kalshi_prob = None
        kalshi_edge_pct = '—'
        kalshi_edge_val = -999.0
        kalshi_url = None

        if k_matched:
            k_p = extract_side_price(k_matched, side_raw, home_info, away_info, is_kalshi=True, point_raw=point_raw, selector_raw=r.get('selector'))
            if k_p is not None and 0 < k_p < 1:
                kalshi_prob = k_p
                kalshi_prob_pct = f"{k_p * 100:.1f}%"
                kalshi_edge_val = round((p_model - k_p) * 100.0, 1)
                kalshi_edge_pct = f"+{kalshi_edge_val:.1f}%" if kalshi_edge_val > 0 else f"{kalshi_edge_val:.1f}%"
                kalshi_url = k_matched.get('url')

        # Polymarket Edge Calculation
        poly_prob_pct = '—'
        poly_prob = None
        poly_edge_pct = '—'
        poly_edge_val = -999.0
        poly_url = None

        if p_matched:
            p_p = extract_side_price(p_matched, side_raw, home_info, away_info, is_kalshi=False, point_raw=point_raw, selector_raw=r.get('selector'))
            if p_p is not None and 0 < p_p < 1:
                poly_prob = p_p
                poly_prob_pct = f"{p_p * 100:.1f}%"
                poly_edge_val = round((p_model - p_p) * 100.0, 1)
                poly_edge_pct = f"+{poly_edge_val:.1f}%" if poly_edge_val > 0 else f"{poly_edge_val:.1f}%"
                poly_url = p_matched.get('url')

        # ½ Kelly Calculation
        valid_probs = [p for p in [kalshi_prob, poly_prob] if p is not None]
        best_market_prob = min(valid_probs) if valid_probs else 1.0

        half_kelly_pct = '—'
        half_kelly_val = 0.0

        if best_market_prob < 1.0 and p_model > best_market_prob:
            full_kelly = (p_model - best_market_prob) / (1.0 - best_market_prob)
            half_kelly = full_kelly * 0.5
            if half_kelly > 0:
                half_kelly_val = round(half_kelly * 100.0, 1)
                half_kelly_pct = f"{half_kelly_val:.1f}%"

        is_pos_ev = kalshi_edge_val > 0 or poly_edge_val > 0

        matched_lines.append({
            'id': r['id'],
            'model_row': r,
            'date_formatted': date_formatted,
            'home_team': home_code,
            'away_team': away_code,
            'market_display': market_display,
            'side_display': side_display,
            'model_prob_pct': f"{p_model * 100:.1f}%",
            'model_prob': p_model,

            'kalshi_prob_pct': kalshi_prob_pct,
            'kalshi_prob': kalshi_prob,
            'kalshi_edge_pct': kalshi_edge_pct,
            'kalshi_edge_val': kalshi_edge_val,
            'kalshi_url': kalshi_url,

            'poly_prob_pct': poly_prob_pct,
            'poly_prob': poly_prob,
            'poly_edge_pct': poly_edge_pct,
            'poly_edge_val': poly_edge_val,
            'poly_url': poly_url,

            'half_kelly_pct': half_kelly_pct,
            'half_kelly_val': half_kelly_val,

            'is_pos_ev': is_pos_ev,
        })

    return matched_lines

def check_player_match(full_text, selector):
    if not selector:
        return False
    sel_clean = selector.strip()
    if sel_clean.lower() in full_text.lower():
        return True
    parts = sel_clean.split()
    if len(parts) >= 2:
        last_name = parts[-1]
        if len(last_name) >= 3 and re.search(r'\b' + re.escape(last_name) + r'\b', full_text, re.IGNORECASE):
            return True
    return False

def extract_date_key(date_str):
    if not date_str:
        return None, None
    s = str(date_str).strip()
    months = {'01':'JAN', '02':'FEB', '03':'MAR', '04':'APR', '05':'MAY', '06':'JUN',
              '07':'JUL', '08':'AUG', '09':'SEP', '10':'OCT', '11':'NOV', '12':'DEC'}
    if len(s) == 8 and s.isdigit():
        m_code = months.get(s[4:6], 'SEP')
        day_code = s[6:8]
        return f"{m_code}{day_code}", f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    if '-' in s:
        parts = s.split('-')
        if len(parts) >= 3:
            y, m, d = parts[0], parts[1].zfill(2), parts[2].zfill(2)
            return f"{months.get(m, 'SEP')}{d}", f"{y}-{m}-{d}"
    return None, None

def find_exchange_match(row, home_info, away_info, markets, is_kalshi=True):
    if not markets:
        return None

    section = (row.get('section') or '').lower()
    market_type = (row.get('market') or 'h2h').lower()
    point = row.get('point')
    selector = (row.get('selector') or '').strip()
    date_raw = row.get('date')

    kalshi_date_key, poly_date_key = extract_date_key(date_raw)

    home_aliases = home_info['aliases'] if home_info else []
    away_aliases = away_info['aliases'] if away_info else []

    target_team_aliases = []
    if selector:
        if home_info and any(a.upper() == selector.upper() for a in home_aliases if a):
            target_team_aliases = home_aliases
        elif away_info and any(a.upper() == selector.upper() for a in away_aliases if a):
            target_team_aliases = away_aliases
        else:
            target_team_aliases = [selector]
    elif row.get('side', '').lower() == 'home' and home_info:
        target_team_aliases = home_aliases
    elif row.get('side', '').lower() == 'away' and away_info:
        target_team_aliases = away_aliases

    is_player_prop = (section in ['player_prop', 'props', 'player_props']) or (market_type in [
        'passing_yards', 'rushing_yards', 'receiving_yards', 'touchdowns', 'receptions',
        'strikeouts', 'hits', 'home_runs', 'rbis', 'points', 'rebounds', 'assists',
        'three_pointers', 'fantasy_points', 'goals', 'saves', 'player_prop'
    ])

    best_match = None
    highest_score = -999

    for m in markets:
        ticker = m.get('ticker', '')
        if is_kalshi:
            full_text = f"{m.get('series_ticker', '')} {ticker} {m.get('title', '')} {m.get('subtitle', '')}"
            title_text = f"{m.get('title', '')} {ticker}"
        else:
            full_text = f"{m.get('event_slug', '')} {ticker} {m.get('event_title', '')} {m.get('question', '')} {m.get('title', '')}"
            title_text = f"{m.get('question', '')} {m.get('title', '')} {ticker}"

        has_home = check_alias_match(full_text, ticker, home_aliases) if home_aliases else False
        has_away = check_alias_match(full_text, ticker, away_aliases) if away_aliases else False

        if is_player_prop:
            has_player = check_player_match(full_text, selector)
            if not (has_player or has_home or has_away):
                continue
            score = 150 if has_player else 80
        elif section in ['head_to_head', 'spread', 'total', 'game_prop'] or market_type in ['h2h', 'spread', 'total']:
            if not (has_home and has_away):
                continue
            score = 100
        else:
            if has_home and has_away: score = 100
            elif has_home or has_away: score = 50
            else: continue

        # Date matching check
        if is_kalshi and kalshi_date_key:
            if kalshi_date_key in ticker.upper():
                score += 400
            else:
                score -= 400
        elif not is_kalshi and poly_date_key:
            if poly_date_key in full_text:
                score += 400
            else:
                score -= 400

        # Market category check
        full_text_lower = full_text.lower()
        if market_type in ['total', 'runs', 'score', 'points', 'goals', 'rounds']:
            if 'total' in full_text_lower or 'over' in full_text_lower or 'under' in full_text_lower or 'points' in full_text_lower:
                score += 30
            else:
                continue
        elif market_type in ['spread', 'run_line', 'puck_line', 'handicap']:
            if 'spread' in full_text_lower or 'by over' in full_text_lower or 'run line' in full_text_lower or 'handicap' in full_text_lower:
                score += 30
            else:
                continue
        elif market_type in ['h2h', 'moneyline']:
            if 'game' in full_text_lower or 'winner' in full_text_lower or 'beat' in full_text_lower or 'vs' in full_text_lower:
                score += 20

        # Strike point line check
        if point:
            if not match_strike_point(m, point):
                continue
            score += 40

        # Team targeting bonus for spread & H2H markets
        if target_team_aliases and market_type in ['spread', 'run_line', 'puck_line', 'handicap', 'h2h', 'moneyline']:
            m_title = m.get('title', '') or m.get('question', '')
            matches_title = check_alias_match(m_title, '', target_team_aliases)
            ticker_parts = ticker.split('-')
            ticker_suffix = ticker_parts[-1] if len(ticker_parts) > 1 else ''
            matches_suffix = any(a.upper() in ticker_suffix.upper() for a in target_team_aliases if a)

            if matches_title or matches_suffix:
                score += 200
            else:
                score -= 100

        if score > highest_score:
            highest_score = score
            best_match = m

    return best_match

def extract_side_price(matched, side_raw, home_info, away_info, is_kalshi=True, point_raw=None, selector_raw=None):
    if not matched:
        return None

    ticker = matched.get('ticker', '')
    title_upper = matched.get('title', '').upper()
    question_upper = matched.get('question', '').upper()

    point_val = 0.0
    if point_raw:
        try:
            point_val = float(str(point_raw).strip())
        except Exception:
            point_val = 0.0

    if is_kalshi:
        price = matched.get('price')
        if price is None or price <= 0:
            return None
        
        if side_raw in ['under', 'lower'] or 'UNDER' in str(side_raw).upper():
            return round(1.0 - price, 4)
        elif side_raw in ['over', 'higher'] or 'OVER' in str(side_raw).upper():
            return round(price, 4)

        contract_is_home = False
        contract_is_away = False

        if home_info and home_info.get('aliases'):
            for a in home_info['aliases']:
                if a and (a.upper() in title_upper or ticker.endswith(f"-{a.upper()}") or f"-{a.upper()}" in ticker):
                    contract_is_home = True
                    break
        if away_info and away_info.get('aliases'):
            for a in away_info['aliases']:
                if a and (a.upper() in title_upper or ticker.endswith(f"-{a.upper()}") or f"-{a.upper()}" in ticker):
                    contract_is_away = True
                    break

        row_is_home = (side_raw == 'home')
        if selector_raw and home_info and any(a.upper() == selector_raw.upper() for a in home_info.get('aliases', [])):
            row_is_home = True
        elif selector_raw and away_info and any(a.upper() == selector_raw.upper() for a in away_info.get('aliases', [])):
            row_is_home = False

        if point_val != 0.0:
            same_team = (row_is_home == contract_is_home) or (not row_is_home and contract_is_away)
            if same_team:
                return round(price, 4) if point_val < 0 else round(1.0 - price, 4)
            else:
                return round(1.0 - price, 4) if point_val > 0 else None

        if row_is_home:
            return round(price, 4) if contract_is_home else round(1.0 - price, 4)
        else:
            return round(price, 4) if contract_is_away else round(1.0 - price, 4)

    else:
        outcomes = matched.get('outcomes', [])
        prices = matched.get('outcome_prices', [])
        if not prices:
            return None

        if side_raw in ['over', 'under'] and outcomes and len(outcomes) >= 2:
            for idx, out in enumerate(outcomes):
                if str(out).lower() == side_raw:
                    if idx < len(prices) and prices[idx] > 0:
                        return float(prices[idx])

        row_team_aliases = []
        if selector_raw:
            if home_info and any(a.upper() == selector_raw.upper() for a in home_info.get('aliases', [])):
                row_team_aliases = home_info['aliases']
            elif away_info and any(a.upper() == selector_raw.upper() for a in away_info.get('aliases', [])):
                row_team_aliases = away_info['aliases']
            else:
                row_team_aliases = [selector_raw]
        elif side_raw == 'home' and home_info:
            row_team_aliases = home_info['aliases']
        elif side_raw == 'away' and away_info:
            row_team_aliases = away_info['aliases']
        
        if outcomes and len(outcomes) >= 2:
            for idx, out in enumerate(outcomes):
                out_str = str(out).upper()
                has_team = any(a.upper() in out_str for a in row_team_aliases if a)
                if has_team:
                    if idx < len(prices) and prices[idx] > 0:
                        return float(prices[idx])

        if outcomes in [['Yes', 'No'], ['YES', 'NO']] and len(prices) >= 2:
            q_is_home = False
            q_is_away = False
            full_q = f"{question_upper} {title_upper}"
            if home_info and any(a.upper() in full_q for a in home_info.get('aliases', [])):
                q_is_home = True
            if away_info and any(a.upper() in full_q for a in away_info.get('aliases', [])):
                q_is_away = True

            row_is_home = (side_raw == 'home')
            if selector_raw and home_info and any(a.upper() == selector_raw.upper() for a in home_info.get('aliases', [])):
                row_is_home = True
            elif selector_raw and away_info and any(a.upper() == selector_raw.upper() for a in away_info.get('aliases', [])):
                row_is_home = False
            
            if point_val != 0.0:
                same_team = (row_is_home and q_is_home) or (not row_is_home and q_is_away)
                if same_team:
                    return float(prices[0]) if point_val < 0 else float(prices[1])
                else:
                    return float(prices[1]) if point_val > 0 else None

            if row_is_home:
                return float(prices[0]) if q_is_home else float(prices[1])
            else:
                return float(prices[0]) if q_is_away else float(prices[1])

        return float(prices[0]) if prices and prices[0] > 0 else None
