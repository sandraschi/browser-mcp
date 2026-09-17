import { Download, Trash2 } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { listTools } from '../lib/mcp';

const STORAGE_KEY = 'browser-mcp-chat-history';
const PERSONALITY_KEY = 'browser-mcp-chat-personality';
const MAX = 100;

interface Msg {
  role: 'user' | 'assistant';
  content: string;
  ts?: string;
}

const PERSONALITIES = [
  {
    id: 'browser-automator',
    label: 'Browser Automator',
    prompt:
      'You are an expert browser automation assistant. Help users control browser tabs, manage bookmarks, fill forms, and automate web tasks. Be practical and detail-oriented.',
  },
  {
    id: 'web-scraper',
    label: 'Web Scraper',
    prompt:
      'You are a web scraping and data extraction specialist. Advise on page navigation, DOM interaction, and efficient data collection strategies from web pages.',
  },
  {
    id: 'quick-summarizer',
    label: 'Quick Summarizer',
    prompt: 'You are a concise assistant. Answer in 1-3 sentences. Be direct and to the point.',
  },
  { id: 'custom', label: 'Custom', prompt: '' },
];

const EXAMPLE_PROMPTS = [
  {
    group: 'Navigation',
    items: [
      'Open a new tab and navigate to https://example.com',
      'List all open browser tabs',
      'Search for "MCP servers" on Google',
    ],
  },
  {
    group: 'Bookmarks',
    items: [
      'Bookmark the current page as "Reference"',
      'List all bookmarks in the dev folder',
      'Search bookmarks for "documentation"',
    ],
  },
];

function load(): Msg[] {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
  } catch {
    return [];
  }
}

