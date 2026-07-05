import { RefreshCw } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

export default function LoggerModal({ onClose }: { onClose: () => void }) {
  const [lines, setLines] = useState<string[]>([]);
  const [error, setError] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  const load = async () => {
    try {
      const r = await fetch('/api/logs?tail=200');
      if (r.ok) { const d = await r.json(); setLines(d.lines ?? []); if (d.error) setError(d.error); }
    } catch (e) { setError(String(e)); }
  };

  useEffect(() => { load(); }, []);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [lines]);

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/70" onClick={onClose}>
      <div className="border border-zinc-600 rounded-lg shadow-xl max-w-4xl w-full max-h-[85vh] flex flex-col bg-zinc-900" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between p-4 border-b border-zinc-600">
          <h2 className="text-lg font-semibold text-amber">Logs</h2>
          <div className="flex items-center gap-2">
            <button type="button" onClick={load} className="p-1.5 rounded text-zinc-400 hover:text-white hover:bg-zinc-700"><RefreshCw size={16} /></button>
            <button type="button" onClick={onClose} className="text-zinc-400 hover:text-white">Close</button>
          </div>
        </div>
        {error && <div className="px-4 py-2 text-sm text-red-400 border-b border-zinc-600">{error}</div>}
        <div className="p-4 overflow-auto text-xs font-mono flex-1 leading-5 text-zinc-300">
          {lines.length === 0 && !error && <span className="text-zinc-500">No log entries</span>}
          {lines.map((l, i) => <div key={i}>{l}</div>)}
          <div ref={bottomRef} />
        </div>
      </div>
    </div>
  );
}
