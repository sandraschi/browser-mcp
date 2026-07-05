import { FileText, HelpCircle, Minus, Plus, Wifi, WifiOff } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useConnection } from '../../store/connection';

const ZOOM_LEVELS = [0.8, 1.0, 1.25, 1.5, 2.0, 3.0];

export default function Topbar({ onHelp, onLogs }: { onHelp: () => void; onLogs: () => void }) {
  const { state } = useConnection();
  const [zoom, setZoom] = useState(1.0);

  useEffect(() => {
    const saved = (() => { try { return parseFloat(localStorage.getItem('tauri-zoom') ?? '1.0'); } catch { return 1.0; } })();
    setZoom(ZOOM_LEVELS.includes(saved) ? saved : 1.0);
  }, []);

  const adj = (d: number) => {
    const idx = ZOOM_LEVELS.indexOf(zoom);
    const n = ZOOM_LEVELS[Math.max(0, Math.min(ZOOM_LEVELS.length - 1, idx + d))];
    if (n !== zoom) { setZoom(n); document.documentElement.style.zoom = String(n); try { localStorage.setItem('tauri-zoom', String(n)); } catch {} }
  };

  return (
    <header className="sticky top-0 z-50 border-b border-zinc-700/50 bg-zinc-950">
      <div className="flex h-12 items-center justify-between px-4">
        <span className="font-semibold text-amber text-sm">Browser MCP</span>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 text-zinc-500">
            <button type="button" onClick={() => adj(-1)} disabled={zoom <= ZOOM_LEVELS[0]} className="p-1 rounded hover:bg-zinc-800 hover:text-zinc-300 disabled:opacity-30"><Minus size={14} /></button>
            <span className="text-xs w-8 text-center tabular-nums">{Math.round(zoom * 100)}%</span>
            <button type="button" onClick={() => adj(1)} disabled={zoom >= ZOOM_LEVELS[ZOOM_LEVELS.length - 1]} className="p-1 rounded hover:bg-zinc-800 hover:text-zinc-300 disabled:opacity-30"><Plus size={14} /></button>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-zinc-500">
            {state === 'connected' ? <Wifi size={14} className="text-green-500" /> : <WifiOff size={14} className="text-red-500" />}
            <span>{state === 'connected' ? 'Online' : state === 'connecting' ? 'Connecting...' : 'Offline'}</span>
          </div>
          <button type="button" onClick={onLogs} className="p-1.5 rounded text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800" title="Logs"><FileText size={16} /></button>
          <button type="button" onClick={onHelp} className="p-1.5 rounded text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800" title="Help"><HelpCircle size={16} /></button>
        </div>
      </div>
    </header>
  );
}
