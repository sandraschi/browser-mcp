export default function HelpModal({ onClose }: { onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/70" onClick={onClose}>
      <div className="border border-zinc-600 rounded-lg shadow-xl max-w-lg w-full bg-zinc-900" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between p-4 border-b border-zinc-600">
          <h2 className="text-lg font-semibold text-amber">Help</h2>
          <button type="button" onClick={onClose} className="text-zinc-400 hover:text-white">Close</button>
        </div>
        <div className="p-4 text-sm text-zinc-300 space-y-3">
          <p><strong className="text-amber">Dashboard</strong> — Server health, tool count, and connection status.</p>
          <p><strong className="text-amber">Bookmarks</strong> — Manage Chrome/Firefox/Edge/Brave bookmarks.</p>
          <p><strong className="text-amber">Tools</strong> — All MCP tools registered by the server.</p>
          <p><strong className="text-amber">Chat</strong> — LLM-assisted browser automation queries (requires Ollama).</p>
          <p>Set <code className="text-amber text-xs">LLM_BASE_URL</code> in the backend env for custom LLM endpoints.</p>
        </div>
      </div>
    </div>
  );
}
