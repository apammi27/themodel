export interface EightRainRow {
  id: string;
  league: string;
  date: string; // YYYYMMDD e.g. 20260927
  home: string;
  away: string;
  doubleheader?: number;
  section?: string;
  market: string; // h2h, spread, total, etc.
  selector?: string;
  point?: string;
  side: string; // home, away, over, under, yes, no
  winPctRaw: string;
  winPctDecimal: number; // 0.0 - 1.0 (e.g. 0.626)
  americanOdds: number;
}

export interface ExchangeMarketLine {
  id: string;
  exchange: 'kalshi' | 'polymarket';
  ticker: string;
  title: string;
  homeTeam?: string;
  awayTeam?: string;
  marketType?: string;
  side?: string;
  point?: string;
  price: number; // 0.0 - 1.0
  impliedProb: number; // 0.0 - 1.0
  url?: string;
}

export interface MatchedEvLine {
  id: string;
  modelRow: EightRainRow;

  dateFormatted: string; // e.g. "Sep 27"
  homeTeam: string;
  awayTeam: string;
  marketDisplay: string; // e.g. "H2H", "SPREAD (-3.5)", "TOTAL (47.5)"
  sideDisplay: string; // e.g. "Steelers", "Bengals", "Over", "Under"

  modelProbPct: string; // e.g. "62.6%"
  modelProbDecimal: number;

  kalshiProbPct: string; // e.g. "55.0%" or "—"
  kalshiProbDecimal?: number;
  kalshiEdgePct: string; // e.g. "+7.6%" or "—"
  kalshiEdgeVal: number;
  kalshiUrl?: string;

  polyProbPct: string; // e.g. "49.0%" or "—"
  polyProbDecimal?: number;
  polyEdgePct: string; // e.g. "+13.6%" or "-1.4%"
  polyEdgeVal: number;
  polyUrl?: string;

  halfKellyPct: string; // e.g. "13.3%" or "—"
  halfKellyVal: number;

  isPosEv: boolean; // true if kalshiEdgeVal > 0 or polyEdgeVal > 0
}

export interface FilterState {
  posEvOnly: boolean;
  minEdge: number;
  sortBy: 'k_edge' | 'p_edge' | 'model_prob' | 'date';
}
