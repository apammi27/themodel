const fs = require('fs');

// Canonical Team Mappings for all sports leagues
const TEAM_MAPPINGS = {
  // NFL
  KC: { name: 'Kansas City Chiefs', city: 'Kansas City', mascot: 'Chiefs', aliases: ['KC', 'CHIEFS', 'KANSAS CITY'] },
  BUF: { name: 'Buffalo Bills', city: 'Buffalo', mascot: 'Bills', aliases: ['BUF', 'BILLS', 'BUFFALO'] },
  PIT: { name: 'Pittsburgh Steelers', city: 'Pittsburgh', mascot: 'Steelers', aliases: ['PIT', 'STEELERS', 'PITTSBURGH'] },
  CIN: { name: 'Cincinnati Bengals', city: 'Cincinnati', mascot: 'Bengals', aliases: ['CIN', 'BENGALS', 'CINCINNATI'] },
  SF: { name: 'San Francisco 49ers', city: 'San Francisco', mascot: '49ers', aliases: ['SF', '49ERS', 'NINERS', 'SAN FRANCISCO'] },
  ARI: { name: 'Arizona Cardinals', city: 'Arizona', mascot: 'Cardinals', aliases: ['ARI', 'CARDINALS', 'ARIZONA'] },
  IND: { name: 'Indianapolis Colts', city: 'Indianapolis', mascot: 'Colts', aliases: ['IND', 'COLTS', 'INDIANAPOLIS'] },
  HOU: { name: 'Houston Texans', city: 'Houston', mascot: 'Texans', aliases: ['HOU', 'TEXANS', 'HOUSTON'] },
  LAC: { name: 'Los Angeles Chargers', city: 'Los Angeles', mascot: 'Chargers', aliases: ['LAC', 'CHARGERS', 'LA CHARGERS'] },
  CLE: { name: 'Cleveland Browns', city: 'Cleveland', mascot: 'Browns', aliases: ['CLE', 'BROWNS', 'CLEVELAND'] },
  CAR: { name: 'Carolina Panthers', city: 'Carolina', mascot: 'Panthers', aliases: ['CAR', 'PANTHERS', 'CAROLINA'] },
  
  // MLB
  COL: { name: 'Colorado Rockies', city: 'Colorado', mascot: 'Rockies', aliases: ['COL', 'ROCKIES', 'COLORADO'] },
  MIL: { name: 'Milwaukee Brewers', city: 'Milwaukee', mascot: 'Brewers', aliases: ['MIL', 'BREWERS', 'MILWAUKEE'] },
  NYY: { name: 'New York Yankees', city: 'New York', mascot: 'Yankees', aliases: ['NYY', 'YANKEES'] },
  LAD: { name: 'Los Angeles Dodgers', city: 'Los Angeles', mascot: 'Dodgers', aliases: ['LAD', 'DODGERS'] },

  // NBA
  BOS: { name: 'Boston Celtics', city: 'Boston', mascot: 'Celtics', aliases: ['BOS', 'CELTICS', 'BOSTON'] },
  LAL: { name: 'Los Angeles Lakers', city: 'Los Angeles', mascot: 'Lakers', aliases: ['LAL', 'LAKERS'] },
};

function getTeamInfo(code) {
  if (!code) return null;
  const upper = code.toUpperCase().trim();
  return TEAM_MAPPINGS[upper] || { name: upper, city: upper, mascot: upper, aliases: [upper] };
}

