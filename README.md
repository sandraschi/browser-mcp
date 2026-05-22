# browser-mcp

<p align="center">
  <a href="https://github.com/sandraschi/browser-mcp"><img src="https://img.shields.io/github/stars/sandraschi/browser-mcp?style=flat-square" alt="Stars"></a>
  <a href="https://github.com/sandraschi/browser-mcp/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.2-7c5cfc?style=flat-square" alt="FastMCP"></a>
  <a href="https://playwright.dev/"><img src="https://img.shields.io/badge/Playwright-powered-45ba4b?style=flat-square" alt="Playwright"></a>
</p>

**Browser automation + bookmark management — over MCP.** A unified MCP server for controlling Chrome, Firefox, Edge, and Brave: browse pages, click elements, take screenshots, and manage bookmarks across all major browsers. Ships with a React webapp dashboard.

---

## Features

### Browser Automation (Playwright + CDP + CLI)

| Tool | Description |
|------|-------------|
| `browse_page(url)` | Navigate and extract visible text |
| `click_element(selector)` | Click elements by CSS selector |
| `extract_text(selector)` | Extract text from any element |
| `fill_input(selector, text)` | Type into input fields |
| `press_key(key)` | Press keyboard keys |
| `screenshot()` | Viewport PNG screenshot |
| `browse_url_cli(url, browser)` | Headless CLI mode (no Playwright overhead) |
| `list_browsers()` | Detect installed browsers and profiles |

### Bookmark Management (4 Browsers)

17 operations across Chrome, Firefox, Edge, and Brave:

- **CRUD**: list, get, add, edit, delete bookmarks
- **Search**: full-text search by title/URL
- **Cross-browser sync**: migrate bookmarks between any two browsers
- **Deduplication**: find duplicate URLs (Firefox)
- **Tag management**: list, find similar, merge, clean up tags (Firefox)
- **Age analysis**: find old or forgotten bookmarks, get stats (Firefox)
- **Link checking**: detect broken links (Firefox)
- **Export**: bookmarks to JSON/CSV (Firefox)

Bookmarks are read/written directly to the browser's native storage:
- **Firefox**: SQLite (`places.sqlite`) with brute-force unlock for read-while-running
- **Chrome/Edge/Brave**: Chromium `Bookmarks` JSON file

### Webapp Dashboard (React + Vite)

A full React SPA on port `10781` with:
- **Dashboard**: health status, installed browser detection
- **Bookmarks panel**: list bookmarks by browser with live search

---

## Quick Start

```powershell
git clone https://github.com/sandraschi/browser-mcp
cd browser-mcp
just
```

Opens an interactive recipe dashboard. Otherwise:

```powershell
# Install dependencies
uv sync

# Install Playwright browsers
playwright install chromium

# Start backend (port 10780)
uv run browser-mcp --serve

# Start frontend (port 10781) — separate terminal
cd webapp && npm install && npm run dev
```

For more details: [INSTALL.md](INSTALL.md)

---

## Tools Reference

### Browser Automation

```python
# Navigate and extract
await browse_page("https://example.com")
# → {"title": "...", "text": "...", "url": "...", "status": 200}

# Click and interact
await click_element("button#submit")
await fill_input("#search", "hello world")
await press_key("Enter")

# Screenshot
await screenshot()
# → {"screenshot_b64": "iVBORw0KGgo..."}

# CLI mode (no Playwright session needed)
await browse_url_cli("https://example.com", browser="chrome")

# Detect installed browsers
await list_browsers()
# → {"browsers": {"chrome": {"installed": true, "path": "..."}, ...}}
```

### Bookmark Management

