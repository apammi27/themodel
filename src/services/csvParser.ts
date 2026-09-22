import type { EightRainRow } from '../types';

export function parseWinProbability(winPctStr: string): { decimalProb: number; americanOdds: number } {
  if (!winPctStr) return { decimalProb: 0.5, americanOdds: -110 };
  
  const clean = winPctStr.trim().replace('%', '');
  const num = parseFloat(clean);
  
  if (isNaN(num)) return { decimalProb: 0.5, americanOdds: -110 };

  // Case 1: Decimal probability between 0 and 1 (e.g. 0.626)
  if (num > 0 && num < 1) {
    const dec = num;
    const american = decToAmericanOdds(dec);
    return { decimalProb: dec, americanOdds: american };
  }

  // Case 2: Percentage (e.g. 62.6 -> 0.626)
  if (num >= 1 && num <= 99.9 && !winPctStr.startsWith('+') && !winPctStr.startsWith('-') && !Number.isInteger(num)) {
    const dec = num / 100;
    const american = decToAmericanOdds(dec);
    return { decimalProb: dec, americanOdds: american };
  }

  // Case 3: American Odds (-150, +120)
  let decProb = 0.5;
  let american = num;
  if (num < 0) {
    decProb = (-num) / (-num + 100);
  } else if (num > 0) {
    decProb = 100 / (num + 100);
  }

  decProb = Math.max(0.001, Math.min(0.999, decProb));
  return { decimalProb: decProb, americanOdds: Math.round(american) };
}

export function decToAmericanOdds(p: number): number {
  if (p <= 0.001) return 10000;
  if (p >= 0.999) return -10000;
  if (p >= 0.5) {
    return Math.round(-100 * (p / (1 - p)));
  } else {
    return Math.round(100 * ((1 - p) / p));
  }
}

export function parse8rainCsv(csvText: string): EightRainRow[] {
  const lines = csvText.split(/\r?\n/).filter(line => line.trim().length > 0);
  if (lines.length === 0) return [];

  const rows: EightRainRow[] = [];

  // Find header row
  const headerIdx = lines.findIndex(l => {
    const u = l.toUpperCase();
    return u.includes('LEAGUE') && (u.includes('MARKET') || u.includes('HOME'));
  });

  if (headerIdx < 0) return [];

  const headers = parseCsvRow(lines[headerIdx]).map(h => h.toUpperCase().trim());

  // Find column mapping dynamically
  const colMap = {
    league: headers.findIndex(h => h.includes('LEAGUE')),
    date: headers.findIndex(h => h.includes('DATE')),
    home: headers.findIndex(h => h.includes('HOME')),
    away: headers.findIndex(h => h.includes('AWAY')),
    doubleheader: headers.findIndex(h => h.includes('DOUBLEHEADER')),
    section: headers.findIndex(h => h.includes('SECTION')),
    market: headers.findIndex(h => h.includes('MARKET')),
    selector: headers.findIndex(h => h.includes('SELECTOR')),
    point: headers.findIndex(h => h.includes('POINT')),
    side: headers.findIndex(h => h.includes('SIDE')),
    winPct: headers.findIndex(h => h.includes('MODEL_PROB') || h.includes('WIN') || h.includes('PROB')),
  };

  for (let i = headerIdx + 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line || line.startsWith('#') || line.startsWith('//')) continue;

    const cols = parseCsvRow(line);
    if (cols.length < 4) continue;

    const getCol = (idx: number) => (idx >= 0 && cols[idx] !== undefined) ? cols[idx].trim() : '';

    const league = getCol(colMap.league) || 'nfl';
    const date = getCol(colMap.date) || '20260927';
    const home = getCol(colMap.home);
    const away = getCol(colMap.away);
    const doubleheader = parseInt(getCol(colMap.doubleheader) || '0', 10) || 0;
    const section = getCol(colMap.section) || 'head_to_head';
    const market = getCol(colMap.market) || 'h2h';
    const selector = getCol(colMap.selector);
    const point = getCol(colMap.point);
    const side = getCol(colMap.side) || 'home';
    const winPctRaw = getCol(colMap.winPct);

    const { decimalProb, americanOdds } = parseWinProbability(winPctRaw);

    rows.push({
      id: `row-${i}-${league}-${home}-${away}-${market}-${side}`,
      league,
      date,
      home,
      away,
      doubleheader,
      section,
      market,
      selector,
      point,
      side,
      winPctRaw,
      winPctDecimal: decimalProb,
      americanOdds,
    });
  }

  return rows;
}

function parseCsvRow(row: string): string[] {
  const result: string[] = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < row.length; i++) {
    const char = row[i];
    if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      result.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  result.push(current.trim());
  return result;
}