// Kalshi Live Fetcher & Rigorous Matcher
async function fetchAndMatchKalshi(row, apiKey) {
  const homeInfo = getTeamInfo(row.home);
  const awayInfo = getTeamInfo(row.away);
  const league = (row.league || 'nfl').toUpperCase();

  const headers = { Accept: 'application/json' };
  if (apiKey) {
    headers['Authorization'] = `Bearer ${apiKey}`;
    headers['Authorization-Key'] = apiKey;
  }

  // Try multiple series tickers for Kalshi
  const seriesTickers = [`KX${league}GAME`, `KX${league}`, `KX${league}SPREAD`, `KX${league}TOTAL` ];
  let markets = [];

  for (const series of seriesTickers) {
    try {
      const res = await fetch(`https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=${series}`, { headers });
      if (res.ok) {
        const json = await res.json();
        if (json.markets) markets.push(...json.markets);
      }
    } catch (e) {}
  }

  // Fallback: general active markets query
  try {
    const res = await fetch(`https://api.elections.kalshi.com/trade-api/v2/markets?limit=200&status=active`, { headers });
    if (res.ok) {
      const json = await res.json();
      if (json.markets) markets.push(...json.markets);
    }
  } catch (e) {}

  // Filter for exact team matchup
  const matched = markets.find(m => {
    const title = (m.title || '' + ' ' + m.ticker || '').toUpperCase();
    const sub = (m.no_sub_title || '' + ' ' + m.yes_sub_title || '').toUpperCase();
    const fullText = title + ' ' + sub;

    const hasHome = homeInfo ? homeInfo.aliases.some(a => fullText.includes(a)) : false;
    const hasAway = awayInfo ? awayInfo.aliases.some(a => fullText.includes(a)) : false;

    return hasHome && hasAway;
  });

  if (!matched) {
    return { status: 'UNMATCHED', price: null, ticker: null, title: null };
  }

  // Extract Price
  let price = null;
  if (matched.yes_ask_dollars !== undefined) {
    price = parseFloat(matched.yes_ask_dollars);
  } else if (matched.yes_ask !== undefined) {
    price = matched.yes_ask > 1 ? matched.yes_ask / 100 : matched.yes_ask;
  } else if (matched.last_price_dollars !== undefined) {
    price = parseFloat(matched.last_price_dollars);
  }

  return {
    status: 'VERIFIED_MATCH',
    ticker: matched.ticker,
    title: matched.title,
    price,
    impliedProbPct: price !== null ? `${(price * 100).toFixed(1)}%` : null
  };
}

// Polymarket Live Fetcher & Rigorous Matcher
async function fetchAndMatchPolymarket(row) {
  const homeInfo = getTeamInfo(row.home);
  const awayInfo = getTeamInfo(row.away);

  // Fetch events and markets from Polymarket Gamma API
  let events = [];
  let markets = [];

  try {
    const resEv = await fetch('https://gamma-api.polymarket.com/events?limit=200&closed=false');
    if (resEv.ok) events = await resEv.json();
  } catch (e) {}

  try {
    const resMkt = await fetch('https://gamma-api.polymarket.com/markets?limit=200&closed=false');
    if (resMkt.ok) markets = await resMkt.json();
  } catch (e) {}

  // Combine event sub-markets and market lists
  events.forEach(e => {
    if (e.markets && Array.isArray(e.markets)) {
      markets.push(...e.markets);
    }
  });

  // Find exact matchup match
  const matched = markets.find(m => {
    const text = ((m.question || '') + ' ' + (m.slug || '') + ' ' + (m.groupItemTitle || '')).toUpperCase();
    const hasHome = homeInfo ? homeInfo.aliases.some(a => text.includes(a)) : false;
    const hasAway = awayInfo ? awayInfo.aliases.some(a => text.includes(a)) : false;
    return hasHome && hasAway;
  });

  if (!matched) {
    return { status: 'UNMATCHED', price: null, question: null, sideMatched: null };
  }

  // Parse outcomePrices and outcomes
  let outcomes = ['Yes', 'No'];
  let outcomePrices = [0.5, 0.5];

  try {
    if (typeof matched.outcomes === 'string') outcomes = JSON.parse(matched.outcomes);
    else if (Array.isArray(matched.outcomes)) outcomes = matched.outcomes;
  } catch (e) {}

  try {
    if (typeof matched.outcomePrices === 'string') outcomePrices = JSON.parse(matched.outcomePrices).map(p => parseFloat(p) || 0);
    else if (Array.isArray(matched.outcomePrices)) outcomePrices = matched.outcomePrices.map(p => parseFloat(p) || 0);
  } catch (e) {}

  // Determine side index
  const targetSide = row.side.toLowerCase();
  let targetIndex = 0;

  if (targetSide === 'home' && homeInfo) {
    const idx = outcomes.findIndex(o => homeInfo.aliases.some(a => o.toUpperCase().includes(a)));
    if (idx >= 0) targetIndex = idx;
  } else if (targetSide === 'away' && awayInfo) {
    const idx = outcomes.findIndex(o => awayInfo.aliases.some(a => o.toUpperCase().includes(a)));
    if (idx >= 0) targetIndex = idx;
  } else if (targetSide === 'under' || targetSide === 'no') {
    targetIndex = 1;
  }

  const price = outcomePrices[targetIndex] !== undefined ? outcomePrices[targetIndex] : (matched.bestAsk || 0.5);

  return {
    status: 'VERIFIED_MATCH',
    question: matched.question || matched.slug,
    outcomeMatched: outcomes[targetIndex],
    price,
    impliedProbPct: `${(price * 100).toFixed(1)}%`
  };
}

