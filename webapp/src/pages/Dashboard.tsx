import { useEffect, useState } from 'react';
import { useConnection } from '../store/connection';

const BACKOFF = [1, 2, 4, 8, 16, 30];

export default function Dashboard() {
  const { state, setState } = useConnection();
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);
  const [tools, setTools] = useState<{ name: string }[]>([]);

  useEffect(() => {
    let attempt = 0;
    let cancelled = false;
    const poll = async () => {
      try {
        const r = await fetch('http://127.0.0.1:10776/health', { signal: AbortSignal.timeout(5000) });
        if (!cancelled) {
          if (r.ok) { const d = await r.json(); setHealth(d); setState('connected'); attempt = 0; }
          else setState('offline');
        }
      } catch { if (!cancelled) setState('offline'); }
      if (!cancelled) { attempt = Math.min(++attempt, BACKOFF.length - 1); setTimeout(poll, BACKOFF[attempt] * 1000); }
    };
    poll();
    return () => { cancelled = true; };
  }, [setState]);

  useEffect(() => {
    fetch('http://127.0.0.1:10776/mcp', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/list', params: {} }),
    }).then(r => r.json()).then(d => { if (d.result?.tools) setTools(d.result.tools); }).catch(() => {});
  }, []);

  return (
    <div data-testid="dashboard" className="space-y-6">
      <h1 className="text-2xl font-bold text-zinc-100">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-4" data-testid="kpi-server">
          <p className="text-xs text-zinc-500 mb-1">Server</p>
          <p className="text-lg font-semibold">{health?.service as string || health?.server as string || '...'}</p>
          <p className="text-xs text-zinc-600 mt-0.5">v{health?.version as string || '?'} · port {health?.port as string || health?.backend_port as string || '?'}</p>
        </div>
        <div className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-4" data-testid="kpi-tools">
          <p className="text-xs text-zinc-500 mb-1">Tools</p>
          <p className="text-lg font-semibold">{health?.tool_count as number ?? tools.length}</p>
          <p className="text-xs text-zinc-600 mt-0.5">registered</p>
        </div>
        <div className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-4" data-testid="backend-dot">
          <p className="text-xs text-zinc-500 mb-1">Status</p>
          <p className={`text-lg font-semibold flex items-center gap-2 ${state === 'connected' ? 'text-green-500' : state === 'offline' ? 'text-red-500' : 'text-amber-500'}`}>
            <span className={`w-2 h-2 rounded-full ${state === 'connected' ? 'bg-green-500' : state === 'offline' ? 'bg-red-500' : 'bg-amber-500 animate-pulse'}`} />
            {state === 'connected' ? 'Online' : state === 'offline' ? 'Offline' : 'Connecting...'}
          </p>
        </div>
      </div>
      {tools.length > 0 && (
        <div className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-4">
          <h2 className="text-sm font-semibold text-zinc-300 mb-3">Available Tools</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
            {tools.map((t) => (
              <div key={t.name} className="text-xs text-zinc-400 bg-zinc-800 px-3 py-2 rounded border border-zinc-700 truncate">{t.name}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