```python
# List bookmarks from Chrome
await browser_bookmarks(operation="list_bookmarks", browser="chrome")

# List from Firefox
await browser_bookmarks(operation="list_bookmarks", browser="firefox")

# Add a bookmark
await browser_bookmarks(
    operation="add_bookmark",
    browser="chrome",
    url="https://example.com",
    title="Example",
)

# Search
await browser_bookmarks(operation="search", browser="firefox", search_query="python")

# Find duplicates (Firefox only)
await browser_bookmarks(operation="find_duplicates", browser="firefox")

# Sync bookmarks from Firefox to Chrome
await browser_bookmarks(
    operation="sync_bookmarks",
    browser="firefox",
    target_browser="chrome",
)

# Export Firefox bookmarks
await browser_bookmarks(operation="export_bookmarks", browser="firefox", export_format="json")

# Find forgotten bookmarks (not visited in 1 year)
await browser_bookmarks(
    operation="find_forgotten_bookmarks",
    browser="firefox",
    age_days=365,
)
```

### Full Operation List

| Operation | Chrome | Firefox | Edge | Brave |
|-----------|:------:|:-------:|:----:|:-----:|
| list_bookmarks | ✓ | ✓ | ✓ | ✓ |
| get_bookmark | ✓ | ✓ | ✓ | ✓ |
| add_bookmark | ✓ | ✓ | ✓ | ✓ |
| edit_bookmark | ✓ | ✓ | ✓ | ✓ |
| delete_bookmark | ✓ | ✓ | ✓ | ✓ |
| search / search_bookmarks | ✓ | ✓ | ✓ | ✓ |
| sync_bookmarks | ✓ | ✓ | ✓ | ✓ |
| find_duplicates | — | ✓ | — | — |
| export_bookmarks | — | ✓ | — | — |
| list_tags | — | ✓ | — | — |
| find_similar_tags | — | ✓ | — | — |
| merge_tags | — | ✓ | — | — |
| clean_up_tags | — | ✓ | — | — |
| find_old_bookmarks | — | ✓ | — | — |
| find_forgotten_bookmarks | — | ✓ | — | — |
| get_bookmark_stats | — | ✓ | — | — |
| find_broken_links | — | ✓ | — | — |
| refresh_bookmarks | — | ✓ | — | — |

---

## Architecture

### Browser Control Layers

| Layer | Chrome/Chromium | Firefox |
|-------|----------------|---------|
| **Bookmark read/write** | Direct JSON file | Direct SQLite |
| **Headless automation** | Playwright (primary) + CDP WebSocket | Playwright (primary) + geckodriver |
| **CLI quick ops** | `chrome --headless --dump-dom` | `firefox --headless --screenshot` |

### Ports

| Port | Service |
|------|---------|
| 10780 | Backend (FastAPI + MCP HTTP) |
| 10781 | Frontend (Vite React dev server) |

### Project Structure

```
browser-mcp/
├── src/browser_mcp/
│   ├── server.py              # MCP tools + browser lifecycle
│   ├── app.py                 # FastAPI app with /health + MCP mount
│   ├── config.py              # Environment-based settings
│   ├── __main__.py            # CLI entry point (stdio / HTTP)
│   └── bookmarks/             # Bookmark management backend
│       ├── portmanteau.py     # Main browser_bookmarks MCP tool
│       ├── firefox_bookmarks.py    # Firefox SQLite backend
│       ├── chromium_common.py      # Chrome/Edge/Brave JSON backend
│       ├── sync.py            # Cross-browser sync
│       └── firefox/           # 13 submodules (db, status, utils, etc.)
├── webapp/                    # React + Vite dashboard (port 10781)
│   ├── src/
│   │   ├── pages/Dashboard.tsx
│   │   └── pages/Bookmarks.tsx
│   └── package.json
└── justfile
```

---

## Config

| Env Var | Default | Description |
|---------|---------|-------------|
| `BROWSER_MCP_HOST` | 127.0.0.1 | HTTP bind address |
| `BROWSER_MCP_PORT` | 10780 | HTTP backend port |
| `BROWSER_MCP_FRONTEND_PORT` | 10781 | Vite frontend port |
| `BROWSER_HEADLESS` | true | Run Playwright headless |
| `MCP_TRANSPORT` | — | Set to `http` for HTTP mode |

---

## Running

```powershell
# stdio mode (Claude Desktop, MCP clients)
uv run browser-mcp --stdio

# HTTP mode (web dashboard + API)
uv run browser-mcp --serve

# Debug mode
uv run browser-mcp --serve --debug
```

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

---

## License

MIT
