import { useEffect, useState } from 'react';

interface AppItem { label: string; port: number; url: string; up: boolean; }

export default function Apps() {
  const [apps, setApps] = useState<AppItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/fleet/webapps').then(r => r.json()).then(d => {
      setApps(d.webapps?.filter((a: AppItem) => a.up) || []);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-zinc-100">Fleet Apps</h1>
      {loading && <p className="text-zinc-500 text-sm">Scanning fleet...</p>}
      {!loading && apps.length === 0 && <p className="text-zinc-500 text-sm">No fleet webapps detected.</p>}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {apps.map(a => (
          <a key={a.url} href={a.url} target="_blank" rel="noopener noreferrer"
            className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-4 hover:bg-zinc-800 transition-colors">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500 shrink-0" />
              <span className="font-medium text-zinc-200 text-sm">{a.label}</span>
              <span className="text-xs text-zinc-600 ml-auto">:{a.port}</span>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}
