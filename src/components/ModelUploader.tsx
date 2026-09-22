import { useState } from 'react';
import { parse8rainCsv } from '../services/csvParser';
import type { EightRainRow } from '../types';
import { DEFAULT_NFL_CSV } from '../data/sampleSlates';

interface ModelUploaderProps {
  onRowsLoaded: (rows: EightRainRow[]) => void;
  activeRowsCount: number;
}

export const ModelUploader = ({ onRowsLoaded, activeRowsCount }: ModelUploaderProps) => {
  const [rawInput, setRawInput] = useState<string>('');
  const [isExpanded, setIsExpanded] = useState<boolean>(false);

  const handleParse = () => {
    if (!rawInput.trim()) return;
    const rows = parse8rainCsv(rawInput);
    if (rows.length > 0) {
      onRowsLoaded(rows);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      const content = evt.target?.result as string;
      setRawInput(content);
      const rows = parse8rainCsv(content);
      if (rows.length > 0) onRowsLoaded(rows);
    };
    reader.readAsText(file);
  };

  const handleLoadDefault = () => {
    setRawInput(DEFAULT_NFL_CSV);
    const rows = parse8rainCsv(DEFAULT_NFL_CSV);
    onRowsLoaded(rows);
  };

  return (
    <div className="bg-[#121620] border border-[#1e2536] rounded-xl p-5 text-xs text-[#94a3b8]">
      
      {/* Header Label */}
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-xs font-bold text-[#e2e8f0]">
          Expected CSV format <span className="text-[#64748b] font-normal">— columns (header row required):</span>
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={handleLoadDefault}
            className="text-[11px] font-medium text-indigo-400 hover:text-indigo-300 underline"
          >
            Load NFL Sunday Slate
          </button>
          <span className="text-[#334155]">|</span>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-[11px] font-medium text-slate-400 hover:text-white"
          >
            {isExpanded ? 'Collapse Input ▲' : 'Paste / Upload CSV ▼'}
          </button>
        </div>
      </div>

      {/* Code Block Snippet */}
      <div className="bg-[#080a0f] border border-[#181e2b] rounded-lg p-3.5 font-mono text-[11px] text-[#93c5fd] leading-relaxed overflow-x-auto mb-3">
        <div>LEAGUE,DATE,HOME,AWAY,MARKET,SIDE,POINT,MODEL_PROB</div>
        <div className="text-[#cbd5e1]">NFL,20260927,KC,BUF,h2h,home,,0.62</div>
        <div className="text-[#cbd5e1]">NFL,20260927,KC,BUF,h2h,away,,0.38</div>
        <div className="text-[#cbd5e1]">NFL,20260927,KC,BUF,spread,home,-3.5,0.52</div>
        <div className="text-[#cbd5e1]">NFL,20260927,KC,BUF,total,over,47.5,0.55</div>
      </div>

      {/* Subtitle */}
      <p className="text-[#64748b] text-[11px] mb-3">
        Also accepts the existing model output format with <code className="bg-[#181e2b] text-[#cbd5e1] px-1.5 py-0.5 rounded font-mono">WIN %</code> column.
      </p>

      {/* Expandable Textarea & File Upload Input */}
      {isExpanded && (
        <div className="mt-4 pt-3 border-t border-[#1e2536] space-y-3">
          <textarea
            value={rawInput}
            onChange={(e) => setRawInput(e.target.value)}
            placeholder="Paste raw CSV content here..."
            className="w-full h-28 bg-[#080a0f] border border-[#181e2b] text-white p-3 rounded-lg font-mono text-xs outline-none focus:border-indigo-500"
          />

          <div className="flex items-center justify-between">
            <label className="bg-[#1f2636] hover:bg-[#283146] text-[#d1d5db] px-3 py-1.5 rounded-md border border-[#2e374d] cursor-pointer text-xs font-medium">
              Choose CSV File...
              <input type="file" accept=".csv,.txt" onChange={handleFileUpload} className="hidden" />
            </label>

            <button
              onClick={handleParse}
              className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-4 py-1.5 rounded-md text-xs"
            >
              Parse & Match Lines ({activeRowsCount} active)
            </button>
          </div>
        </div>
      )}

    </div>
  );
};
