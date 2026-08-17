# browser-mcp — System Prompt / Server Capabilities

## 1. Overview

browser-mcp is a FastMCP 3.4 server that gives an MCP client full control over a local web browser through the Playwright automation library, plus deep cross-browser bookmark management and LLM-driven agentic browsing workflows. The server runs either as a stdio process (for Claude Desktop and other stdio MCP clients) or as a streamable HTTP server (for Cursor, Tauri desktop apps, and IDE integrations) on port 10780 by default.

The server is organized into four capability groups:

1. Browser automation: navigate pages, click elements, extract text, fill forms, press keys, take screenshots.
2. Bookmark management: full CRUD, search, deduplication, tag management, age analysis, broken-link checking, and cross-browser sync across Chrome, Firefox, Edge, and Brave.
3. Agentic workflows: natural-language browsing tasks executed by an LLM-driven agent (browser-use), configurable morning briefing routines, and batch link processing.
4. System: documentation lookup and graceful shutdown.

All tools return structured dictionaries with a `success` boolean and domain-specific fields. Failures return `{"success": false, "error": "<human readable>", "error_type": "<exception class>"}`. Treat the `success` flag as the first thing to check in any tool result.

## 2. Architecture

The server has three layers:

- `src/browser_mcp/server.py`: FastMCP instance and all automation/system tools. This module defines the `mcp` FastMCP object, registers the bookmark portmanteau and workflow modules, and exposes `browse_page`, `click_element`, `extract_text`, `screenshot`, `fill_input`, `press_key`, `close_browser`, `list_browsers`, `browse_url_cli`, `browser_help`, and `browser_shutdown`.
- `src/browser_mcp/bookmarks/`: bookmark management. `portmanteau.py` exposes the single `browser_bookmarks` tool with an `operation` discriminator; `chromium_common.py` handles Chrome/Edge/Brave JSON bookmark files; `firefox/` handles Firefox `places.sqlite` including brute-force read access while Firefox is running; `sync.py` migrates bookmarks between browsers.
- `src/browser_mcp/workflows/`: agentic tools. `browser_use_agent.py` exposes `browser_agent`; `briefing.py` exposes `morning_briefing`; `link_processor.py` exposes `browse_items`; `agentic.py` exposes `browse_workflow`.
- `src/browser_mcp/app.py`: FastAPI application that mounts the MCP HTTP transport at `/mcp` and exposes REST endpoints: `GET /health`, `GET /api/status`, `GET /api/capabilities`, `GET /api/skills`, `GET /api/llm/discover`, `POST /api/llm/chat`, `GET /api/fleet/webapps`, `POST /api/shutdown`, `GET /api/v1/diagnostics`.

The browser lifecycle is managed by `src/browser_mcp/browser.py` with a module-level singleton: the first tool call that needs a page lazily launches Playwright Chromium, and the same page/browser instance is reused across calls until `close_browser()` is called or an unrecoverable error occurs. Because the browser is a singleton, consecutive automation calls operate on the same page — a click followed by a text extraction observes the state left by the click. If the page has been closed or the browser crashed, the next call transparently relaunches.

## 3. Browser Automation Tools

### 3.1 browse_page(url, headless=None)

Navigates to a URL and extracts the visible text content of the page. The URL must be complete (`https://example.com`). The call waits for DOM content to load, then returns the page title, the final URL (after redirects), the HTTP status, and up to the first 20,000 characters of visible body text.

Use this tool as the starting point for almost any web task: research, content extraction, verification of a page state, or as the first step of a multi-step automation sequence. The extracted text is plain visible text — it does not include HTML markup, script content, or hidden elements.

Return format: `{"success": true, "title": str, "url": str, "text": str, "status": int}`.

### 3.2 click_element(selector, headless=None)

Clicks an element on the current page identified by a CSS selector. Examples of valid selectors: `button#submit`, `.nav-link`, `a[href*="login"]`, `input[type="submit"]`. The click waits for the element to be actionable (visible, stable, enabled). After the click, the page may navigate or open a dialog; a subsequent `extract_text` or `browse_page` call reflects the new state.

If the element does not exist or is not visible, the tool returns a failure with a descriptive error. When automating unknown pages, prefer `extract_text` first to learn the page structure, then click with a selector copied from the observed content or a common-sense selector.

