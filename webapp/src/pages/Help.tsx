export default function Help() {
  return (
    <div data-testid="help-page" className="space-y-6 max-w-3xl">
      <h1 className="text-2xl font-bold text-zinc-100">Help</h1>

      <section className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-4">
        <h2 className="text-sm font-semibold text-amber mb-2">About</h2>
        <p className="text-sm text-zinc-300">
          Browser MCP is a FastMCP 3.4 server for Playwright browser automation: browse pages, click elements, fill
          forms, take screenshots, and manage bookmarks across Chrome, Firefox, Edge, and Brave.
        </p>
      </section>

      <section className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-4">
        <h2 className="text-sm font-semibold text-amber mb-2">Pages</h2>
        <div className="text-sm text-zinc-300 space-y-1.5">
          <p>
            <strong className="text-zinc-100">Dashboard</strong> - Server health, tool count, connection status.
          </p>
          <p>
            <strong className="text-zinc-100">Bookmarks</strong> - Manage Chrome/Firefox/Edge/Brave bookmarks (CRUD,
            search, sync, dedupe).
          </p>
          <p>
            <strong className="text-zinc-100">Tools</strong> - All MCP tools registered by the server, with portmanteau
            drill-down.
          </p>
          <p>
            <strong className="text-zinc-100">Chat</strong> - LLM-assisted browser automation queries (requires Ollama
            or LM Studio).
          </p>
          <p>
            <strong className="text-zinc-100">Apps</strong> - Fleet webapp discovery.
          </p>
          <p>
            <strong className="text-zinc-100">Settings</strong> - Backend status and local LLM provider/model selection.
          </p>
          <p>
            <strong className="text-zinc-100">API Docs</strong> - Swagger UI and ReDoc for the REST surface.
          </p>
        </div>
      </section>

      <section className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-4">
        <h2 className="text-sm font-semibold text-amber mb-2">Architecture & Ports</h2>
        <div className="text-sm text-zinc-300 space-y-1.5">
          <p>
            <strong className="text-zinc-100">Backend</strong> - FastAPI + FastMCP HTTP on{' '}
            <code className="text-amber">127.0.0.1:10780</code>. REST at <code className="text-amber">/api/*</code>, MCP
            streamable HTTP at <code className="text-amber">/mcp</code>.
          </p>
          <p>
            <strong className="text-zinc-100">Frontend</strong> - Vite React SPA on{' '}
            <code className="text-amber">127.0.0.1:10781</code>, proxying <code className="text-amber">/api</code> and{' '}
            <code className="text-amber">/mcp</code> to the backend.
          </p>
          <p>
            <strong className="text-zinc-100">MCP clients</strong> - Connect Cursor/Claude Desktop to{' '}
            <code className="text-amber">http://127.0.0.1:10780/mcp</code> (streamable HTTP) or run stdio via{' '}
            <code className="text-amber">uv run browser-mcp</code>.
          </p>
        </div>
      </section>

      <section className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-4">
        <h2 className="text-sm font-semibold text-amber mb-2">Configuration</h2>
        <div className="text-sm text-zinc-300 space-y-1.5">
          <p>
            <code className="text-amber">BROWSER_MCP_PORT</code> - HTTP port (default 10780).
          </p>
          <p>
            <code className="text-amber">BROWSER_MCP_HOST</code> - Bind host (default 127.0.0.1).
          </p>
          <p>
            <code className="text-amber">HEADLESS</code> - Browser headless mode (default true).
          </p>
          <p>
            <code className="text-amber">LLM_BASE_URL</code> / <code className="text-amber">LLM_MODEL</code> - LLM
            endpoint for browser-use agent and chat (default Ollama at{' '}
            <code className="text-amber">http://127.0.0.1:11434</code>).
          </p>
          <p>
            <code className="text-amber">MCP_BRIDGE_URLS</code> - Comma-separated upstream MCP servers to proxy.
          </p>
        </div>
      </section>

      <section className="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-4">
        <h2 className="text-sm font-semibold text-amber mb-2">Troubleshooting</h2>
        <div className="text-sm text-zinc-300 space-y-1.5">
          <p>
            <strong className="text-zinc-100">Dashboard shows Offline</strong> - Start the backend:{' '}
            <code className="text-amber">.\start.ps1</code> or{' '}
            <code className="text-amber">uv run python -m browser_mcp --serve</code>.
          </p>
          <p>
            <strong className="text-zinc-100">Bookmarks read-only / locked</strong> - Firefox bookmarks are read from{' '}
            <code className="text-amber">places.sqlite</code>; close Firefox or pass{' '}
            <code className="text-amber">force_access=True</code>.
          </p>
          <p>
            <strong className="text-zinc-100">Chat errors</strong> - Ensure Ollama (or LM Studio) is running; check the
            provider status in Settings.
          </p>
          <p>
            <strong className="text-zinc-100">Tauri app backend not starting</strong> - Check{' '}
            <code className="text-amber">%LOCALAPPDATA%\com.sandraschi.browser-mcp\logs\backend-spawn.log</code>.
          </p>
        </div>
      </section>
    </div>
  );
}
