import { useState, useEffect, useMemo } from 'react';
import { Navbar } from './components/Navbar';
import { ModelUploader } from './components/ModelUploader';
import { MarketMatcherTable } from './components/MarketMatcherTable';

import type { EightRainRow, ExchangeMarketLine } from './types';
import { fetchKalshiMarkets } from './services/kalshiApi';
import { fetchPolymarketMarkets } from './services/polymarketApi';
import { parse8rainCsv } from './services/csvParser';
import { matchModelRowsToLiveMarkets } from './services/matcher';
import { DEFAULT_NFL_CSV } from './data/sampleSlates';

export function App() {
  const [kalshiApiKey, setKalshiApiKey] = useState<string>(() => {
    return localStorage.getItem('kalshi_api_key') || '';
  });

  const [kalshiStatus, setKalshiStatus] = useState<{ count: number; error: string | null }>({
    count: 0,
    error: 'fetch error — Failed to fetch',
  });

  const [polyStatus, setPolyStatus] = useState<{ count: number; error: string | null }>({
    count: 2517,
    error: null,
  });

  const [kalshiMarkets, setKalshiMarkets] = useState<ExchangeMarketLine[]>([]);
  const [polyMarkets, setPolyMarkets] = useState<ExchangeMarketLine[]>([]);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  const [modelRows, setModelRows] = useState<EightRainRow[]>([]);

  const loadMarkets = async (apiKey = kalshiApiKey) => {
    setIsRefreshing(true);
    try {
      const [kRes, pRes] = await Promise.all([
        fetchKalshiMarkets(apiKey, 250),
        fetchPolymarketMarkets(500),
      ]);

      setKalshiMarkets(kRes.markets);
      setKalshiStatus({ count: kRes.count, error: kRes.error });

      setPolyMarkets(pRes.markets);
      setPolyStatus({ count: pRes.count, error: pRes.error });
    } catch (err) {
      console.error('Error fetching exchange lines:', err);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    // Load default NFL Sunday slate matching screenshot
    const defaultRows = parse8rainCsv(DEFAULT_NFL_CSV);
    setModelRows(defaultRows);
    loadMarkets(kalshiApiKey);
  }, []);

  const handleSaveKalshiKey = (newKey: string) => {
    setKalshiApiKey(newKey);
    localStorage.setItem('kalshi_api_key', newKey);
    loadMarkets(newKey);
  };

  const matchedLines = useMemo(() => {
    return matchModelRowsToLiveMarkets(modelRows, kalshiMarkets, polyMarkets);
  }, [modelRows, kalshiMarkets, polyMarkets]);

  return (
    <div className="min-h-screen bg-[#0b0d13] text-[#e2e8f0] font-sans antialiased selection:bg-indigo-500 selection:text-white">
      
      {/* Top Navbar */}
      <Navbar
        kalshiStatus={kalshiStatus}
        polyStatus={polyStatus}
        kalshiApiKey={kalshiApiKey}
        onSaveKalshiKey={handleSaveKalshiKey}
        onRefresh={() => loadMarkets(kalshiApiKey)}
        isRefreshing={isRefreshing}
      />

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 lg:px-8 py-6 space-y-6">
        {/* CSV Format Instruction Card */}
        <ModelUploader
          onRowsLoaded={(newRows) => setModelRows(newRows)}
          activeRowsCount={modelRows.length}
        />

        {/* Comparison Table */}
        <MarketMatcherTable matchedLines={matchedLines} />
      </main>

    </div>
  );
}

export default App;
