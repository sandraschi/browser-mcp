import { Copy, Eraser, Pause, Play, RefreshCw, Search } from 'lucide-react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { API_BASE } from '../lib/api';

const LEVELS = ['ALL', 'INFO', 'WARNING', 'ERROR', 'DEBUG'] as const;
type Level = (typeof LEVELS)[number];

const LEVEL_STYLES: Record<string, string> = {
  ERROR: 'text-red-400',
  WARNING: 'text-amber-300',
  INFO: 'text-zinc-300',
  DEBUG: 'text-zinc-500',
};

function levelOf(line: string): string {
  const m = line.match(/\[([A-Z]+)\]/);
  return m ? m[1] : 'INFO';
}

export default function Logs() {
  const [lines, setLines] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [level, setLevel] = useState<Level>('ALL');
  const [query, setQuery] = useState('');
  const [autoScroll, setAutoScroll] = useState(true);
  const [paused, setPaused] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const load = useCallback(async () => {
    try {
      const r = await fetch(`${API_BASE}/api/logs?tail=1000`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const d = await r.json();
      setLines(Array.isArray(d.lines) ? d.lines : []);
      setError('');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load logs');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    if (paused) return;
    const id = setInterval(load, 2000);
    return () => clearInterval(id);
  }, [load, paused]);

  useEffect(() => {
    if (autoScroll && lines.length > 0) bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [lines, autoScroll]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return lines.filter((l) => {
      if (level !== 'ALL' && levelOf(l) !== level) return false;
      if (q && !l.toLowerCase().includes(q)) return false;
      return true;
    });
  }, [lines, level, query]);

  const clear = async () => {
    try {
      await fetch(`${API_BASE}/api/logs/clear`, { method: 'POST' });
      setLines([]);
    } catch {
      /* ignore */
    }
  };

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(filtered.join('\n'));
    } catch {
      /* ignore */
    }
  };

  return (
    <div className="flex flex-col min-h-0 flex-1" data-testid="logs-page">
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <h1 className="text-2xl font-bold text-zinc-100">Logs</h1>
        <div className="flex-1" />
        <div className="relative">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter..."
            data-testid="logs-search"
            className="pl-8 pr-3 py-1.5 rounded-lg bg-zinc-800 border border-zinc-600 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-amber w-44"
          />
        </div>
        <select
          value={level}
          onChange={(e) => setLevel(e.target.value as Level)}
          data-testid="logs-level"
          className="px-2 py-1.5 rounded-lg bg-zinc-800 border border-zinc-600 text-sm text-zinc-100 focus:outline-none"
        >
          {LEVELS.map((l) => (
            <option key={l} value={l}>
              {l}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={copy}
          className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800"
          title="Copy"
          data-testid="logs-copy"
        >
          <Copy size={16} />
        </button>
        <button
          type="button"
          onClick={clear}
          className="p-1.5 rounded-lg text-zinc-400 hover:text-red-400 hover:bg-zinc-800"
          title="Clear"
          data-testid="logs-clear"
        >
          <Eraser size={16} />
        </button>
        <button
          type="button"
          onClick={() => setPaused((v) => !v)}
          className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800"
          title={paused ? 'Resume' : 'Pause'}
          data-testid="logs-pause"
        >
          {paused ? <Play size={16} /> : <Pause size={16} />}
        </button>
        <button
          type="button"
          onClick={() => {
            setAutoScroll(true);
            load();
          }}
          className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800"
          title="Refresh"
          data-testid="logs-refresh"
        >
          <RefreshCw size={16} />
        </button>
        <label className="flex items-center gap-1.5 text-sm text-zinc-400 select-none">
          <input
            type="checkbox"
            checked={autoScroll}
            onChange={(e) => setAutoScroll(e.target.checked)}
            className="accent-amber"
            data-testid="logs-autoscroll"
          />
          Auto-scroll
        </label>
      </div>

      {error && (
        <div className="bg-red-900/50 border border-red-700/50 text-red-300 text-sm rounded-lg p-3 mb-3">{error}</div>
      )}

      <div className="flex-1 min-h-0 overflow-auto rounded-lg border border-zinc-700/50 bg-zinc-900/60 font-mono text-xs leading-5">
        {loading && <p className="text-zinc-400 p-4">Loading...</p>}
        {!loading && filtered.length === 0 && <p className="text-zinc-400 p-4">No log entries match.</p>}
        {filtered.map((l, i) => (
          <div
            key={i}
            className={`px-3 py-0.5 border-b border-zinc-800/50 whitespace-pre-wrap break-all ${LEVEL_STYLES[levelOf(l)] ?? 'text-zinc-300'}`}
          >
            {l}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
