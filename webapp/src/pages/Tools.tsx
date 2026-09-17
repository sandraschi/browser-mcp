import { useEffect, useState } from 'react';
import { listTools } from '../lib/mcp';

interface ToolInfo {
  name: string;
  description?: string;
}

export default function Tools() {
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    listTools()
      .then(setTools)
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-zinc-100">Tools</h1>
      {error && <div className="bg-red-900/50 p-3 rounded text-sm text-red-300">{error}</div>}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {tools.map((t) => (
          <div key={t.name} className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-4">
            <p className="text-sm font-semibold text-amber mb-1">{t.name}</p>
            {t.description && <p className="text-sm text-zinc-400">{t.description}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}
