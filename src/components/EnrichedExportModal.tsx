import { useState } from 'react';
import { X, Download, Copy, Check, FileSpreadsheet } from 'lucide-react';
import type { MatchedEvLine } from '../types';
import confetti from 'canvas-confetti';

interface EnrichedExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  matchedLines: MatchedEvLine[];
  slateTitle: string;
}

export const EnrichedExportModal = ({
  isOpen,
  onClose,
  matchedLines,
  slateTitle,
}: EnrichedExportModalProps) => {
  const [copied, setCopied] = useState(false);
  const [includeEvCols, setIncludeEvCols] = useState(true);

  if (!isOpen) return null;

  // Build CSV content
  const generateCsv = (): string => {
    let headers = 'LEAGUE,DATE,HOME,AWAY,MARKET,SIDE,POINT,MODEL_PROB';
    if (includeEvCols) {
      headers += ',KALSHI_PROB,K_EDGE,POLY_PROB,P_EDGE,HALF_KELLY';
    }

    const rows = matchedLines.map((line) => {
      const r = line.modelRow;
      let base = `${r.league},${r.date},${r.home},${r.away},${r.market},${r.side},${r.point || ''},${line.modelProbPct}`;
      if (includeEvCols) {
        base += `,${line.kalshiProbPct},${line.kalshiEdgePct},${line.polyProbPct},${line.polyEdgePct},${line.halfKellyPct}`;
      }
      return base;
    });

    return [headers, ...rows].join('\n');
  };

  const csvOutput = generateCsv();

  const handleCopy = () => {
    navigator.clipboard.writeText(csvOutput);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([csvOutput], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    const safeTitle = slateTitle.replace(/[^a-zA-Z0-9]/g, '_');
    link.setAttribute('download', `8rain_Station_EV_${safeTitle}_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    try {
      confetti({
        particleCount: 80,
        spread: 70,
        origin: { y: 0.6 }
      });
    } catch (e) {}
  };

  return (
    <div className="fixed inset-0 z-50 bg-[#07090e]/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-[#121620] border border-[#1e2536] rounded-xl w-full max-w-3xl p-6 relative shadow-2xl animate-scaleUp">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-[#1f2738] mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-500/20 text-indigo-400">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base text-white">Export 8rain Station® CSV Slate</h3>
              <p className="text-xs text-[#94a3b8]">
                Download "{slateTitle}" with calculated Kalshi & Polymarket edge and Kelly %
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-[#1f2636] text-[#9ca3af] hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Column Toggle Options */}
        <div className="mb-4 flex items-center justify-between bg-[#080a0f] p-3 rounded-xl border border-[#181e2b]">
          <label className="flex items-center gap-2 text-xs font-semibold text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              checked={includeEvCols}
              onChange={(e) => setIncludeEvCols(e.target.checked)}
              className="accent-indigo-500 rounded"
            />
            Include Kalshi Edge & Polymarket Edge Columns
          </label>
          <span className="text-[11px] text-slate-500 mono">{matchedLines.length} Rows Ready</span>
        </div>

        {/* CSV Code Preview Area */}
        <div className="mb-6">
          <textarea
            readOnly
            value={csvOutput}
            className="w-full h-64 bg-[#080a0f] border border-[#181e2b] text-white p-3 rounded-lg font-mono text-xs outline-none leading-relaxed resize-none"
          />
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3">
          <button onClick={handleCopy} className="bg-[#1f2636] hover:bg-[#283146] text-slate-300 px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2">
            {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
            {copied ? 'Copied to Clipboard!' : 'Copy Raw CSV'}
          </button>

          <button onClick={handleDownload} className="bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2 rounded-lg text-xs font-semibold flex items-center gap-2">
            <Download className="w-4 h-4" />
            Download CSV Slate
          </button>
        </div>

      </div>
    </div>
  );
};
