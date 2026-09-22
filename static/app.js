document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const kalshiKeyInput = document.getElementById('kalshiKeyInput');
    const saveKeyBtn = document.getElementById('saveKeyBtn');
    const kalshiPill = document.getElementById('kalshiPill');
    const polyPill = document.getElementById('polyPill');
    const refreshBtn = document.getElementById('refreshBtn');
    const refreshSpinner = document.getElementById('refreshSpinner');
    
    const csvTextArea = document.getElementById('csvTextArea');
    const csvFileInput = document.getElementById('csvFileInput');
    const resetSampleBtn = document.getElementById('resetSampleBtn');
    const calculateBtn = document.getElementById('calculateBtn');
    
    const posEvOnlyToggle = document.getElementById('posEvOnlyToggle');
    const minEdgeInput = document.getElementById('minEdgeInput');
    const sortSelect = document.getElementById('sortSelect');
    const rowCountText = document.getElementById('rowCountText');
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    
    const tableBody = document.getElementById('tableBody');
    const tableEmptyState = document.getElementById('tableEmptyState');

    // Default Sample CSV
    const DEFAULT_CSV = `LEAGUE,DATE,HOME,AWAY,DOUBLEHEADER,SECTION,MARKET,SELECTOR,POINT,SIDE,WIN %
MLB,20260922,LAD,SD,0,spread,spread,LAD,1.5,LAD,0.695
MLB,20260922,BAL,TOR,0,spread,spread,BAL,1.5,BAL,0.687
MLB,20260922,NYY,BOS,0,head_to_head,h2h,NYY,,NYY,0.582
MLB,20260922,ATL,CIN,0,total,total,,9.5,Under,0.530
NFL,20260927,PIT,CIN,0,head_to_head,h2h,PIT,,PIT,0.626
NFL,20260927,SF,ARI,0,head_to_head,h2h,SF,,SF,0.911`;

    if (!csvTextArea.value.trim()) {
        csvTextArea.value = DEFAULT_CSV;
    }

    // State
    let rawLines = [];
    let kalshiApiKey = localStorage.getItem('kalshi_api_key') || '';

    if (kalshiApiKey) {
        kalshiKeyInput.value = kalshiApiKey;
    }

    // Save API key
    saveKeyBtn.addEventListener('click', () => {
        kalshiApiKey = kalshiKeyInput.value.trim();
        localStorage.setItem('kalshi_api_key', kalshiApiKey);
        alert('Kalshi API Key saved!');
        fetchAndCalculate(true);
    });

    // Reset Sample Slate
    resetSampleBtn.addEventListener('click', () => {
        csvTextArea.value = DEFAULT_CSV;
        fetchAndCalculate(false);
    });

    // Handle File Upload
    csvFileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (event) => {
                csvTextArea.value = event.target.result;
                fetchAndCalculate(false);
            };
            reader.readAsText(file);
        }
    });

    // Trigger Calculation / Refresh
    calculateBtn.addEventListener('click', () => fetchAndCalculate(false));
    refreshBtn.addEventListener('click', () => fetchAndCalculate(true));

    // Filters & Sorting Triggers
    posEvOnlyToggle.addEventListener('change', renderTable);
    minEdgeInput.addEventListener('input', renderTable);
    sortSelect.addEventListener('change', renderTable);
    clearFiltersBtn.addEventListener('click', () => {
        posEvOnlyToggle.checked = true;
        minEdgeInput.value = 0;
        sortSelect.value = 'k_edge_desc';
        renderTable();
    });

    // Main API Fetch & Calculation Function
    async function fetchAndCalculate(forceRefresh = false) {
        refreshSpinner.classList.remove('hidden');
        refreshBtn.disabled = true;
        
        updateStatusPill(kalshiPill, 'connecting', 'Kalshi: Connecting...');
        updateStatusPill(polyPill, 'connecting', 'Poly: Connecting...');

        try {
            // Attempt Flask API endpoint if running locally
            let isLocalBackend = false;
            try {
                const res = await fetch('/api/calculate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        csv_text: csvTextArea.value,
                        kalshi_key: kalshiApiKey,
                        force_refresh: forceRefresh
                    })
                });

                if (res.ok) {
                    const data = await res.json();
                    if (data.success) {
                        isLocalBackend = true;
                        rawLines = data.lines || [];
                        
                        updateStatusPill(
                            kalshiPill,
                            data.kalshi_status === 'connected' ? 'connected' : 'error',
                            data.kalshi_status === 'connected' ? `Kalshi: Connected (${data.kalshi_count})` : 'Kalshi: Offline'
                        );
                        updateStatusPill(
                            polyPill,
                            data.poly_status === 'connected' ? 'connected' : 'error',
                            data.poly_status === 'connected' ? `Poly: Connected (${data.poly_count})` : 'Poly: Offline'
                        );
                        renderTable();
                    }
                }
            } catch (e) {
                // Not running Flask backend -> fallback to client-side JS engine
            }

            if (!isLocalBackend) {
                // Client-side pure JS execution for GitHub Pages
                await runClientSideFetchAndMatch();
            }

        } catch (err) {
            console.error('Calculation error:', err);
            updateStatusPill(kalshiPill, 'error', 'Kalshi: Connection Error');
            updateStatusPill(polyPill, 'error', 'Poly: Connection Error');
        } finally {
            refreshSpinner.classList.add('hidden');
            refreshBtn.disabled = false;
        }
    }

    async function runClientSideFetchAndMatch() {
        const parsedRows = parseCsvInput(csvTextArea.value);
        
        const [kalshiRes, polyRes] = await Promise.all([
            fetchKalshiClientSide(kalshiApiKey),
            fetchPolymarketClientSide()
        ]);

        updateStatusPill(
            kalshiPill,
            kalshiRes.markets.length > 0 ? 'connected' : 'error',
            kalshiRes.markets.length > 0 ? `Kalshi: Connected (${kalshiRes.count})` : 'Kalshi: Offline'
        );
        updateStatusPill(
            polyPill,
            polyRes.markets.length > 0 ? 'connected' : 'error',
            polyRes.markets.length > 0 ? `Poly: Connected (${polyRes.count})` : 'Poly: Offline'
        );

        rawLines = matchRowsClientSide(parsedRows, kalshiRes.markets, polyRes.markets);
        renderTable();
    }

    // Client-side CSV Parser
    function parseCsvInput(text) {
        if (!text) return [];
        const lines = text.split('\n');
        const rows = [];
        let headerParsed = false;
        
        for (const line of lines) {
            const clean = line.trim();
            if (!clean || clean.startsWith('#')) continue;
            if (!headerParsed && (clean.toUpperCase().includes('LEAGUE') || clean.toUpperCase().includes('WIN %'))) {
                headerParsed = true;
                continue;
            }
            const parts = clean.split(',').map(p => p.trim());
            if (parts.length >= 11) {
                const winPct = parseFloat(parts[10]);
                if (!isNaN(winPct)) {
                    rows.push({
                        league: parts[0],
                        date: parts[1],
                        home: parts[2],
                        away: parts[3],
                        doubleheader: parts[4],
                        section: parts[5],
                        market: parts[6],
                        selector: parts[7],
                        point: parts[8],
                        side: parts[9],
                        winPctDecimal: winPct > 1.0 ? winPct / 100.0 : winPct
                    });
                }
            }
        }
        return rows;
    }

    // Client-side Kalshi Fetcher
    async function fetchKalshiClientSide(apiKey) {
        const seriesList = ['KXNFLGAME', 'KXMLBGAME', 'KXNBAGAME', 'KXNHLGAME', 'KXEPLGAME', 'KXNFLTOTAL', 'KXMLBTOTAL', 'KXNBATOTAL', 'KXNHLTOTAL', 'KXNFLSPREAD', 'KXMLBSPREAD', 'KXNBASPREAD', 'KXNHLSPREAD'];
        let markets = [];

        for (const s of seriesList) {
            const url = `https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=${s}&status=open&limit=200`;
            try {
                let res = await fetch(url).catch(() => null);
                if (!res || !res.ok) {
                    res = await fetch(`https://corsproxy.io/?${encodeURIComponent(url)}`).catch(() => null);
                }
                if (res && res.ok) {
                    const data = await res.json();
                    if (data && data.markets) markets.push(...data.markets);
                }
            } catch (e) {}
        }

        const unique = new Map();
        markets.forEach(m => {
            if (m && m.ticker) unique.set(m.ticker, m);
        });

        const parsed = Array.from(unique.values()).map(m => {
            let price = 0;
            if (m.yes_ask_dollars !== undefined && parseFloat(m.yes_ask_dollars) > 0) price = parseFloat(m.yes_ask_dollars);
            else if (m.last_price_dollars !== undefined && parseFloat(m.last_price_dollars) > 0) price = parseFloat(m.last_price_dollars);
            else if (m.yes_ask !== undefined && m.yes_ask > 0) price = m.yes_ask > 1 ? m.yes_ask / 100 : m.yes_ask;

            return {
                exchange: 'kalshi',
                ticker: m.ticker,
                title: m.title || m.ticker,
                price: price,
                url: `https://kalshi.com/markets/${m.ticker}`
            };
        });

        return { markets: parsed, count: parsed.length };
    }

    // Client-side Polymarket Fetcher
    async function fetchPolymarketClientSide() {
        const url = 'https://gamma-api.polymarket.com/markets?limit=500&active=true&closed=false';
        let parsed = [];
        try {
            const res = await fetch(url);
            if (res.ok) {
                const raw = await res.json();
                if (Array.isArray(raw)) {
                    parsed = raw.map(m => {
                        let price = 0.5;
                        try {
                            if (typeof m.outcomePrices === 'string') {
                                const arr = JSON.parse(m.outcomePrices);
                                price = parseFloat(arr[0]) || 0.5;
                            }
                        } catch (e) {}
                        return {
                            exchange: 'polymarket',
                            ticker: m.slug || m.id,
                            title: m.question || m.groupItemTitle || m.slug,
                            price: price,
                            url: `https://polymarket.com/market/${m.slug}`
                        };
                    });
                }
            }
        } catch (e) {}
        return { markets: parsed, count: parsed.length };
    }

    // Client-side Matcher Engine
    function matchRowsClientSide(rows, kalshiMarkets, polyMarkets) {
        return rows.map(r => {
            const kMatch = findBestMatch(r, kalshiMarkets);
            const pMatch = findBestMatch(r, polyMarkets);

            const pModel = r.winPctDecimal;

            // Date Format
            let dateFormatted = 'Sep 22';
            if (r.date && r.date.length >= 8) {
                const months = { '01':'Jan', '02':'Feb', '03':'Mar', '04':'Apr', '05':'May', '06':'Jun', '07':'Jul', '08':'Aug', '09':'Sep', '10':'Oct', '11':'Nov', '12':'Dec' };
                const m = r.date.substring(4, 6);
                const d = parseInt(r.date.substring(6, 8), 10);
                dateFormatted = `${months[m] || 'Sep'} ${d}`;
            }

            // Market Display
            let marketDisplay = (r.market || 'H2H').toUpperCase();
            if (marketDisplay === 'SPREAD') marketDisplay = `SPREAD (${r.point || '1.5'})`;
            else if (marketDisplay === 'TOTAL') marketDisplay = `TOTAL (${r.point || '9.5'})`;

            // Side Display
            let sideDisplay = r.side || r.home;

            // Kalshi Prob
            let kalshiProbPct = '—';
            let kalshiEdgePct = '—';
            let kalshiEdgeVal = -999;
            let kalshiUrl = kMatch ? kMatch.url : null;
            if (kMatch && kMatch.price > 0) {
                kalshiProbPct = `${(kMatch.price * 100).toFixed(1)}%`;
                kalshiEdgeVal = parseFloat(((pModel - kMatch.price) * 100).toFixed(1));
                kalshiEdgePct = kalshiEdgeVal > 0 ? `+${kalshiEdgeVal.toFixed(1)}%` : `${kalshiEdgeVal.toFixed(1)}%`;
            }

            // Poly Prob
            let polyProbPct = '—';
            let polyEdgePct = '—';
            let polyEdgeVal = -999;
            let polyUrl = pMatch ? pMatch.url : null;
            if (pMatch && pMatch.price > 0) {
                polyProbPct = `${(pMatch.price * 100).toFixed(1)}%`;
                polyEdgeVal = parseFloat(((pModel - pMatch.price) * 100).toFixed(1));
                polyEdgePct = polyEdgeVal > 0 ? `+${polyEdgeVal.toFixed(1)}%` : `${polyEdgeVal.toFixed(1)}%`;
            }

            // Half Kelly
            let halfKellyPct = '—';
            let halfKellyVal = 0;
            const bestProb = Math.min(kMatch ? kMatch.price : 1.0, pMatch ? pMatch.price : 1.0);
            if (bestProb < 1.0 && pModel > bestProb) {
                const fullKelly = (pModel - bestProb) / (1 - bestProb);
                const halfKelly = fullKelly * 0.5;
                if (halfKelly > 0) {
                    halfKellyVal = parseFloat((halfKelly * 100).toFixed(1));
                    halfKellyPct = `${halfKellyVal.toFixed(1)}%`;
                }
            }

            const isPosEv = kalshiEdgeVal > 0 || polyEdgeVal > 0;

            return {
                date_formatted: dateFormatted,
                home_team: r.home,
                away_team: r.away,
                market_display: marketDisplay,
                side_display: sideDisplay,
                model_prob: pModel,
                model_prob_pct: `${(pModel * 100).toFixed(1)}%`,
                kalshi_prob_pct: kalshiProbPct,
                kalshi_edge_pct: kalshiEdgePct,
                kalshi_edge_val: kalshiEdgeVal,
                kalshi_url: kalshiUrl,
                poly_prob_pct: polyProbPct,
                poly_edge_pct: polyEdgePct,
                poly_edge_val: polyEdgeVal,
                poly_url: polyUrl,
                half_kelly_pct: halfKellyPct,
                half_kelly_val: halfKellyVal,
                is_pos_ev: isPosEv
            };
        });
    }

    function findBestMatch(row, markets) {
        if (!markets || markets.length === 0) return null;
        const home = (row.home || '').toUpperCase();
        const away = (row.away || '').toUpperCase();
        const side = (row.side || '').toUpperCase();
        const section = (row.section || row.market || '').toLowerCase();
        const pointVal = row.point ? parseFloat(row.point) : null;

        let best = null;
        let highest = 0;

        for (const m of markets) {
            let score = 0;
            const title = (m.title || '').toUpperCase();
            const ticker = (m.ticker || '').toUpperCase();

            if (home && (title.includes(home) || ticker.includes(home))) score += 150;
            if (away && (title.includes(away) || ticker.includes(away))) score += 150;
            if (side && (title.includes(side) || ticker.includes(side))) score += 200;

            if (score > highest && score >= 250) {
                highest = score;
                best = m;
            }
        }

        if (!best) return null;

        let price = best.price;
        const isUnderdogSpread = section.includes('spread') && (side.includes('+') || (pointVal !== null && pointVal > 0));
        if (isUnderdogSpread && price > 0 && price < 1) {
            price = Math.round((1.0 - price) * 1000) / 1000;
        }

        return { ...best, price: price };
    }

    function updateStatusPill(pillElement, state, text) {
        const dot = pillElement.querySelector('.dot');
        const textSpan = pillElement.querySelector('.pill-text');

        textSpan.textContent = text;
        dot.className = 'dot';
        if (state === 'connected') dot.classList.add('dot-green');
        else if (state === 'error') dot.classList.add('dot-red');
        else dot.classList.add('dot-yellow');
    }

    // Render & Filter Table Rows
    function renderTable() {
        const showPosOnly = posEvOnlyToggle.checked;
        const minEdge = parseFloat(minEdgeInput.value) || 0;
        const sortBy = sortSelect.value;

        let filtered = rawLines.filter(row => {
            if (showPosOnly && !row.is_pos_ev) return false;
            
            const maxEdge = Math.max(
                row.kalshi_edge_val > -900 ? row.kalshi_edge_val : -999,
                row.poly_edge_val > -900 ? row.poly_edge_val : -999
            );

            if (maxEdge < minEdge) return false;

            return true;
        });

        // Sorting Logic
        filtered.sort((a, b) => {
            if (sortBy === 'k_edge_desc') return b.kalshi_edge_val - a.kalshi_edge_val;
            if (sortBy === 'p_edge_desc') return b.poly_edge_val - a.poly_edge_val;
            if (sortBy === 'model_prob_desc') return b.model_prob - a.model_prob;
            if (sortBy === 'matchup_asc') return `${a.home_team} ${a.away_team}`.localeCompare(`${b.home_team} ${b.away_team}`);
            return 0;
        });

        rowCountText.textContent = `Showing ${filtered.length} / ${rawLines.length} rows`;

        if (filtered.length === 0) {
            tableBody.innerHTML = '';
            tableEmptyState.classList.remove('hidden');
            return;
        }

        tableEmptyState.classList.add('hidden');

        tableBody.innerHTML = filtered.map(row => {
            const posClass = row.is_pos_ev ? 'row-pos-ev' : '';

            // Kalshi Edge Tag
            let kalshiEdgeTag = `<span class="badge-edge-neg">${row.kalshi_edge_pct}</span>`;
            if (row.kalshi_edge_val > 0) {
                kalshiEdgeTag = `<span class="badge-edge-pos">${row.kalshi_edge_pct}</span>`;
            }

            // Poly Edge Tag
            let polyEdgeTag = `<span class="badge-edge-neg">${row.poly_edge_pct}</span>`;
            if (row.poly_edge_val > 0) {
                polyEdgeTag = `<span class="badge-edge-pos">${row.poly_edge_pct}</span>`;
            }

            // Kelly Tag
            let kellyTag = `<span class="font-mono">—</span>`;
            if (row.half_kelly_val > 0) {
                kellyTag = `<span class="badge-kelly">${row.half_kelly_pct}</span>`;
            }

            // Link Buttons
            let kalshiBtn = row.kalshi_url ? `<a href="${row.kalshi_url}" target="_blank" rel="noopener" class="exchange-link link-kalshi">Kalshi ↗</a>` : '';
            let polyBtn = row.poly_url ? `<a href="${row.poly_url}" target="_blank" rel="noopener" class="exchange-link link-poly">Poly ↗</a>` : '';

            return `
                <tr class="${posClass}">
                    <td class="font-mono">${row.date_formatted}</td>
                    <td class="matchup-cell">${row.home_team} vs ${row.away_team}</td>
                    <td class="font-mono">${row.market_display}</td>
                    <td class="side-cell">${row.side_display}</td>
                    <td class="font-mono">${row.model_prob_pct}</td>
                    <td class="font-mono">${row.kalshi_prob_pct}</td>
                    <td>${kalshiEdgeTag}</td>
                    <td class="font-mono">${row.poly_prob_pct}</td>
                    <td>${polyEdgeTag}</td>
                    <td>${kellyTag}</td>
                    <td>
                        <div class="link-buttons">
                            ${kalshiBtn}
                            ${polyBtn}
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    }

    // Initial load
    fetchAndCalculate(false);
});