Return format: `{"success": true, "clicked": str, "url": str}`.

### 3.3 extract_text(selector="body", headless=None)

Extracts the inner text of the first element matching the CSS selector. The default selector `body` returns the entire visible text of the page. Useful for reading the content of a specific container after navigation, for example `extract_text(selector="article.main")` or `extract_text(selector="#results")`. The result is capped at 20,000 characters.

Return format: `{"success": true, "text": str, "url": str, "selector": str}`.

### 3.4 screenshot(headless=None)

Captures a PNG screenshot of the current viewport and returns it base64-encoded. The returned string can be decoded to bytes and written to a `.png` file, or passed to a vision-capable model for visual inspection. Screenshots capture what is visible in the viewport only; use `browse_page` text extraction for content that requires scrolling.

Return format: `{"success": true, "screenshot_b64": str, "url": str, "format": "png"}`.

### 3.5 fill_input(selector, text, headless=None)

Fills an input field with text, clearing any existing value first. The selector must identify an editable element (`input`, `textarea`, `[contenteditable]`). This is the reliable way to enter text into forms; typing character by character is unnecessary.

Return format: `{"success": true, "selector": str}`.

### 3.6 press_key(key, headless=None)

Presses a single keyboard key on the focused element/page. Valid key names are Playwright key names: `Enter`, `Escape`, `Tab`, `ArrowDown`, `ArrowUp`, `ArrowLeft`, `ArrowRight`, `Home`, `End`, `PageDown`, `PageUp`, `Backspace`, `Delete`, `F5`, and letter/digit characters. Useful after `fill_input` to submit a form (`Enter`) or to navigate results (`ArrowDown`, `Enter`).

Return format: `{"success": true, "key": str}`.

### 3.7 close_browser()

Closes the browser and releases all Playwright resources. Call this at the end of a browsing session or when you no longer need the page, to free memory and file handles. Subsequent automation calls will relaunch the browser automatically.

Return format: `{"success": true, "message": "Browser closed"}`.

### 3.8 list_browsers()

Detects installed browsers and Firefox profiles by scanning common installation paths on Windows. Reports Chrome, Firefox, Edge, and Brave with their executable paths, and lists Firefox profile names parsed from `profiles.ini`. Call this before bookmark operations to learn which browsers are available, and before automation if you plan to use a specific browser profile.

Return format: `{"success": true, "browsers": {"<name>": {"installed": bool, "path": str, "profiles": [str]}}}`.

### 3.9 browse_url_cli(url, browser="chrome")

Quick headless navigation without starting a full Playwright session. For Chrome it runs `chrome --headless --dump-dom` and returns the DOM text; for Firefox it runs `firefox --headless --screenshot` and returns the path of the captured PNG. This is the low-overhead path for simple "what does this page contain" checks.

Return format: `{"success": true, "browser": str, "url": str, "text" | "screenshot": str}`.

## 4. Bookmark Management (browser_bookmarks)

The `browser_bookmarks` tool is a portmanteau: the first argument `operation` selects the sub-operation, and `browser` selects the target browser (`chrome`, `firefox`, `edge`, `brave`). Supported operations:

- `list_bookmarks`: list bookmarks, optionally filtered by folder.
- `get_bookmark`: fetch a single bookmark by id.
- `add_bookmark`: add a bookmark (requires `url`, optional `title`, `folder`, `tags`).
- `edit_bookmark`: change title, folder, or URL of an existing bookmark.
- `delete_bookmark`: remove a bookmark.
- `search` / `search_bookmarks`: full-text search over title and URL.
- `sync_bookmarks`: copy bookmarks from one browser to another (requires `target_browser`; `dry_run=true` previews).
- `find_duplicates`: detect duplicate URLs within a browser.
- `export_bookmarks`: export to JSON or CSV (`export_format`, `export_path`).
- `list_tags`: list existing bookmark tags.
- `find_old_bookmarks`: bookmarks untouched for `age_days` (default 365).
- `find_forgotten_bookmarks`: bookmarks never revisited.
- `get_bookmark_stats`: aggregate counts.
- `find_broken_links`: verify URLs still resolve (Firefox).
- `tag` management ops: `find_similar_tags`, `merge_tags`, `cleanup_tags` (Firefox).

