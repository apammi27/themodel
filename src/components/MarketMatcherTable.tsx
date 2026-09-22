import { useState } from 'react';
import type { MatchedEvLine, FilterState } from '../types';

interface MarketMatcherTableProps {
  matchedLines: MatchedEvLine[];
}

export const MarketMatcherTable = ({ matchedLines }: MarketMatcherTableProps) => {
  const [filters, setFilters] = useState<FilterState>({
    posEvOnly: false,
    minEdge: 0,
    sortBy: 'k_edge',
  });

  // Filtering
  const filteredLines = matchedLines.filter((line) => {
    if (filters.posEvOnly && !line.isPosEv) return false;
    
    if (filters.minEdge > 0) {
      const maxEdge = Math.max(line.kalshiEdgeVal, line.polyEdgeVal);
      if (maxEdge < filters.minEdge) return false;
    }

    return true;
  });

  // Sorting
  const sortedLines = [...filteredLines].sort((a, b) => {
    if (filters.sortBy === 'k_edge') return b.kalshiEdgeVal - a.kalshiEdgeVal;
    if (filters.sortBy === 'p_edge') return b.polyEdgeVal - a.polyEdgeVal;
    if (filters.sortBy === 'model_prob') return b.modelProbDecimal - a.modelProbDecimal;
    return a.dateFormatted.localeCompare(b.dateFormatted);
  });

  const handleClearFilters = () => {
    setFilters({
      posEvOnly: false,
      minEdge: 0,
      sortBy: 'k_edge',
    });
  };

  return (
    <div className="space-y-4 animate-fadeIn">
      
      {/* Filter Bar */}
      <div className="bg-[#121620] border border-[#1e2536] rounded-xl p-3 px-5 flex flex-wrap items-center justify-between gap-4 text-xs text-[#d1d5db]">
        
        {/* Left Filter Controls */}
        <div className="flex items-center gap-6">
          {/* +EV rows only Checkbox */}
          <label className="flex items-center gap-2 cursor-pointer font-medium hover:text-white">
            <input
              type="checkbox"
              checked={filters.posEvOnly}
              onChange={(e) => setFilters({ ...filters, posEvOnly: e.target.checked })}
              className="accent-[#10b981] rounded w-3.5 h-3.5"
            />
            <span>+EV rows only</span>
          </label>

          {/* Min edge % Input */}
          <div className="flex items-center gap-1.5 text-[#9ca3af]">
            <span>Min edge:</span>
            <input
              type="number"
              value={filters.minEdge}
              onChange={(e) => setFilters({ ...filters, minEdge: parseFloat(e.target.value) || 0 })}
              className="w-12 text-center bg-[#080a0f] border border-[#242b3d] text-white py-0.5 rounded font-mono font-bold outline-none"
            />
            <span>%</span>
          </div>

          {/* Sort By Dropdown */}
          <div className="flex items-center gap-1.5 text-[#9ca3af]">
            <span>Sort by:</span>
            <select
              value={filters.sortBy}
              onChange={(e) => setFilters({ ...filters, sortBy: e.target.value as any })}
              className="bg-[#080a0f] border border-[#242b3d] text-white px-2.5 py-1 rounded font-medium outline-none cursor-pointer"
            >
              <option value="k_edge">K Edge ↓</option>
              <option value="p_edge">P Edge ↓</option>
              <option value="model_prob">Model % ↓</option>
              <option value="date">Date ↑</option>
            </select>
          </div>
        </div>

        {/* Right Info & Clear */}
        <div className="flex items-center gap-4">
          <span className="text-[#9ca3af] font-mono text-xs">{sortedLines.length} rows</span>
          <button
            onClick={handleClearFilters}
            className="bg-[#1f2636] hover:bg-[#283146] text-[#9ca3af] hover:text-white px-3 py-1 rounded-md text-xs font-medium border border-[#2e374d]"
          >
            ✕ Clear
          </button>
        </div>

      </div>

      {/* Main Table */}
      <div className="bg-[#0c0f17] border border-[#1b2130] rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            
            {/* Table Header */}
            <thead>
              <tr className="bg-[#121724] text-[#6b7280] uppercase tracking-wider font-bold text-[11px] border-b border-[#1f2738]">
                <th className="py-3 px-4">DATE</th>
                <th className="py-3 px-4">MATCHUP</th>
                <th className="py-3 px-4">MARKET</th>
                <th className="py-3 px-4">SIDE</th>
                <th className="py-3 px-4">MODEL %</th>
                <th className="py-3 px-4">KALSHI %</th>
                <th className="py-3 px-4">K EDGE</th>
                <th className="py-3 px-4">POLY %</th>
                <th className="py-3 px-4">P EDGE</th>
                <th className="py-3 px-4">½ KELLY</th>
                <th className="py-3 px-4">LINKS</th>
              </tr>
            </thead>

            {/* Table Body */}
            <tbody className="divide-y divide-[#181f2e]">
              {sortedLines.length === 0 ? (
                <tr>
                  <td colSpan={11} className="py-12 text-center text-[#64748b]">
                    No rows match current filter settings.
                  </td>
                </tr>
              ) : (
                sortedLines.map((line) => {
                  const isPosK = line.kalshiEdgeVal > 0;
                  const isPosP = line.polyEdgeVal > 0;
                  const isPosRow = isPosK || isPosP;

                  return (
                    <tr
                      key={line.id}
                      className={`hover:bg-[#161c2b] transition-colors ${
                        isPosRow ? 'border-l-2 border-l-[#10b981]' : ''
                      }`}
                    >
                      {/* DATE */}
                      <td className="py-3 px-4 text-[#9ca3af] font-mono text-xs whitespace-nowrap">
                        {line.dateFormatted}
                      </td>

                      {/* MATCHUP */}
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span className="font-bold text-white">{line.homeTeam}</span>
                        <span className="text-[#64748b] text-[11px] mx-1 font-normal">vs</span>
                        <span className="font-bold text-white">{line.awayTeam}</span>
                      </td>

                      {/* MARKET */}
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span className="bg-[#1e293b] text-[#93c5fd] font-bold text-[10px] px-2 py-0.5 rounded border border-[#334155] tracking-wide uppercase">
                          {line.marketDisplay}
                        </span>
                      </td>

                      {/* SIDE */}
                      <td className="py-3 px-4 font-bold text-white text-xs whitespace-nowrap">
                        {line.sideDisplay}
                      </td>

                      {/* MODEL % */}
                      <td className="py-3 px-4 font-bold text-white font-mono text-xs whitespace-nowrap">
                        {line.modelProbPct}
                      </td>

                      {/* KALSHI % */}
                      <td className="py-3 px-4 text-[#cbd5e1] font-mono text-xs whitespace-nowrap">
                        {line.kalshiProbPct}
                      </td>

                      {/* K EDGE */}
                      <td className="py-3 px-4 font-mono text-xs whitespace-nowrap">
                        {line.kalshiEdgePct !== '—' ? (
                          isPosK ? (
                            <span className="font-bold text-[#34d399]">{line.kalshiEdgePct}</span>
                          ) : (
                            <span className="text-[#94a3b8]">{line.kalshiEdgePct}</span>
                          )
                        ) : (
                          <span className="text-[#475569]">—</span>
                        )}
                      </td>

                      {/* POLY % */}
                      <td className="py-3 px-4 text-[#cbd5e1] font-mono text-xs whitespace-nowrap">
                        {line.polyProbPct}
                      </td>

                      {/* P EDGE */}
                      <td className="py-3 px-4 font-mono text-xs whitespace-nowrap">
                        {line.polyEdgePct !== '—' ? (
                          isPosP ? (
                            <span className="font-bold text-[#34d399]">{line.polyEdgePct}</span>
                          ) : (
                            <span className="text-[#94a3b8]">{line.polyEdgePct}</span>
                          )
                        ) : (
                          <span className="text-[#475569]">—</span>
                        )}
                      </td>

                      {/* ½ KELLY */}
                      <td className="py-3 px-4 text-[#cbd5e1] font-mono text-xs whitespace-nowrap">
                        {line.halfKellyPct !== '—' ? (
                          <span className="font-medium">{line.halfKellyPct}</span>
                        ) : (
                          <span className="text-[#475569]">—</span>
                        )}
                      </td>

                      {/* LINKS */}
                      <td className="py-3 px-4 font-semibold text-xs whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          {line.polyUrl && (
                            <a
                              href={line.polyUrl}
                              target="_blank"
                              rel="noreferrer"
                              className="text-[#60a5fa] hover:text-[#93c5fd] hover:underline flex items-center gap-0.5"
                            >
                              <span>P</span>
                              <span className="text-[10px]">↗</span>
                            </a>
                          )}
                          {line.kalshiUrl && (
                            <a
                              href={line.kalshiUrl}
                              target="_blank"
                              rel="noreferrer"
                              className="text-[#60a5fa] hover:text-[#93c5fd] hover:underline flex items-center gap-0.5"
                            >
                              <span>K</span>
                              <span className="text-[10px]">↗</span>
                            </a>
                          )}
                          {!line.polyUrl && !line.kalshiUrl && (
                            <span className="text-[#475569]">—</span>
                          )}
                        </div>
                      </td>

                    </tr>
                  );
                })
              )}
            </tbody>

          </table>
        </div>
      </div>

    </div>
  );
};
