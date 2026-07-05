import { useEffect, useState } from 'react';

interface BrowserInfo {
  installed: boolean;
  path?: string;
  profiles?: string[];
}

export default function Dashboard() {
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);
  const [browsers, setBrowsers] = useState<Record<string, BrowserInfo> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetch('/health').then(r => r.json()),
      fetch('/mcp?command=list_browsers').then(r => r.json()).catch(() => null),
    ])
      .then(([h, b]) => {
        setHealth(h);
        if (b?.result) setBrowsers(b.result.browsers);
      })
      .catch(e => setError(e.message));
  }, []);

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Dashboard</h2>

      {error && <div className="bg-red-900 p-3 rounded mb-4">{error}</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="bg-gray-800 p-4 rounded" data-testid="kpi-server">
          <h3 className="text-sm text-gray-400 mb-1">Service</h3>
          <p className="text-xl">{health?.service as string || '...'}</p>
          <p className="text-xs text-gray-500 mt-1">v{health?.version as string || '?'}</p>
        </div>
        <div className="bg-gray-800 p-4 rounded" data-testid="kpi-port">
          <h3 className="text-sm text-gray-400 mb-1">Port</h3>
          <p className="text-xl">{health?.port as string || '...'}</p>
        </div>
      </div>

      <h3 className="text-lg font-semibold mb-3">Detected Browsers</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {browsers && Object.entries(browsers).map(([name, info]) => (
          <div key={name} className={`p-3 rounded ${info.installed ? 'bg-gray-800' : 'bg-gray-800/50 opacity-60'}`}>
            <div className="flex items-center justify-between">
              <span className="font-medium capitalize">{name}</span>
              <span className={`text-xs px-2 py-0.5 rounded ${info.installed ? 'bg-green-700' : 'bg-gray-600'}`}>
                {info.installed ? 'Installed' : 'Not found'}
              </span>
            </div>
            {info.path && <p className="text-xs text-gray-400 mt-1 truncate">{info.path}</p>}
            {info.profiles && (
              <p className="text-xs text-gray-500 mt-1">Profiles: {info.profiles.join(', ')}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
