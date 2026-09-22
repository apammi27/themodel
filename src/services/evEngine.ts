import type { EightRainRow, ExchangeMarketLine, MatchedEvLine } from '../types';

export function calculateEvForPair(
  modelRow: EightRainRow,
  kalshiLine?: ExchangeMarketLine,
  polyLine?: ExchangeMarketLine
): MatchedEvLine {
  const pModel = modelRow.winPctDecimal;

  // Format Date (20260927 -> Sep 27)
  const dateFormatted = formatDate(modelRow.date);

  // Format Market (h2h -> H2H, spread -> SPREAD (-12), total -> TOTAL (44))
  let marketDisplay = (modelRow.market || 'H2H').toUpperCase();
  if (marketDisplay === 'H2H') marketDisplay = 'H2H';
  else if (marketDisplay === 'SPREAD') marketDisplay = `SPREAD ${modelRow.point ? `(${modelRow.point})` : ''}`;
  else if (marketDisplay === 'TOTAL') marketDisplay = `TOTAL ${modelRow.point ? `(${modelRow.point})` : ''}`;

  // Format Side (home -> homeTeam name, away -> awayTeam name, over -> Over, under -> Under)
  let sideDisplay = modelRow.side;
  const sideLower = (modelRow.side || '').toLowerCase();
  if (sideLower === 'home') sideDisplay = modelRow.home || 'Home';
  else if (sideLower === 'away') sideDisplay = modelRow.away || 'Away';
  else if (sideLower === 'over') sideDisplay = 'Over';
  else if (sideLower === 'under') sideDisplay = 'Under';

  // --- Kalshi Calculations ---
  let kalshiProbPct = '—';
  let kalshiProbDecimal: number | undefined = undefined;
  let kalshiEdgePct = '—';
  let kalshiEdgeVal = -999;
  let kalshiUrl: string | undefined = undefined;

  if (kalshiLine && kalshiLine.price > 0) {
    kalshiProbDecimal = kalshiLine.price;
    kalshiProbPct = `${(kalshiLine.price * 100).toFixed(1)}%`;
    kalshiEdgeVal = parseFloat(((pModel - kalshiLine.price) * 100).toFixed(1));
    kalshiEdgePct = kalshiEdgeVal > 0 ? `+${kalshiEdgeVal.toFixed(1)}%` : `${kalshiEdgeVal.toFixed(1)}%`;
    kalshiUrl = kalshiLine.url || `https://kalshi.com/markets/${kalshiLine.ticker}`;
  }

  // --- Polymarket Calculations ---
  let polyProbPct = '—';
  let polyProbDecimal: number | undefined = undefined;
  let polyEdgePct = '—';
  let polyEdgeVal = -999;
  let polyUrl: string | undefined = undefined;

  if (polyLine && polyLine.price > 0) {
    polyProbDecimal = polyLine.price;
    polyProbPct = `${(polyLine.price * 100).toFixed(1)}%`;
    polyEdgeVal = parseFloat(((pModel - polyLine.price) * 100).toFixed(1));
    polyEdgePct = polyEdgeVal > 0 ? `+${polyEdgeVal.toFixed(1)}%` : `${polyEdgeVal.toFixed(1)}%`;
    polyUrl = polyLine.url || `https://polymarket.com/market/${polyLine.ticker}`;
  }

  // --- ½ Kelly Calculation ---
  // Pick best available edge between Kalshi and Polymarket
  const bestMarketProb = Math.min(
    kalshiProbDecimal !== undefined ? kalshiProbDecimal : 1.0,
    polyProbDecimal !== undefined ? polyProbDecimal : 1.0
  );

  let halfKellyVal = 0;
  let halfKellyPct = '—';

  if (bestMarketProb < 1.0 && pModel > bestMarketProb) {
    // Full Kelly = (pModel - pMarket) / (1 - pMarket)
    const fullKelly = (pModel - bestMarketProb) / (1 - bestMarketProb);
    const halfKelly = fullKelly * 0.5;
    if (halfKelly > 0) {
      halfKellyVal = parseFloat((halfKelly * 100).toFixed(1));
      halfKellyPct = `${halfKellyVal.toFixed(1)}%`;
    }
  }

  const isPosEv = kalshiEdgeVal > 0 || polyEdgeVal > 0;

  return {
    id: `ev-${modelRow.id}`,
    modelRow,
    dateFormatted,
    homeTeam: modelRow.home,
    awayTeam: modelRow.away,
    marketDisplay,
    sideDisplay,
    modelProbPct: `${(pModel * 100).toFixed(1)}%`,
    modelProbDecimal: pModel,

    kalshiProbPct,
    kalshiProbDecimal,
    kalshiEdgePct,
    kalshiEdgeVal,
    kalshiUrl,

    polyProbPct,
    polyProbDecimal,
    polyEdgePct,
    polyEdgeVal,
    polyUrl,

    halfKellyPct,
    halfKellyVal,

    isPosEv,
  };
}

function formatDate(dateStr: string): string {
  if (!dateStr || dateStr.length < 8) return 'Sep 27';
  const monthMap: Record<string, string> = {
    '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr', '05': 'May', '06': 'Jun',
    '07': 'Jul', '08': 'Aug', '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'
  };
  const m = dateStr.substring(4, 6);
  const d = parseInt(dateStr.substring(6, 8), 10);
  return `${monthMap[m] || 'Sep'} ${d || 27}`;
}
