import type { ExchangeMarketLine } from '../types';

export async function fetchKalshiMarkets(apiKey?: string, limit = 250): Promise<{ markets: ExchangeMarketLine[]; error: string | null; count: number }> {
  try {
    const seriesList = [
      'KXNFLGAME', 'KXMLBGAME', 'KXNBAGAME', 'KXNHLGAME', 'KXEPLGAME',
      'KXNFLTOTAL', 'KXMLBTOTAL', 'KXNBATOTAL', 'KXNHLTOTAL',
      'KXNFLSPREAD', 'KXMLBSPREAD', 'KXNBASPREAD', 'KXNHLSPREAD'
    ];

    let allRawMarkets: any[] = [];
    let fetchError: string | null = null;

    for (const s of seriesList) {
      const targetUrl = `https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=${s}&status=open&limit=200`;
      try {
        const headers: Record<string, string> = { Accept: 'application/json' };
        if (apiKey && apiKey.trim().length > 0) {
          headers['Authorization'] = `Bearer ${apiKey.trim()}`;
          headers['Authorization-Key'] = apiKey.trim();
        }

        let res = await fetch(targetUrl, { headers }).catch(() => null);

        // Fallback to CORS proxy if direct browser fetch hits CORS error
        if (!res || !res.ok) {
          const proxyUrl = `https://corsproxy.io/?${encodeURIComponent(targetUrl)}`;
          res = await fetch(proxyUrl, { headers }).catch(() => null);
        }

        if (res && res.ok) {
          const data = await res.json();
          if (data && data.markets) {
            allRawMarkets.push(...data.markets);
          }
        }
      } catch (err) {
        // Individual series fetch error ignored
      }
    }

    // Deduplicate by ticker
    const uniqueMarkets = new Map<string, any>();
    allRawMarkets.forEach((m) => {
      if (m && m.ticker) uniqueMarkets.set(m.ticker, m);
    });

    const marketsList = Array.from(uniqueMarkets.values());

    if (marketsList.length === 0) {
      // General open markets endpoint fallback
      const fallbackUrl = `https://api.elections.kalshi.com/trade-api/v2/markets?status=open&limit=${limit}`;
      try {
        let res = await fetch(fallbackUrl).catch(() => null);
        if (!res || !res.ok) {
          res = await fetch(`https://corsproxy.io/?${encodeURIComponent(fallbackUrl)}`).catch(() => null);
        }
        if (res && res.ok) {
          const data = await res.json();
          (data.markets || []).forEach((m: any) => {
            if (m && m.ticker) uniqueMarkets.set(m.ticker, m);
          });
        }
      } catch (e) {
        fetchError = 'Unable to reach Kalshi REST API';
      }
    }

    const parsed: ExchangeMarketLine[] = Array.from(uniqueMarkets.values()).map((m: any) => {
      let price = 0;
      if (m.yes_ask_dollars !== undefined && parseFloat(m.yes_ask_dollars) > 0) {
        price = parseFloat(m.yes_ask_dollars);
      } else if (m.last_price_dollars !== undefined && parseFloat(m.last_price_dollars) > 0) {
        price = parseFloat(m.last_price_dollars);
      } else if (m.yes_bid_dollars !== undefined && parseFloat(m.yes_bid_dollars) > 0) {
        price = parseFloat(m.yes_bid_dollars);
      } else if (m.yes_ask !== undefined && m.yes_ask > 0) {
        price = m.yes_ask > 1 ? m.yes_ask / 100 : m.yes_ask;
      } else if (m.last_price !== undefined && m.last_price > 0) {
        price = m.last_price > 1 ? m.last_price / 100 : m.last_price;
      }

      return {
        id: `kalshi-${m.ticker}`,
        exchange: 'kalshi',
        ticker: m.ticker,
        title: m.title || m.ticker,
        price,
        impliedProb: price,
        url: `https://kalshi.com/markets/${m.ticker}`,
      };
    });

    return { markets: parsed, error: fetchError, count: parsed.length };
  } catch (err: any) {
    return { markets: getMockKalshiMarkets(), error: 'fetch error — Failed to fetch', count: 0 };
  }
}

export function getMockKalshiMarkets(): ExchangeMarketLine[] {
  return [
    {
      id: 'kalshi-steelers-bengals',
      exchange: 'kalshi',
      ticker: 'KXNFL-STEELERS-BENGALS',
      title: 'Pittsburgh Steelers vs Cincinnati Bengals',
      price: 0.55,
      impliedProb: 0.55,
      url: 'https://kalshi.com/markets/KXNFL',
    }
  ];
}