export default function Chat() {
  const [msgs, setMsgs] = useState<Msg[]>(load);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [model, setModel] = useState('');
  const [personality, setPersonality] = useState(() => {
    try {
      return localStorage.getItem(PERSONALITY_KEY) || 'browser-automator';
    } catch {
      return 'browser-automator';
    }
  });
  const [showExamples, setShowExamples] = useState(true);
  const [skillCtx, setSkillCtx] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(msgs.slice(-MAX)));
    } catch {}
  }, [msgs]);
  useEffect(() => {
    if (msgs.length > 0) bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [msgs]);

  useEffect(() => {
    listTools()
      .then((ts) => {
        const ctx = ts
          .map((t: { name: string; description?: string }) => `  - ${t.name}: ${t.description || 'No description'}`)
          .join('\n');
        setSkillCtx(`\n\nAvailable tools:\n${ctx}`);
      })
      .catch(() => {});
    const saved = (() => {
      try {
        return localStorage.getItem('browser-mcp-default-model');
      } catch {
        return '';
      }
    })();
    if (saved) setModel(saved);
  }, []);

  const handlePersonalityChange = (id: string) => {
    setPersonality(id);
    try {
      localStorage.setItem(PERSONALITY_KEY, id);
    } catch {}
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    setShowExamples(false);
    const um: Msg = { role: 'user', content: input.trim(), ts: new Date().toISOString() };
    const updated = [...msgs, um];
    setMsgs(updated);
    setInput('');
    setLoading(true);
    const sel = PERSONALITIES.find((p) => p.id === personality);
    const personalityPrompt = sel?.prompt ? `\n\nRole:\n${sel.prompt}` : '';
    try {
      const r = await fetch('/api/llm/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [
            { role: 'system', content: `You are a browser automation assistant.${skillCtx}${personalityPrompt}` },
            ...updated,
          ],
          model: model || 'gemma4:12b',
        }),
      });
      const txt = await r.text();
      let data: Record<string, unknown>;
      try {
        data = JSON.parse(txt);
      } catch {
        setMsgs((m) => [...m, { role: 'assistant', content: `Parse error: ${txt.slice(0, 100)}` }]);
        return;
      }
      if (data.error) setMsgs((m) => [...m, { role: 'assistant', content: `Error: ${data.error}` }]);
      else {
        const c =
          (data as any).message?.content || (data as any).choices?.[0]?.message?.content || JSON.stringify(data);
        setMsgs((m) => [...m, { role: 'assistant', content: String(c), ts: new Date().toISOString() }]);
      }
    } catch (e) {
      setMsgs((m) => [...m, { role: 'assistant', content: `Failed: ${e instanceof Error ? e.message : 'Unknown'}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col flex-1 min-h-0" data-testid="chat-page">
      <div className="flex items-center gap-2 mb-4" data-testid="chat-controls">
        <input
          type="text"
          value={model}
          onChange={(e) => {
            setModel(e.target.value);
            try {
              localStorage.setItem('browser-mcp-default-model', e.target.value);
            } catch {}
          }}
          placeholder="Model (e.g. gemma4:12b)"
          className="px-3 py-1.5 rounded bg-zinc-800 border border-zinc-600 text-zinc-100 text-sm w-36 placeholder-zinc-500"
        />
        <select
          value={personality}
          onChange={(e) => handlePersonalityChange(e.target.value)}
          data-testid="personality-select"
          className="px-2 py-1.5 rounded bg-zinc-800 border border-zinc-600 text-zinc-100 text-sm focus:outline-none"
        >
          {PERSONALITIES.map((p) => (
            <option key={p.id} value={p.id}>
              {p.label}
            </option>
          ))}
        </select>
        <span className="text-xs text-zinc-400 bg-zinc-800/50 px-1.5 py-0.5 rounded font-mono">skill:browser</span>
        <div className="flex-1" />
        <button
          type="button"
          onClick={() => {
            setMsgs([]);
            try {
              localStorage.removeItem(STORAGE_KEY);
            } catch {}
          }}
          disabled={msgs.length === 0}
          className="p-1.5 rounded text-zinc-500 hover:text-red-400 disabled:opacity-30"
          data-testid="chat-clear"
          title="Clear"
        >
          <Trash2 size={16} />
        </button>
        <button
          type="button"
          onClick={() => {
            const blob = new Blob([msgs.map((m) => `[${m.ts || '?'}] ${m.role}: ${m.content}`).join('\n')], {
              type: 'text/plain',
            });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = `browser-mcp-chat-${new Date().toISOString().slice(0, 10)}.txt`;
            a.click();
          }}
          disabled={msgs.length === 0}
          className="p-1.5 rounded text-zinc-500 hover:text-zinc-200 disabled:opacity-30"
          data-testid="chat-export"
          title="Export"
        >
          <Download size={16} />
        </button>
      </div>
      {showExamples && msgs.length === 0 && (
        <div className="flex flex-wrap gap-1.5 mb-2" data-testid="example-prompts">
          {EXAMPLE_PROMPTS.map((group) => (
            <div key={group.group} className="flex items-center gap-1 mr-2">
              <span className="text-xs text-zinc-400 mr-1">{group.group}:</span>
              {group.items.map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => {
                    setInput(p);
                  }}
                  className="px-2 py-0.5 rounded text-xs bg-zinc-800 text-zinc-400 hover:bg-zinc-700 transition-colors border border-zinc-700/30"
                >
                  {p}
                </button>
              ))}
            </div>
          ))}
        </div>
      )}
      <div
        className="flex-1 overflow-auto rounded-lg bg-zinc-800/50 border border-zinc-700/50 p-4 space-y-3"
        data-testid="chat-messages"
      >
        {msgs.length === 0 && (
          <p className="text-zinc-400 text-center py-8">Ask about browser tasks, bookmarks, or anything.</p>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${m.role === 'user' ? 'bg-amber/20 text-zinc-200' : 'bg-zinc-700/50 text-zinc-300'}`}
            >
              <p className="whitespace-pre-wrap">{m.content}</p>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-zinc-700/50 rounded-lg px-3 py-2 text-zinc-400 text-sm animate-pulse">Thinking...</div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <form onSubmit={submit} className="mt-3 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Message..."
          disabled={loading}
          className="flex-1 px-3 py-2 rounded-lg bg-zinc-800 border border-zinc-600 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-amber disabled:opacity-50"
          data-testid="chat-input"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="px-4 py-2 rounded-lg bg-amber text-zinc-900 font-medium hover:bg-amber/90 disabled:opacity-50"
          data-testid="chat-send"
        >
          Send
        </button>
      </form>
    </div>
  );
}
