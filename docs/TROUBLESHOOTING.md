# Troubleshooting

## Backend does not start

- `uv sync` first; missing deps surface as import errors.
- Port 10780 busy: `start.ps1` clears zombies; manually:
  `Get-NetTCPConnection -LocalPort 10780 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }`.
- `uv run python -m browser_mcp --serve` prints the bind error if any.

## Pages do not load

- `playwright install chromium` — the Playwright-managed Chromium is separate from installed Chrome.
- Some sites block headless: pass `headless=false`.
- URL must include the scheme (`https://...`).

## Bookmarks: Firefox "database is locked"

Firefox locks `places.sqlite` while running. Reads fall back to a temp copy
(brute-force); writes need Firefox closed. `force_access=true` forces the copy path.

## Bookmarks: Chrome/Edge/Brave empty

The server reads the profile `Bookmarks` JSON file. Confirm the browser created a
profile at the default path and was closed cleanly (corrupt JSON is reported as a
parse error in the tool result).

## browser_agent errors

- Verify the LLM: `Invoke-WebRequest http://127.0.0.1:11434/api/tags`.
- `LLM_BASE_URL` / `LLM_MODEL` must be set before the server starts.
- If the error mentions browser-use, run `uv sync` (browser-use is a core dep).

## Chat page errors in the webapp

Check Settings -> Local LLM: provider status and model. The chat proxies to
`POST /api/llm/chat` (Ollama at 11434 by default). Start Ollama if not detected.

## Tauri app shows "Offline" on the dashboard

The packaged app spawns the backend on 10780 and the frontend polls
`http://127.0.0.1:10780/health`. Check the spawn log:
`%LOCALAPPDATA%\com.sandraschi.browser-mcp\logs\backend-spawn.log`. If the backend
exe is missing from resources, rebuild with `just build-native`.

## Hung browser / server

- `close_browser()` relaunches cleanly on the next call.
- Full reset: restart the server. HTTP mode: `POST /api/shutdown` or Ctrl+C.

## CUA smoke test fails

- `scripts/cua-nsis-config.json` must match reality: `health_path` is `/health`
  (not `/api/v1/health`), backend process names are `browser-mcp-native` /
  `browser-mcp-backend`, port `10780`.
- The nav walk needs the sidebar labels to match `nav_routes` exactly
  (Dashboard, Bookmarks, Tools, Chat, Apps, Skills, Settings, Help, API Docs).
