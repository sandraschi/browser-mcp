import { useEffect, useState } from 'react';

interface Provider {
  name: string;
  port: number;
  base: string;
  status: 'detected' | 'not_found';
  models: string[];
}

interface Health {
  service?: string;
  version?: string;
  port?: number;
  frontend_port?: number;
  uptime_seconds?: number;
  tool_count?: number;
}

export default function Settings() {
  const [health, setHealth] = useState<Health | null>(null);
  const [providers, setProviders] = useState<Provider[] | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<string>(() => {
    try { return localStorage.getItem('llm_provider') || ''; } catch { return ''; }
  });
  const [selectedModel, setSelectedModel] = useState<string>(() => {
    try { return localStorage.getItem('llm_model') || ''; } catch { return ''; }
  });

  useEffect(() => {
    fetch('http://127.0.0.1:10780/api/status').then(r => r.json()).then(d => {
      if (d?.status === 'ok') setHealth(d);
    }).catch(() => {});
    fetch('http://127.0.0.1:10780/api/llm/discover').then(r => r.json()).then(d => {
      setProviders(Array.isArray(d.providers) ? d.providers : []);
    }).catch(() => {});
  }, []);

  const detected = providers?.filter(p => p.status === 'detected') || [];
  const activeProvider = providers?.find(p => p.name === selectedProvider && p.status === 'detected') || null;

  const changeProvider = (name: string) => {
    setSelectedProvider(name);
    try { localStorage.setItem('llm_provider', name); } catch {}
    const p = providers?.find(x => x.name === name);
    if (p && p.models.length > 0) {
      setSelectedModel(p.models[0]);
      try { localStorage.setItem('llm_model', p.models[0]); } catch {}
    }
  };

  const changeModel = (model: string) => {
    setSelectedModel(model);
    try { localStorage.setItem('llm_model', model); } catch {}
  };

  const uptime = health?.uptime_seconds ?? 0;
  const uptimeText = uptime > 3600 ? `${Math.floor(uptime / 3600)}h ${Math.floor((uptime % 3600) / 60)}m` : `${Math.floor(uptime / 60)}m ${uptime % 60}s`;

  return (
    <div data-testid="settings-page" className="space-y-6 max-w-3xl">
      <h1 className="text-2xl font-bold text-zinc-100">Settings</h1>

      <section className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-4">
        <h2 className="text-sm font-semibold text-zinc-300 mb-3">Backend</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div data-testid="kpi-server">
            <p className="text-sm text-zinc-500">Server</p>
            <p className="text-lg font-semibold text-zinc-100">{health?.service || '...'}</p>
          </div>
          <div>
            <p className="text-sm text-zinc-500">Version</p>
            <p className="text-lg font-semibold text-zinc-100">v{health?.version || '?'}</p>
          </div>
          <div>
            <p className="text-sm text-zinc-500">Port</p>
            <p className="text-lg font-semibold text-zinc-100">{health?.port ?? '?'}</p>
          </div>
          <div>
            <p className="text-sm text-zinc-500">Uptime</p>
            <p className="text-lg font-semibold text-zinc-100">{health ? uptimeText : '...'}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 mt-3">
          <span className={`w-2 h-2 rounded-full ${health ? 'bg-green-500' : 'bg-red-500 animate-pulse'}`} />
          <span className="text-sm text-zinc-300">{health ? 'Connected' : 'Offline'}</span>
          <span className="text-sm text-zinc-500 ml-4">{health?.tool_count ?? '?'} tools registered</span>
        </div>
      </section>

      <section className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-4">
        <h2 className="text-sm font-semibold text-zinc-300 mb-3">Local LLM</h2>
        {providers === null && <p className="text-sm text-zinc-400">Probing providers...</p>}
        {providers !== null && (
          <>
            <div className="space-y-2 mb-4">
              {providers.map(p => (
                <div key={p.name} className="flex items-center gap-2 text-sm">
                  <span className={`w-2 h-2 rounded-full ${p.status === 'detected' ? 'bg-green-500' : 'bg-zinc-600'}`} />
                  <span className="text-zinc-200 capitalize w-24">{p.name}</span>
                  <span className="text-zinc-500">:{p.port}</span>
                  <span className={`${p.status === 'detected' ? 'text-green-400' : 'text-zinc-500'}`}>{p.status === 'detected' ? 'Detected' : 'Not found'}</span>
                </div>
              ))}
            </div>
            {detected.length === 0 && (
              <p className="text-sm text-amber-400">Install Ollama or LM Studio to enable AI features.</p>
            )}
            {detected.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm text-zinc-400 mb-1" htmlFor="llm-provider-select">Provider</label>
                  <select id="llm-provider-select" data-testid="llm-provider-select" value={selectedProvider} onChange={e => changeProvider(e.target.value)}
                    className="w-full px-3 py-2 rounded bg-zinc-800 border border-zinc-600 text-zinc-100 text-sm focus:outline-none focus:ring-2 focus:ring-amber">
                    {detected.map(p => <option key={p.name} value={p.name}>{p.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-zinc-400 mb-1" htmlFor="llm-model-select">Model</label>
                  <select id="llm-model-select" data-testid="llm-model-select" value={selectedModel} onChange={e => changeModel(e.target.value)}
                    className="w-full px-3 py-2 rounded bg-zinc-800 border border-zinc-600 text-zinc-100 text-sm focus:outline-none focus:ring-2 focus:ring-amber">
                    {(activeProvider?.models || []).map(m => <option key={m} value={m}>{m}</option>)}
                  </select>
                </div>
              </div>
            )}
          </>
        )}
      </section>
    </div>
  );
}