Bookmark storage differs by browser:

- Chrome/Edge/Brave store bookmarks in a JSON file (`Bookmarks`) inside the user profile; the server reads and writes it directly.
- Firefox stores bookmarks in SQLite (`places.sqlite`). While Firefox is running, the database file is locked; the server attempts read-only URI tricks first, and if those fail, copies the database to a temporary file and reads the copy (brute-force access). Writes to Firefox generally require Firefox to be closed.

Return format (list): `{"success": true, "browser": str, "operation": str, "bookmarks": [...]}`. Most sub-operations return a domain-specific payload plus `success`.

## 5. Agentic Workflows

### 5.1 browser_agent(task, headless=True, max_steps=20)

Executes a natural-language browsing task with the browser-use agent. The agent autonomously navigates, clicks, fills forms, and extracts information based on the task description. It requires a configured LLM: by default it uses Ollama at `http://127.0.0.1:11434` with model `LLM_MODEL` (default `gemma4:12b`), overridable via `LLM_BASE_URL` and `LLM_MODEL` environment variables. If `browser-use` is not installed, the tool returns a failure with installation instructions.

Use for tasks with an unambiguous goal: "Find the price of the RTX 5090 on Amazon", "Log in and check for unread emails from Sandra". For simple deterministic tasks, prefer the direct automation tools; for open-ended research or multi-page workflows, `browser_agent` is the right tool.

Return format: `{"success": true, "result": str | null, "steps": int, "urls": [str]}`.

### 5.2 morning_briefing(config_name="default", headless=True, max_pages=5)

Runs a configurable daily browsing routine defined in `conf/morning_pages.json`. Built-in profiles: `default` (Hacker News + GitHub), `dev` (HN + Python + Lobsters), `research` (arXiv + Reddit ML), `fleet` (repo activity). Each profile lists pages to visit; the tool extracts a text preview from each and returns a structured briefing with per-page summaries. Custom profiles can be added to the config file.

Return format: `{"success": true, "profile": str, "label": str, "briefing_date": str, "pages_visited": int, "pages": [...], "errors": [...], "suggestions": {...}}`.

### 5.3 browse_items(items_json, task="Summarize...", headless=True, max_items=10)

Batch-browses a list of links and returns structured summaries. `items_json` is a JSON array of `{"title": ..., "url": ...}` objects (also accepts `{"name": ...}`). Designed to chain with other fleet servers: feed `aiwatcher-mcp get_top_items` output, `arxiv-mcp search_papers` results, or issue lists from git tooling, and get back per-item text previews plus an aggregate summary.

Return format: `{"success": true, "items_processed": int, "items_total": int, "errors": [...], "results": [...], "summary": str, "task": str, "next_steps": [str]}`.

### 5.4 browse_workflow(task, initial_url="", headless=True, max_steps=8)

Executes a multi-step agentic browsing task with a step log: each step navigates or extracts, and the tool returns a chronological record of pages visited and content extracted. `initial_url` seeds the starting point; empty starts at about:blank. The workflow executes up to `max_steps` iterations. Unlike `browser_agent`, this tool drives the server's own automation tools directly and does not require an LLM configuration.

Return format: `{"success": bool, "task": str, "initial_url": str, "steps_taken": int, "steps": [{step, url, title, text_preview}], "errors": [str], "summary": str}`.

## 6. System Tools

### 6.1 browser_help(topic="overview")

Returns documentation for the server. Topics: `overview`, `automation`, `bookmarks`, `workflows`, `configuration`. Use this tool when you need a quick reference of available capabilities or exact tool signatures.

### 6.2 browser_shutdown(confirm=False)

Gracefully shuts down the server process. Requires `confirm=True`; without it the tool returns a failure message. In HTTP mode the process exits after a short delay. Use at the end of a session when the server should be stopped (for example in tests or after batch jobs).

## 7. Configuration

All configuration is read from environment variables at startup:

