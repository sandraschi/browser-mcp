# Development

## Layout

```
src/browser_mcp/
  server.py            # FastMCP instance + automation/system tools
  app.py               # FastAPI app (REST + /mcp mount)
  browser.py           # Playwright singleton lifecycle
  config.py            # env config (single source of truth)
  bookmarks/           # bookmark portmanteau + per-browser backends
  workflows/           # agentic tools (browser_agent, briefing, items, workflow)
webapp/                # React + Vite + Tailwind dashboard
native/                # Tauri 2.0 wrapper (embedded backend)
tests/                 # pytest suite
scripts/               # cua smoke tests, pack scripts, just helpers
```

## Commands

```powershell
uv sync --group dev          # install deps incl. dev group
uv run pytest tests/ -q      # tests
uv run ruff check src/       # lint
uv run ruff format src/      # format
uv run pyright src/          # types
uv run python -m browser_mcp --serve   # HTTP mode
.\start.ps1                  # backend + frontend + browser open
```

Webapp:

```powershell
cd webapp
npm install
npx tsc --noEmit             # typecheck
npm run build                # vite build
npm run dev                  # dev server on 10781
```

## Architecture notes

- The browser is a singleton per process: one page reused across tool calls until
  `close_browser()`.
- Tool modules register themselves by import; `server.py` imports them at module
  level (workflow modules lazy-import `browse_page` to avoid circular imports).
- REST endpoints live in `app.py`; add endpoints there, not in `server.py`.
- Tool docstrings follow the fleet SOTA protocol: `## Return Format` + `## Examples`,
  no `Args:` blocks (parameter docs live in `Annotated[..., Field(description=...)]`).

## Releasing

1. `just gates` equivalent: ruff, format, pyright, pytest, tsc, build.
2. `just build-native` (PyInstaller + Tauri NSIS; bundles `.env.example` only).
3. `just cua-nsis-test` (install -> launch -> nav walk -> uninstall).
4. `just mcpb-pack` (Claude Desktop bundle).
