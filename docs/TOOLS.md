# Tools

16 MCP tools, grouped by domain. All return structured dicts with `success`.

## Browser automation

| Tool | Purpose |
|------|---------|
| `browse_page(url, headless?)` | Navigate and extract visible text (20K cap) |
| `click_element(selector, headless?)` | Click by CSS selector |
| `extract_text(selector="body", headless?)` | Inner text of an element |
| `screenshot(headless?)` | Viewport PNG as base64 |
| `fill_input(selector, text, headless?)` | Type into an input (clears first) |
| `press_key(key, headless?)` | Keyboard key (Enter, Tab, ArrowDown, ...) |
| `close_browser()` | Release the Playwright singleton |
| `list_browsers()` | Detect Chrome/Firefox/Edge/Brave + Firefox profiles |
| `browse_url_cli(url, browser="chrome")` | Headless CLI read (no Playwright) |

## Bookmarks (portmanteau)

`browser_bookmarks(operation, browser, ...)` across chrome/firefox/edge/brave:

- CRUD: `list_bookmarks`, `get_bookmark`, `add_bookmark`, `edit_bookmark`, `delete_bookmark`
- Search: `search_bookmarks` / `search` (title/url, `search_type`)
- Sync: `sync_bookmarks` (requires `target_browser`, supports `dry_run`)
- Hygiene: `find_duplicates`, `find_old_bookmarks`, `find_forgotten_bookmarks`,
  `get_bookmark_stats`, `find_broken_links` (Firefox)
- Tags (Firefox): `list_tags`, `find_similar_tags`, `merge_tags`, `cleanup_tags`
- Export: `export_bookmarks` (json/csv)

## Agentic workflows

| Tool | Purpose |
|------|---------|
| `browser_agent(task, headless?, max_steps?)` | LLM-driven browsing via browser-use (needs Ollama) |
| `morning_briefing(config_name="default", ...)` | Daily routine from `conf/morning_pages.json` |
| `browse_items(items_json, task?, max_items?)` | Batch link processing (JSON array in, previews out) |
| `browse_workflow(task, initial_url?, max_steps?)` | Logged multi-step browsing, no LLM needed |

## System

| Tool | Purpose |
|------|---------|
| `browser_help(topic="overview")` | Documentation lookup |
| `browser_shutdown(confirm=false)` | Graceful shutdown (needs `confirm=true`) |

## REST endpoints (HTTP mode)

`GET /health`, `GET /api/status`, `GET /api/capabilities`, `GET /api/skills`,
`GET /api/llm/discover`, `POST /api/llm/chat`, `GET /api/fleet/webapps`,
`POST /api/shutdown`, `GET /api/v1/diagnostics`; Swagger at `/docs`.
