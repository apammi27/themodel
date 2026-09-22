import csv
import io

def parse_win_probability(raw_str):
    if not raw_str:
        return 0.5
    clean = str(raw_str).replace('%', '').strip()
    try:
        val = float(clean)
    except ValueError:
        return 0.5

    # Case 1: Decimal probability 0.0 - 1.0 (e.g. 0.37 or 0.626)
    if 0.0 < val < 1.0:
        return val

    # Case 2: Percentage string (e.g. 62.6% -> 0.626)
    if 1.0 <= val <= 99.9 and not str(raw_str).startswith('+') and not str(raw_str).startswith('-'):
        return val / 100.0

    # Case 3: American Odds (-150, +120, 100)
    if val < 0:
        prob = (-val) / (-val + 100.0)
    elif val > 0:
        prob = 100.0 / (val + 100.0)
    else:
        prob = 0.5

    return max(0.001, min(0.999, prob))

def parse_csv_content(csv_text):
    if not csv_text or not csv_text.strip():
        return []

    stream = io.StringIO(csv_text.strip())
    reader = csv.reader(stream)

    rows = []
    headers = []

    for i, row in enumerate(reader):
        if not row or not any(row):
            continue
        
        row_str = " ".join(row).upper()
        
        # Header detection
        if 'LEAGUE' in row_str or 'MARKET' in row_str or 'WIN %' in row_str or 'MODEL_PROB' in row_str:
            headers = [h.strip().upper() for h in row]
            continue

        if not headers:
            # 11-column default spec header if missing
            headers = ['LEAGUE', 'DATE', 'HOME', 'AWAY', 'DOUBLEHEADER', 'SECTION', 'MARKET', 'SELECTOR', 'POINT', 'SIDE', 'WIN %']

        get_val = lambda keyword: row[headers.index(keyword)].strip() if keyword in headers and headers.index(keyword) < len(row) else ''

        league = get_val('LEAGUE') or 'MLB'
        date = get_val('DATE') or '20250410'
        home = get_val('HOME')
        away = get_val('AWAY')
        doubleheader = get_val('DOUBLEHEADER') or '0'
        section = get_val('SECTION') or 'head_to_head'
        market = get_val('MARKET') or 'h2h'
        selector = get_val('SELECTOR')
        point = get_val('POINT')
        side = get_val('SIDE') or 'home'
        
        win_str = get_val('WIN %') or get_val('MODEL_PROB') or get_val('WIN') or get_val('PROB')
        model_prob = parse_win_probability(win_str)

        # Handle team_prop / player_prop selector fallback if HOME/AWAY are blank
        if section in ['team_prop', 'player_prop'] and selector and not home:
            home = selector

        # Un-slugify selector (e.g. joe-burrow -> Joe Burrow)
        clean_selector = selector.replace('-', ' ').title() if ('-' in selector and not selector.startswith('+') and not selector.startswith('-')) else selector

        # Un-slugify market (e.g. player-passing_yards-ou -> passing_yards)
        clean_market = market.lower().replace('-', '_').replace('player_', '').replace('_ou', '')

        rows.append({
            'id': f"row-{i}-{league}-{date}-{home}-{away}-{clean_market}-{side}-{point}",
            'league': league.upper(),
            'date': date,
            'home': home,
            'away': away,
            'doubleheader': doubleheader,
            'section': section.lower(),
            'market': clean_market,
            'raw_market': market,
            'selector': clean_selector,
            'raw_selector': selector,
            'point': point,
            'side': side.lower(),
            'win_str': win_str,
            'model_prob': model_prob,
        })

    return rows
