import type { EightRainRow, ExchangeMarketLine, MatchedEvLine } from '../types';
import { calculateEvForPair } from './evEngine';

export function matchModelRowsToLiveMarkets(
  modelRows: EightRainRow[],
  kalshiMarkets: ExchangeMarketLine[],
  polyMarkets: ExchangeMarketLine[]
): MatchedEvLine[] {
  return modelRows.map((row) => {
    const matchedKalshi = findBestExchangeMatch(row, kalshiMarkets);
    const matchedPoly = findBestExchangeMatch(row, polyMarkets);

    return calculateEvForPair(row, matchedKalshi, matchedPoly);
  });
}

function findBestExchangeMatch(
  row: EightRainRow,
  markets: ExchangeMarketLine[]
): ExchangeMarketLine | undefined {
  if (!markets || markets.length === 0) return undefined;

  const home = (row.home || '').toUpperCase();
  const away = (row.away || '').toUpperCase();
  const side = (row.side || '').toUpperCase();
  const selector = (row.selector || '').toUpperCase();
  const section = (row.section || row.market || '').toLowerCase();
  const pointVal = row.point ? parseFloat(row.point) : null;

  // Extract date tokens (e.g. 20260922 -> 2026-09-22 / SEP22)
  const dateStr = row.date || '';
  let dateTokens: string[] = [];
  if (dateStr.length >= 8) {
    const yyyy = dateStr.substring(0, 4);
    const mm = dateStr.substring(4, 6);
    const dd = dateStr.substring(6, 8);
    const months: Record<string, string> = {
      '01': 'JAN', '02': 'FEB', '03': 'MAR', '04': 'APR', '05': 'MAY', '06': 'JUN',
      '07': 'JUL', '08': 'AUG', '09': 'SEP', '10': 'OCT', '11': 'NOV', '12': 'DEC'
    };
    dateTokens = [
      `${yyyy}-${mm}-${dd}`,
      `${months[mm] || 'SEP'}${dd}`,
      `${months[mm] || 'SEP'}-${dd}`,
    ];
  }

  let bestMatch: ExchangeMarketLine | undefined = undefined;
  let highestScore = 0;

  for (const m of markets) {
    let score = 0;
    const titleUpper = (m.title || '').toUpperCase();
    const tickerUpper = (m.ticker || '').toUpperCase();

    // Date Score (+400 or -400)
    if (dateTokens.length > 0) {
      const matchDate = dateTokens.some(
        (t) => titleUpper.includes(t) || tickerUpper.includes(t)
      );
      if (matchDate) score += 400;
      else score -= 400;
    }

    // Team Matching
    let homeMatch = false;
    let awayMatch = false;
    if (home && (titleUpper.includes(home) || tickerUpper.includes(home))) {
      homeMatch = true;
      score += 150;
    }
    if (away && (titleUpper.includes(away) || tickerUpper.includes(away))) {
      awayMatch = true;
      score += 150;
    }

    // Target Team / Side Match
    const targetTeam = selector === 'HOME' ? home : (selector === 'AWAY' ? away : (side.length > 2 ? side : ''));
    if (targetTeam && (titleUpper.includes(targetTeam) || tickerUpper.includes(targetTeam))) {
      score += 200;
    }

    // Market Section Match (Spread vs Total vs H2H)
    if (section.includes('spread')) {
      if (titleUpper.includes('SPREAD') || tickerUpper.includes('SPREAD') || titleUpper.includes('WINS BY')) score += 100;
    } else if (section.includes('total')) {
      if (titleUpper.includes('TOTAL') || tickerUpper.includes('TOTAL') || titleUpper.includes('OVER') || titleUpper.includes('UNDER')) score += 100;
    } else if (section.includes('head') || section.includes('h2h')) {
      if (titleUpper.includes('WINNER') || titleUpper.includes('GAME') || tickerUpper.includes('GAME')) score += 100;
    }

    // Strike Point Tolerance Matching (0.1 tolerance)
    if (pointVal !== null && !isNaN(pointVal)) {
      const ptStr = Math.abs(pointVal).toString();
      if (titleUpper.includes(ptStr) || tickerUpper.includes(ptStr)) {
        score += 150;
      }
    }

    if (score > highestScore && score >= 250) {
      highestScore = score;
      bestMatch = m;
    }
  }

  if (!bestMatch) return undefined;

  // Perform spread/underdog side price inversion if needed
  let effectivePrice = bestMatch.price;
  const isUnderdogSpread = section.includes('spread') && (side.includes('+') || pointVal !== null && pointVal > 0);
  
  if (isUnderdogSpread && bestMatch.price > 0 && bestMatch.price < 1) {
    // Invert favorite price ($1.00 - P_fav = P_underdog)
    effectivePrice = Math.round((1.0 - bestMatch.price) * 1000) / 1000;
  }

  return {
    ...bestMatch,
    price: effectivePrice,
    impliedProb: effectivePrice,
  };
}
