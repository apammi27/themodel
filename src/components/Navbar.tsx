import { useState } from 'react';
import { RefreshCw } from 'lucide-react';

interface NavbarProps {
  kalshiStatus: { count: number; error: string | null };
  polyStatus: { count: number; error: string | null };
  kalshiApiKey: string;
  onSaveKalshiKey: (key: string) => void;
  onRefresh: () => void;
  isRefreshing: boolean;
}

export const Navbar = ({
  kalshiStatus,
  polyStatus,
  kalshiApiKey,
  onSaveKalshiKey,
  onRefresh,
  isRefreshing,
}: NavbarProps) => {
  const [tempKey, setTempKey] = useState(kalshiApiKey);

  const handleSave = () => {
    onSaveKalshiKey(tempKey);
  };

  const timeString = 'live 03:13 AM';

  return (
    <header className="w-full border-b border-[#1b202e] bg-[#0b0d13] px-4 lg:px-8 py-3 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        
        {/* Title */}
        <div className="flex items-center gap-2">
          <h1 className="text-base font-bold text-white tracking-tight">
            8rain Station® EV Checker
          </h1>
        </div>

        {/* Right Header Controls */}
        <div className="flex flex-wrap items-center gap-3 text-xs">
          
          {/* Kalshi API Key Input */}
          <div className="flex items-center gap-2">
            <span className="text-[#9ca3af] font-medium">Kalshi API key</span>
            <input
              type="password"
              placeholder="••••••••••••••••••••"
              value={tempKey}
              onChange={(e) => setTempKey(e.target.value)}
              className="w-52 px-3 py-1 bg-[#141824] border border-[#242b3d] text-white rounded-md text-xs font-mono outline-none focus:border-indigo-500"
            />
            <button
              onClick={handleSave}
              className="bg-[#1f2636] hover:bg-[#283146] text-[#d1d5db] px-3 py-1 rounded-md border border-[#2e374d] font-medium transition-colors"
            >
              Save
            </button>
          </div>

          {/* Kalshi Status Pill */}
          <div className={`px-3 py-1 rounded-full text-xs font-medium border flex items-center gap-1.5 ${
            kalshiStatus.error
              ? 'bg-[#3f191f] text-[#f87171] border-[#5e232b]'
              : 'bg-[#132e27] text-[#34d399] border-[#1e4a3f]'
          }`}>
            <span>Kalshi: {kalshiStatus.error ? kalshiStatus.error : `${kalshiStatus.count} markets - ${timeString}`}</span>
          </div>

          {/* Poly Status Pill */}
          <div className="px-3 py-1 rounded-full text-xs font-medium bg-[#132e27] text-[#34d399] border border-[#1e4a3f]">
            <span>Poly: {polyStatus.count} markets - {timeString}</span>
          </div>

          {/* Refresh Button */}
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="bg-[#1f2636] hover:bg-[#283146] text-[#d1d5db] px-3 py-1 rounded-md border border-[#2e374d] font-medium transition-colors flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3 h-3 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

        </div>

      </div>
    </header>
  );
};
