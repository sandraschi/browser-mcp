import { Download, Trash2 } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

const STORAGE_KEY = 'browser-mcp-chat-history';
const MAX = 100;

interface Msg { role: 'user' | 'assistant'; content: string; ts?: string; }

function load(): Msg[] { try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); } catch { return []; } }

export default function Chat() {
  const [msgs, setMsgs] = useState<Msg[]>(load);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [model, setModel] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { try { localStorage.setItem(STORAGE_KEY, JSON.stringify(msgs.slice(-MAX))); } catch {} }, [msgs]);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [msgs]);

  useEffect(() => {
    fetch('http://127.0.0.1:10776/mcp', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/list', params: {} }),
    }).then(r => r.json()).then(d => {
      const ts = d.result?.tools || [];
      const ctx = ts.map((t: { name: string; description?: string }) => `  - ${t.name}: ${t.description || 'No description'}`).join('\n');
      setSkillCtx(`\n\nAvailable tools:\n${ctx}`);
    }).catch(() => {});
    const saved = (() => { try { return localStorage.getItem('browser-mcp-default-model'); } catch { return ''; } })();
    if (saved) setModel(saved);
  }, []);

  const [skillCtx, setSkillCtx] = useState('');

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const um: Msg = { role: 'user', content: input.trim(), ts: new Date().toISOString() };
    const updated = [...msgs, um];
    setMsgs(updated); setInput(''); setLoading(true);
    try {
      const r = await fetch('http://127.0.0.1:10776/api/llm/chat', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [{ role: 'system', content: `You are a browser automation assistant.${skillCtx}` }, ...updated],
          model: model || 'gemma4:12b',
        }),
      });
      const txt = await r.text();
      let data: Record<string, unknown>;
      try { data = JSON.parse(txt); } catch { setMsgs(m => [...m, { role: 'assistant', content: `Parse error: ${txt.slice(0, 100)}` }]); return; }
      if (data.error) setMsgs(m => [...m, { role: 'assistant', content: `Error: ${data.error}` }]);
      else {
        const c = (data as any).message?.content || (data as any).choices?.[0]?.message?.content || JSON.stringify(data);
        setMsgs(m => [...m, { role: 'assistant', content: String(c), ts: new Date().toISOString() }]);
      }
    } catch (e) { setMsgs(m => [...m, { role: 'assistant', content: `Failed: ${e instanceof Error ? e.message : 'Unknown'}` }]); }
    finally { setLoading(false); }
  };

  return (
    <div className="flex flex-col flex-1 min-h-0" data-testid="chat-page">
      <div className="flex items-center gap-2 mb-4" data-testid="chat-controls">
        <input type="text" value={model} onChange={e => { setModel(e.target.value); try { localStorage.setItem('browser-mcp-default-model', e.target.value); } catch {} }}
          placeholder="Model (e.g. gemma4:12b)" className="px-3 py-1.5 rounded bg-zinc-800 border border-zinc-600 text-zinc-100 text-sm w-44 placeholder-zinc-500" />
        <div className="flex-1" />
        <button type="button" onClick={() => { setMsgs([]); try { localStorage.removeItem(STORAGE_KEY); } catch {} }} disabled={msgs.length === 0}
          className="p-1.5 rounded text-zinc-500 hover:text-red-400 disabled:opacity-30" data-testid="chat-clear" title="Clear"><Trash2 size={16} /></button>
        <button type="button" onClick={() => {
          const blob = new Blob([msgs.map(m => `[${m.ts || '?'}] ${m.role}: ${m.content}`).join('\n')], { type: 'text/plain' });
          const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `browser-mcp-chat-${new Date().toISOString().slice(0, 10)}.txt`; a.click();
        }} disabled={msgs.length === 0} className="p-1.5 rounded text-zinc-500 hover:text-zinc-200 disabled:opacity-30" data-testid="chat-export" title="Export"><Download size={16} /></button>
      </div>
      <div className="flex-1 overflow-auto rounded-lg bg-zinc-800/50 border border-zinc-700/50 p-4 space-y-3" data-testid="chat-messages">
        {msgs.length === 0 && <p className="text-zinc-500 text-center py-8">Ask about browser tasks, bookmarks, or anything.</p>}
        {msgs.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${m.role === 'user' ? 'bg-amber/20 text-zinc-200' : 'bg-zinc-700/50 text-zinc-300'}`}>
              <p className="whitespace-pre-wrap">{m.content}</p>
            </div>
          </div>
        ))}
        {loading && <div className="flex justify-start"><div className="bg-zinc-700/50 rounded-lg px-3 py-2 text-zinc-500 text-sm animate-pulse">Thinking...</div></div>}
        <div ref={bottomRef} />
      </div>
      <form onSubmit={submit} className="mt-3 flex gap-2">
        <input type="text" value={input} onChange={e => setInput(e.target.value)} placeholder="Message..." disabled={loading}
          className="flex-1 px-3 py-2 rounded-lg bg-zinc-800 border border-zinc-600 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-amber disabled:opacity-50" data-testid="chat-input" />
        <button type="submit" disabled={loading || !input.trim()}
          className="px-4 py-2 rounded-lg bg-amber text-zinc-900 font-medium hover:bg-amber/90 disabled:opacity-50" data-testid="chat-send">Send</button>
      </form>
    </div>
  );
}