| Variable | Default | Purpose |
|----------|---------|---------|
| `BROWSER_MCP_PORT` | `10780` | HTTP/MCP port |
| `BROWSER_MCP_HOST` | `127.0.0.1` | Bind host |
| `BROWSER_MCP_HTTP_PATH` | `/mcp` | MCP streamable HTTP path |
| `BROWSER_HEADLESS` | `true` | Default headless mode for automation tools |
| `BROWSER_MCP_FRONTEND_PORT` | `10781` | Vite dev port (webapp) |
| `LLM_BASE_URL` | `http://127.0.0.1:11434` | OpenAI-compatible base for browser-use agent and chat |
| `LLM_MODEL` | `gemma4:12b` | Default model for browser-use agent |
| `MCP_BRIDGE_URLS` | (empty) | Comma-separated upstream MCP server URLs to proxy |
| `MCP_TRANSPORT` | (empty) | Set `http` to force HTTP mode in `python -m browser_mcp` |

HTTP mode requires `uv run python -m browser_mcp --serve` or `MCP_TRANSPORT=http`; stdio is the default. The PyInstaller entry point `run_server.py` always starts HTTP mode using `BROWSER_MCP_PORT`/`PORT`.

## 8. Safety and Error Handling

- All tools catch their own exceptions and return structured failure dictionaries; they never raise to the MCP client. Check `success` before trusting results.
- Browser automation launches a real Chromium process. Operations are confined to pages you navigate to; there is no arbitrary code execution surface beyond the page's own scripts.
- Bookmark writes modify the user's real browser profile. Prefer `dry_run=true` for sync operations and verify the target browser state before bulk destructive operations.
- `browser_shutdown` is the only destructive system operation and requires explicit confirmation.
- The server is local-only by default: it binds to 127.0.0.1 and exposes no authentication. Do not expose the HTTP port to untrusted networks.

## 9. Multi-Step Workflow Guidance

The browser singleton means a typical automation session is a sequence of calls:

1. `list_browsers()` to confirm availability (optional).
2. `browse_page(url)` to load the page.
3. `extract_text()` to read the page and decide the next action.
4. `click_element(selector)` / `fill_input(selector, text)` / `press_key(key)` to interact.
5. `extract_text()` or `screenshot()` to verify the result.
6. `close_browser()` when the session is done.

For bookmark maintenance: `browser_bookmarks(operation="list_bookmarks", browser=...)` to inventory, then targeted operations. For research: `browse_items` to batch-process links, or `browse_workflow`/`browser_agent` for open-ended tasks.

## 10. Tool Parameter Reference

### 10.1 browse_page

| Parameter | Type | Default | Meaning |
|-----------|------|---------|---------|
| `url` | str (required) | - | Full URL including scheme, e.g. `https://example.com` |
| `headless` | bool | config `BROWSER_HEADLESS` | `false` opens a visible window |

### 10.2 click_element

| Parameter | Type | Default | Meaning |
|-----------|------|---------|---------|
| `selector` | str (required) | - | CSS selector of the click target |
| `headless` | bool | config | `false` opens a visible window |

### 10.3 extract_text

| Parameter | Type | Default | Meaning |
|-----------|------|---------|---------|
| `selector` | str | `body` | CSS selector of the container to read |
| `headless` | bool | config | `false` opens a visible window |

### 10.4 screenshot

| Parameter | Type | Default | Meaning |
|-----------|------|---------|---------|
| `headless` | bool | config | `false` opens a visible window |

### 10.5 fill_input

| Parameter | Type | Default | Meaning |
|-----------|------|---------|---------|
| `selector` | str (required) | - | CSS selector of the editable element |
| `text` | str (required) | - | Text to enter (field is cleared first) |
| `headless` | bool | config | `false` opens a visible window |

### 10.6 press_key

| Parameter | Type | Default | Meaning |
|-----------|------|---------|---------|
| `key` | str (required) | - | Playwright key name: `Enter`, `Tab`, `ArrowDown`, `F5`, ... |
| `headless` | bool | config | `false` opens a visible window |

### 10.7 browser_bookmarks (portmanteau)

Key parameters by operation:

