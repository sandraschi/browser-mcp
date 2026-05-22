import { useState } from 'react';

export default function Bookmarks() {
  const [browser, setBrowser] = useState('chrome');
  const [bookmarks, setBookmarks] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchBookmarks = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/health', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jsonrpc: '2.0',
          id: 1,
          method: 'tools/call',
          params: {
            name: 'browser_bookmarks',
            arguments: { operation: 'list_bookmarks', browser },
          },
        }),
      });
      const data = await res.json();
      if (data?.result?.content?.[0]?.text) {
        const parsed = JSON.parse(data.result.content[0].text);
        setBookmarks(parsed.bookmarks || parsed.results || []);
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Bookmarks</h2>

      <div className="flex gap-3 items-center mb-4">
        <select
          value={browser}
          onChange={e => setBrowser(e.target.value)}
          className="bg-gray-700 text-white px-3 py-2 rounded"
        >
          <option value="chrome">Chrome</option>
          <option value="firefox">Firefox</option>
          <option value="edge">Edge</option>
          <option value="brave">Brave</option>
        </select>
        <button
          onClick={fetchBookmarks}
          disabled={loading}
          className="bg-indigo-600 hover:bg-indigo-700 px-4 py-2 rounded disabled:opacity-50"
        >
          {loading ? 'Loading...' : 'List Bookmarks'}
        </button>
      </div>

      {error && <div className="bg-red-900 p-3 rounded mb-4">{error}</div>}

      {bookmarks && bookmarks.length === 0 && (
        <p className="text-gray-400">No bookmarks found.</p>
      )}

      {bookmarks && bookmarks.length > 0 && (
        <div className="space-y-2">
          {bookmarks.slice(0, 50).map((bm, i) => (
            <div key={i} className="bg-gray-800 p-3 rounded">
              <a href={bm.url} target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:underline font-medium">
                {bm.title || bm.name || bm.url}
              </a>
              <p className="text-xs text-gray-500 truncate mt-0.5">{bm.url}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
