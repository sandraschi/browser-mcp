import { useEffect, useState } from 'react';

interface ToolInfo { name: string; description?: string; }

export default function Tools() {
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch('http://127.0.0.1:10776/mcp', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/list', params: {} }),
    }).then(r => r.json()).then(d => {
      if (d.result?.tools) setTools(d.result.tools);
      else setError(d.error?.message || 'No tools returned');
    }).catch(e => setError(e.message));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-zinc-100">Tools</h1>
      {error && <div className="bg-red-900/50 p-3 rounded text-sm text-red-300">{error}</div>}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {tools.map(t => (
          <div key={t.name} className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-4">
            <p className="text-sm font-semibold text-amber mb-1">{t.name}</p>
            {t.description && <p className="text-xs text-zinc-400">{t.description}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}