| Parameter | Applies to | Meaning |
|-----------|-----------|---------|
| `operation` | all | Sub-operation selector (see Section 4) |
| `browser` | all | `chrome` \| `firefox` \| `edge` \| `brave` |
| `profile_name` | firefox | Firefox profile to target |
| `folder_id` / `folder` | list/add/edit | Folder scoping |
| `bookmark_id` | get/edit/delete | Target bookmark id from a prior list/search |
| `url`, `title`, `tags` | add/edit/search | Content fields |
| `search_query`, `search_type` | search | Text search with `all`/`title`/`url` modes |
| `target_browser` | sync | Destination browser for migration |
| `dry_run` | sync | Preview only |
| `limit` | list/search | Result cap (max 10,000) |
| `export_format`, `export_path` | export | `json` or `csv` output |
| `age_days` | find_old_bookmarks | Age threshold |
| `check_links` | find_broken_links | Enable network verification |
| `similarity_threshold` | find_duplicates | Duplicate match threshold |
| `force_access` | firefox reads | Brute-force copy of locked DB |

### 10.8 Agentic tools

| Tool | Required | Optional |
|------|----------|----------|
| `browser_agent` | `task` | `headless`, `max_steps` (1-50) |
| `morning_briefing` | - | `config_name`, `headless`, `max_pages` |
| `browse_items` | `items_json` | `task`, `headless`, `max_items` |
| `browse_workflow` | `task` | `initial_url`, `headless`, `max_steps` |

### 10.9 System tools

| Tool | Required | Optional |
|------|----------|----------|
| `browser_help` | - | `topic` (overview/automation/bookmarks/workflows/configuration) |
| `browser_shutdown` | - | `confirm` (must be true to act) |

## 11. Agent Best Practices and Recovery

- **Verify before trusting**: every tool returns `success`; a `false` result carries `error` and `error_type`. When a step fails, read the error and adapt — do not blindly retry the same call.
- **Sequence automation**: browser state is shared. A click changes the page; extract after each interaction to keep your model of the page current. When you lose track of the page state, `browse_page` to a known URL resets the session cleanly.
- **Selector strategy**: prefer stable attributes (`id`, `data-testid`, `name`) over fragile positional selectors. When a selector fails, extract the page text and search for a nearby stable anchor (button text, link text, input name).
- **Bounded work**: use `max_steps`, `max_items`, and `limit` to keep tasks bounded. Batch operations should be chunked.
- **Shutdown hygiene**: call `browser_shutdown(confirm=true)` only when the session is genuinely finished; for normal automation, `close_browser()` is the polite resource release.
- **Recovery from transient failures**: network timeouts and page-load races are common. A single retry after a short pause usually succeeds. Persistent failures on the same URL usually mean the site blocks automation or the URL is wrong.

## 12. MCP Client Integration Notes

- **stdio clients** (Claude Desktop): run `uv run browser-mcp`; the server speaks MCP over stdin/stdout with no configuration.
- **HTTP clients** (Cursor, IDE extensions): register a streamable HTTP MCP server at `http://127.0.0.1:10780/mcp`. The server must be started in HTTP mode first.
- **Desktop app** (Tauri/NSIS): the native wrapper spawns the embedded backend automatically on 10780; no manual start needed. The webapp in the wrapper shows live backend status.
- **Tool discovery**: the client lists 16 tools. The `browser_bookmarks` portmanteau exposes its operations in the docstring; discover them via `browser_help(topic="bookmarks")` or the tool description.
- **State sharing**: multiple stdio clients each get their own browser singleton (per-process state). An HTTP server shares one browser across all connected clients — coordinate long automation sessions to avoid interfering page state.

## 13. Version and Compatibility

- FastMCP >= 3.4.4, < 4. Pydantic v2 models; tools return dicts.
- Python >= 3.12.
- Windows-first (bookmark paths, CLI tools), but the Playwright layer is cross-platform.
- The MCP HTTP transport is streamable HTTP (2025-11-25 protocol version). SSE is not provided; clients that need SSE should use the stdio bridge.

## 14. Data Model Notes

- Browser automation state is a singleton page: `title`, `url`, and DOM state persist between calls until navigation or `close_browser()`.
- Bookmark results always carry `browser` and `operation` echo fields for unambiguous interpretation in chained calls.
- Screenshots are base64 PNG; decode to bytes before writing to disk. Never treat the base64 string as text content.
- All timestamps in tool results are ISO 8601 local time unless stated otherwise.
- `browser_bookmarks` caps `limit` at 10,000 results; large libraries require pagination via `folder_id` scoping or search filters.