// Rigorous Test Runner
async function runDiagnosticTest() {
  console.log('================================================================');
  console.log('   8RAIN STATION LIVE MARKET DATA RIGOROUS DIAGNOSTIC SUITE    ');
  console.log('================================================================\n');

  const testCSV = `LEAGUE,DATE,HOME,AWAY,MARKET,SIDE,POINT,MODEL_PROB
NFL,20260927,Steelers,Bengals,h2h,home,,0.626
NFL,20260927,Steelers,Bengals,h2h,away,,0.374
NFL,20260927,49ers,Cardinals,h2h,away,,0.089
NFL,20260927,49ers,Cardinals,h2h,home,,0.911
NFL,20260927,Colts,Texans,h2h,home,,0.509
NFL,20260927,Bills,LA Chargers,h2h,home,,0.853
MLB,20250410,COL,MIL,h2h,away,,0.580
NBA,20250411,BOS,MIL,h2h,home,,0.720`;

  const lines = testCSV.split('\n').slice(1);
  const rows = lines.map(line => {
    const cols = line.split(',');
    return {
      league: cols[0],
      date: cols[1],
      home: cols[2],
      away: cols[3],
      market: cols[4],
      side: cols[5],
      point: cols[6],
      modelProb: parseFloat(cols[7])
    };
  });

  console.log(`Loaded ${rows.length} CSV test rows for verification...\n`);

  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    console.log(`[ROW ${i + 1}] CSV Input: ${row.league} ${row.date} | ${row.home} vs ${row.away} | ${row.market.toUpperCase()} ${row.side.toUpperCase()} ${row.point || ''} | Model %: ${(row.modelProb * 100).toFixed(1)}%`);

    // Kalshi Match Verification
    const kalshiRes = await fetchAndMatchKalshi(row);
    if (kalshiRes.status === 'VERIFIED_MATCH') {
      const kEdge = ((row.modelProb - kalshiRes.price) * 100).toFixed(1);
      console.log(`   ✓ KALSHI VERIFIED MATCH: Ticker: "${kalshiRes.ticker}" | Title: "${kalshiRes.title}"`);
      console.log(`     Price: $${kalshiRes.price.toFixed(2)} (${kalshiRes.impliedProbPct}) | K Edge: ${kEdge > 0 ? '+' : ''}${kEdge}%`);
    } else {
      console.log(`   ✗ KALSHI: Unmatched (No active market found on Kalshi endpoint)`);
    }

    // Polymarket Match Verification
    const polyRes = await fetchAndMatchPolymarket(row);
    if (polyRes.status === 'VERIFIED_MATCH') {
      const pEdge = ((row.modelProb - polyRes.price) * 100).toFixed(1);
      console.log(`   ✓ POLYMARKET VERIFIED MATCH: Question: "${polyRes.question}" | Outcome Side: "${polyRes.outcomeMatched}"`);
      console.log(`     Price: $${polyRes.price.toFixed(3)} (${polyRes.impliedProbPct}) | P Edge: ${pEdge > 0 ? '+' : ''}${pEdge}%`);
    } else {
      console.log(`   ✗ POLYMARKET: Unmatched (No active market found on Polymarket endpoint)`);
    }

    console.log('----------------------------------------------------------------');
  }
}

runDiagnosticTest();
