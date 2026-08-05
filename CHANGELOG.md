
## [Unreleased] — 2026-07-13

### Fixed
- Security: CORS `allow_origin_regex` now unconditional (was gated on `BROWSER_MCP_TAURI`) — covers Tailscale, LAN, CGNAT per `CORS_STANDARD.md`
- Security: Added `allow_credentials=True` to CORS (was missing)
- Version: `pyproject.toml` synced to `0.3.0` (was `0.1.0`), `tauri.conf.json` synced
- `glama.json`: fixed schema (was using old `server_name` format, missing version)

### Added
- `.env.example` with template env vars
- `.cursorrules` for session context injection
- Added missing CORS origins for ports 10780/10781 (backend/frontend)
- `E501` added to ruff ignore (pre-existing bookmarks code style)

## [Unreleased] — 2026-07-05

### Added
- **`browser_agent` tool:** Natural-language browsing via browser-use Agent (local Ollama, configurable LLM_BASE_URL/LLM_MODEL)
- **Packaging docs:** `llms.txt`, `llms-full.txt`, `glama.json` (fleet mandatory)
- **Zoom hook:** Ctrl+Scroll/Ctrl+/Ctrl -/Ctrl 0 zoom with Tauri WebView + dev browser fallback (`webapp/src/hooks/useZoom.ts`)

### Changed
- **CORS:** Explicit Tauri origins (tauri://localhost, http://tauri.localhost, https://tauri.localhost) with BROWSER_MCP_TAURI gating
- **Diagnostics:** `tool_count` now returns live count instead of hardcoded `0`
- **Dashboard poll:** Flat 10s → exponential backoff (1s, 2s, 4s, 8s, 16s, 30s)
- **Dependencies:** Added `browser-use>=0.13.0` for agentic browsing

### Added (data-testid)
- Dashboard KPIs: `kpi-server`, `kpi-port`
- App root: `dashboard`

---

## [Unreleased] — 2026-06-14

### Added
- Tauri 2.0 native wrapper with `bundle.resources` + `std::process::Command`
- PyInstaller frozen backend embedded in NSIS installer
- CUA-NSIS smoke test (`scripts/cua-smoke.py`, `scripts/cua-nsis-config.json`)
- `just cua-nsis-test` recipe
- Tauri CORS: `tauri://localhost` origins for WebView API access
- `GET /api/v1/diagnostics` endpoint for CUA verification
# Changelog

## 0.3.0 (2026-05-23)

- **AI browser workflows**: three new agentic browsing tools
  - `morning_briefing(config)` — configurable daily page routine (HN, GitHub, arXiv, etc.)
  - `browse_items(items_json)` — visit a list of links from aiwatcher-mcp, arxiv-mcp, gitops
  - `browse_workflow(task)` — multi-step agentic browsing from natural language
- **Configurable morning profiles**: `default`, `dev`, `research`, `fleet` in `conf/morning_pages.json`
- **Shared browser lifecycle**: extracted to `browser.py` for reuse across tools and workflows
- **Updated webapp**: workflow-aware dashboard

## 0.2.0 (2026-05-23)

- **Bookmark management**: 17 operations across Chrome, Firefox, Edge, Brave
  - CRUD, search, cross-browser sync, dedup, tags, age analysis, link checking
  - Migrated from `database-operations-mcp` to its proper home
- **Browser detection**: `list_browsers()` — detect installed Chrome, Firefox, Edge, Brave
- **CLI browsing**: `browse_url_cli()` — headless DOM/screenshot via subprocess (no Playwright)
- **Webapp dashboard**: React + Vite on port 10781 with Dashboard + Bookmarks pages
- **Fleet port allocation**: Frontend port 10781 registered in WEBAPP_PORTS.md
- **Fleet registration**: Enabled in MASTER_MCP_CONFIG

## 0.1.0 (2026-04-29)

- Initial scaffold: browse_page, click_element, extract_text, screenshot, fill_input, press_key, close_browser
- Dual transport: stdio (Claude Desktop) + HTTP (port 10780)

