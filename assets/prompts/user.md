# browser-mcp — User Tutorials

This guide teaches you, the human operator, how to get real work done with browser-mcp. The server controls a local web browser through Playwright, manages bookmarks across Chrome, Firefox, Edge, and Brave, and can run autonomous browsing workflows with an LLM. Every section below is a self-contained tutorial you can follow with any MCP client connected to the server.

## Section 1: Setup and First Launch

### 1.1 What you need

- Python 3.12 or newer, with `uv` installed.
- A browser on your machine: Chrome, Firefox, Edge, or Brave (at least one; automation uses Chromium via Playwright).
- For AI-powered features (the `browser_agent` tool and the webapp chat): Ollama running locally (default) or any OpenAI-compatible endpoint.

### 1.2 Install the server

```powershell
git clone https://github.com/sandraschi/browser-mcp
cd browser-mcp
uv sync
playwright install chromium
```

`uv sync` installs all Python dependencies including Playwright and browser-use. `playwright install chromium` downloads the Chromium binary that the automation engine uses. Note that this Chromium is separate from any Chrome you have installed; the automation tools use the Playwright-managed Chromium, while bookmark tools read your real browser profiles.

### 1.3 Start the server

Two modes:

```powershell
# stdio mode (Claude Desktop, stdio clients)
uv run browser-mcp

# HTTP mode (Cursor, webapp, IDE integrations) - port 10780
uv run python -m browser_mcp --serve
```

In HTTP mode the server answers MCP requests at `http://127.0.0.1:10780/mcp` and REST health checks at `http://127.0.0.1:10780/health`. The bundled webapp dashboard runs on port 10781 (`cd webapp && npm install && npm run dev`), or you can use the one-command starter:

```powershell
.\start.ps1
```

which clears stale ports, starts the backend with `--serve`, waits for health, launches the frontend, and opens your browser.

### 1.4 Verify it is alive

```powershell
Invoke-WebRequest http://127.0.0.1:10780/health
```

Expect a JSON answer with `"status": "ok"`. From any MCP client, call `browser_help()` and read the returned capability index.

### 1.5 First smoke test

Ask your client to run:

1. `list_browsers()` — see which browsers were detected.
2. `browse_page(url="https://example.com")` — the server launches Chromium, loads the page, and returns its text.
3. `close_browser()` — releases the browser.

If step 2 returns text content, your installation is complete.

## Section 2: Everyday Browsing

### 2.1 Reading a page

The most common operation is `browse_page`. It returns the visible text of a page, which is exactly what an AI can use to answer questions:

```
browse_page(url="https://en.wikipedia.org/wiki/Model_context_protocol")
```

The result contains `title`, the final `url` (redirects resolved), `status`, and up to 20,000 characters of `text`. For longer articles, read the first 20,000 characters, then follow up with `extract_text(selector="body")` on the same page — but note the same 20,000-character cap applies, so very long pages are best read in sections via `extract_text` with a container selector, or by asking for a summary of the part you already have.

### 2.2 Searching the web

There is no dedicated search tool: use a search engine like any other page.

```
browse_page(url="https://www.google.com/search?q=fastmcp+python")
```

The result text contains the search result titles, URLs, and snippets. For Bing use `https://www.bing.com/search?q=...`; for DuckDuckGo use `https://duckduckgo.com/?q=...` (DuckDuckGo blocks some automated traffic, so Google or Bing is more reliable). Search result links are plain text in the output; to open a result, take the URL from the result text and call `browse_page` again with it. If you need the raw href attributes, use `extract_text(selector="a")` — though innerText usually carries the same information.

### 2.3 Filling forms

Forms are handled with `fill_input` followed by `press_key` or a click:

```
fill_input(selector="#email", text="me@example.com")
fill_input(selector="#password", text="correct horse battery staple")
click_element(selector="button[type=submit]")
extract_text()
```

`fill_input` clears the field first, so there is no need to select-all or delete. If a form uses a custom widget (a rich text editor, a tag picker), the underlying `<input>` or `<textarea>` still usually responds to `fill_input`; if not, fall back to clicking the widget and pressing keys.

### 2.4 Navigating lists and pagination

For result lists that need paging (search engines, forums, category pages), the pattern is:

```
browse_page(url="https://news.ycombinator.com/")
extract_text(selector=".athing, .titleline")   # read current page items
press_key(key="ArrowDown")                      # move focus (if keyboard navigation)
click_element(selector="a.morelink")            # classic HN "More" link
```

Most sites use a "Next" link or button; find its selector from the extracted text or use a common class. Alternatively, compute the next page URL directly and call `browse_page` with it — this is usually more reliable than clicking.

### 2.5 Screenshots as evidence

`screenshot()` returns a base64 PNG. Write it to disk with any small script:

```python
import base64, json
# result = await screenshot()  (from your client)
open("page.png", "wb").write(base64.b64decode(result["screenshot_b64"]))
```

Use screenshots when you need visual proof (a rendered chart, a UI state) or when text extraction misses layout-critical information. Remember the screenshot covers the viewport only.

### 2.6 Verifying a page after an action

Always verify after mutating actions: after clicking "submit", the page either navigated (check `page.url` and `title` in the next `extract_text` result) or showed a validation error (the error text is in the page text). A robust pattern is: act, then `extract_text()`, then decide. Never assume a click succeeded just because the tool returned `success: true` — a click can succeed on a page that then fails to navigate.

## Section 3: Bookmark Management

### 3.1 Understanding the model

Bookmarks are stored per browser. Chrome, Edge, and Brave use a JSON file per profile; Firefox uses SQLite. The `browser_bookmarks` tool unifies all of them behind one interface: `operation` selects what to do, `browser` selects which browser's store to touch.

### 3.2 Listing bookmarks

```
browser_bookmarks(operation="list_bookmarks", browser="chrome")
browser_bookmarks(operation="list_bookmarks", browser="firefox")
```

The result contains the bookmark tree for the selected browser. For Firefox while the browser is running, the server falls back to a read-only copy of the database — this works for reads but writes may fail; close Firefox for reliable write operations.

### 3.3 Adding a bookmark

```
browser_bookmarks(operation="add_bookmark", browser="chrome",
                  url="https://example.com", title="Example Site", folder="Dev")
```

The `folder` argument is optional; omitted, the bookmark lands in the default location. `tags` are supported on Firefox.

### 3.4 Searching bookmarks

```
browser_bookmarks(operation="search_bookmarks", browser="firefox", search_query="documentation")
```

Returns matching bookmarks with ids, titles, URLs, and folder paths. Use the ids for subsequent `get_bookmark`, `edit_bookmark`, or `delete_bookmark` calls.

### 3.5 Cleaning up: duplicates, old links, broken links

The maintenance operations are the strongest reason to use this server:

```
# find duplicate URLs in a browser
browser_bookmarks(operation="find_duplicates", browser="firefox")

# bookmarks untouched for over a year
browser_bookmarks(operation="find_old_bookmarks", browser="firefox", age_days=365)

# verify links still resolve (Firefox only; slow on large libraries)
browser_bookmarks(operation="find_broken_links", browser="firefox", check_links=true)

# tag hygiene
browser_bookmarks(operation="find_similar_tags", browser="firefox")
browser_bookmarks(operation="merge_tags", browser="firefox", source_tag_ids=[...], target_tag_id=...)
```

Run these as a maintenance pass every few months. `find_broken_links` makes one network request per bookmark and can take minutes on big libraries — schedule it for a quiet moment.

### 3.6 Cross-browser sync

Migrate bookmarks from one browser to another:

```
browser_bookmarks(operation="sync_bookmarks", browser="chrome", target_browser="firefox", dry_run=true)
browser_bookmarks(operation="sync_bookmarks", browser="chrome", target_browser="firefox")
```

Always run with `dry_run=true` first to see how many bookmarks would be copied and to confirm the direction is right. The sync copies title and URL only; folders and tags are not preserved by the sync operation.

### 3.7 Exporting bookmarks

```
browser_bookmarks(operation="export_bookmarks", browser="firefox",
                  export_format="json", export_path="C:/backups/bookmarks.json")
browser_bookmarks(operation="export_bookmarks", browser="firefox",
                  export_format="csv", export_path="C:/backups/bookmarks.csv")
```

Exports are a cheap insurance policy before any bulk cleanup. Export, run the cleanup, then compare counts.

## Section 4: Agentic Workflows

### 4.1 The browser-use agent

`browser_agent` hands a natural-language task to an LLM-driven agent that can navigate, click, and type autonomously. It needs an LLM:

```powershell
# configure in your environment before starting the server
$env:LLM_BASE_URL = "http://127.0.0.1:11434"   # Ollama (default)
$env:LLM_MODEL = "gemma4:12b"                   # or your preferred model
```

Then, from the client:

```
browser_agent(task="Find the current price of the RTX 5090 on Amazon and report it")
browser_agent(task="Go to Wikipedia, find the page about the Model Context Protocol, and summarize its first section")
```

Guidance for good results:

- State the goal precisely and include the end deliverable ("report the price", "list the top 3 results").
- Include the starting URL in the task when you know it: "Starting at https://...".
- Keep `max_steps` reasonable (default 20). Long tasks with many clicks are slower and more error-prone.
- The agent works best when the goal is unambiguous. For deterministic single-page tasks, the direct tools (`browse_page`, `click_element`, `extract_text`) are faster and cheaper.

### 4.2 Batch link processing

`browse_items` processes a JSON list of links and returns per-item previews:

```
browse_items(items_json='[{"title":"FastMCP","url":"https://fastmcp.com"},{"title":"Playwright","url":"https://playwright.dev"}]',
             task="Summarize the key point from each link", max_items=10)
```

This tool is designed to chain with other MCP servers in the fleet: take `aiwatcher-mcp` top items, `arxiv-mcp` search results, or git issue lists, serialize them to the JSON shape, and get back structured previews you can feed into a summarization step. `max_items` bounds the work; start small, then scale.

### 4.3 Morning briefing routine

`morning_briefing` runs a fixed routine of pages from `conf/morning_pages.json`. Built-in profiles:

```
morning_briefing(config_name="default")   # HN + GitHub
morning_briefing(config_name="dev")       # HN + Python + Lobsters
morning_briefing(config_name="research")  # arXiv + Reddit ML
morning_briefing(config_name="fleet")     # repo activity
```

Add your own profile by editing `conf/morning_pages.json`: a profile is `{"label": ..., "pages": [{"name": ..., "url": ..., "task": ...}]}`. The result is a structured briefing with a text preview per page — ideal input for an LLM to turn into a morning summary.

### 4.4 Structured multi-step workflows

`browse_workflow` runs a bounded sequence of navigation and extraction steps with a full step log — no LLM required, deterministic behavior:

```
browse_workflow(task="Search for 'MCP servers' on GitHub and open the top result",
                initial_url="https://github.com/search?q=mcp+servers&type=repositories",
                max_steps=8)
```

The returned `steps` array documents every page visited, making it suitable for reproducible research workflows and audits.

## Section 5: HTTP REST Surface and the Webapp

### 5.1 REST endpoints

In HTTP mode the server exposes a small REST API alongside the MCP transport:

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Liveness and version |
| `GET /api/status` | Uptime, tool count, ports |
| `GET /api/capabilities` | Feature flags |
| `GET /api/skills` | Registered skills (empty on this server) |
| `GET /api/llm/discover` | Probe Ollama/LM Studio availability and models |
| `POST /api/llm/chat` | OpenAI-compatible chat proxy to the local LLM |
| `GET /api/fleet/webapps` | Fleet webapp discovery |
| `POST /api/shutdown` | Graceful shutdown |
| `GET /api/v1/diagnostics` | CUA smoke-test diagnostics |

Swagger UI is at `/docs`, ReDoc at `/redoc`.

### 5.2 The webapp dashboard

The React dashboard (port 10781) shows backend health, registered tools, bookmarks per browser, an LLM chat page, fleet app discovery, a Settings page for LLM provider/model selection, and API documentation. Zoom with Ctrl+scroll wheel; zoom level persists.

### 5.3 Connecting IDEs and desktop apps

- Cursor: add a streamable HTTP MCP server with URL `http://127.0.0.1:10780/mcp`.
- Claude Desktop: stdio command `uv --directory <repo> run browser-mcp` (or install the `.mcpb` bundle).
- The Tauri desktop app (`native/`) embeds the backend: one installer, one shortcut, browser automation on 10780.

## Section 6: Troubleshooting

### 6.1 The server starts but pages do not load

- Confirm Playwright browsers are installed: `playwright install chromium`.
- Check the headless flag: some sites block headless browsers. Pass `headless=false` to see the browser window and confirm it is a blocking issue.
- Confirm the URL is complete (includes `https://`).

### 6.2 Bookmark reads fail or are empty

- Firefox: if the browser is running, writes may fail and even reads can be flaky; close Firefox and retry. `force_access=true` enables the brute-force copy path for reads.
- Chrome/Edge/Brave: confirm the browser profile exists at the default location and the `Bookmarks` file is not corrupted (the server reports parse errors).
- Wrong profile: pass `profile_name` for Firefox profiles; the server lists them via `list_browsers()`.

### 6.3 The agent (browser_agent) errors

- Verify the LLM endpoint: `Invoke-WebRequest http://127.0.0.1:11434/api/tags` should return a model list. If you use a custom endpoint, set `LLM_BASE_URL` before starting the server.
- Verify `browser-use` is installed (`uv sync` installs it; the tool returns explicit instructions otherwise).
- Reduce `max_steps` and make the task goal-shaped.

### 6.4 Chat in the webapp fails

The chat proxies to the local LLM via `POST /api/llm/chat`. Check Settings for provider status; if Ollama is not detected, start it (`ollama serve`) or install it. The Settings page also lets you pick the provider and model.

### 6.5 Port conflicts

The server uses 10780 (HTTP/MCP) and the webapp uses 10781 (dev). If either is occupied, `start.ps1` clears zombies before binding. For a manual start, set `BROWSER_MCP_PORT` to a free port in the 10700-11500 range and mirror it in the webapp proxy config (`webapp/vite.config.ts`).

### 6.6 Reset a hung browser

Call `close_browser()`; the next automation call relaunches a fresh browser. If the server itself is hung, restart it (in HTTP mode, `POST /api/shutdown` after confirming no jobs are running).

## Section 7: Privacy and Operational Notes

- The server is local-only: it binds 127.0.0.1 and has no authentication. Keep it that way; exposing it to a LAN grants anyone browser control and bookmark access.
- Automation traffic is visible to the sites you visit (real browser fingerprint, your IP). Use this tool only where automation is permitted.
- Bookmark operations modify your real profile. Prefer `dry_run=true` and exports before bulk operations.
- The browser singleton persists between calls; close it when done to release resources.
- All tool failures are returned as structured errors — always check `success` before proceeding with follow-up actions.

## Section 8: End-to-End Walkthroughs

### 8.1 Research a topic with citations

Goal: collect three authoritative sources about a topic and keep a readable summary.

1. `browse_page(url="https://duckduckgo.com/html/?q=fastmcp+documentation")` — note: DuckDuckGo's HTML endpoint is more automation-friendly.
2. Read the result text; pick the first three URLs that look authoritative.
3. For each URL: `browse_page(url="<url>")`, then `extract_text()` to capture the article body.
4. Ask your client to compose a summary from the three extractions, listing the source URLs.
5. `close_browser()`.

### 8.2 Price check on an e-commerce site

Goal: find the current price of a product and the delivery options.

1. `browse_page(url="https://www.amazon.com/s?k=rtx+5090")`.
2. `extract_text()` — the result list shows product names and prices.
3. `click_element(selector="a[href*='/dp/']")` or navigate to the first product URL from the extracted text.
4. `extract_text(selector="#corePriceDisplay_desktop_feature_div, #price, .a-price")` — price selectors vary; if empty, fall back to `extract_text()` and scan for a price pattern (currency symbol + number).
5. `screenshot()` if you want visual evidence.
6. `close_browser()`.

### 8.3 Login flow

Goal: log into a service and confirm the logged-in state.

1. `browse_page(url="https://service.example/login")`.
2. `fill_input(selector="#username", text="<your username>")`.
3. `fill_input(selector="#password", text="<your password>")`.
4. `click_element(selector="button[type=submit]")` — or `press_key(key="Enter")` if the form submits on Enter.
5. `extract_text()` and verify the page shows the logged-in UI (e.g. an account menu, a greeting). If a CAPTCHA or 2FA step appears, pause and ask the human operator.
6. Do the work, then `close_browser()`.

Security note: never put real credentials in the prompt or in saved chat history; prefer a temporary session or ask the operator to enter them interactively.

### 8.4 Weekly bookmark hygiene

Goal: keep the bookmark library clean in ten minutes.

1. `browser_bookmarks(operation="export_bookmarks", browser="firefox", export_format="json", export_path="C:/backups/bookmarks-weekly.json")` — insurance first.
2. `browser_bookmarks(operation="find_duplicates", browser="firefox")` — review the list; delete obvious duplicates with `delete_bookmark`.
3. `browser_bookmarks(operation="find_old_bookmarks", browser="firefox", age_days=730)` — decide keep/delete for two-year-old bookmarks.
4. `browser_bookmarks(operation="find_similar_tags", browser="firefox")` — merge near-duplicate tags with `merge_tags`.
5. Optionally run `find_broken_links` (slow) on a subset: `browser_bookmarks(operation="search_bookmarks", browser="firefox", search_query="tutorial")` then check the shortlist.

### 8.5 Fleet-aware daily intake

Goal: turn yesterday's AI news into a short briefing.

1. From aiwatcher-mcp: `get_top_items(hours=24, limit=10)`.
2. Serialize the items to `[{"title": ..., "url": ...}, ...]` and pass them to `browse_items(items_json=..., task="Summarize the key point of each story", max_items=10)`.
3. Have your client compress the per-item previews into a three-bullet summary per story.
4. Optionally archive the interesting ones with `browser_bookmarks(operation="add_bookmark", browser="chrome", url=..., title=...)`.
5. `close_browser()`.

### 8.6 Automated acceptance check for a website

Goal: verify a site's main flows still work after a deployment.

1. `browse_page(url="https://your.site/")` — home loads (status 200).
2. `extract_text(selector="header nav")` — navigation present.
3. `click_element(selector="a[href='/pricing']")`, then `extract_text()` — pricing page renders.
4. `fill_input(selector="#search", text="test")` + `press_key(key="Enter")`, then `extract_text()` — search returns results.
5. Report status for each step; `close_browser()`.

## Section 9: Frequently Asked Questions

**Q: Do the automation tools use my installed Chrome?**
A: No. Automation launches the Playwright-managed Chromium binary (installed via `playwright install chromium`). Bookmark tools read and write your real browser profiles. If you need automation against your real profile (logged-in sessions), configure the Playwright launch with a persistent profile — the server does not do this by default.

**Q: Why does `browse_page` return only 20,000 characters?**
A: The cap keeps responses small enough for MCP clients. For longer pages, extract sections with `extract_text(selector="...")` targeting containers, or ask for a summary of the first chunk and follow up on specific sections.

**Q: Can I take full-page screenshots?**
A: Not with the current `screenshot()` (viewport only). For full-page capture, use the webapp or a Playwright script outside the server.

**Q: The Firefox bookmarks say the database is locked.**
A: Firefox locks `places.sqlite` while running. Reads fall back to a copy automatically; writes need Firefox closed. `force_access=true` enables the copy path for reads explicitly.

**Q: What does `dry_run` do in sync_bookmarks?**
A: It reports how many bookmarks would be copied from source to target without writing anything. Always run it once before a real sync.

**Q: How do I stop the HTTP server?**
A: `POST /api/shutdown` (after confirming nothing is running), or the `browser_shutdown(confirm=true)` MCP tool, or Ctrl+C on the terminal that started it.

**Q: Can the server control multiple tabs?**
A: Not yet — one page at a time per browser singleton. For parallel browsing, run multiple server instances on different ports (`BROWSER_MCP_PORT`).

**Q: Does it work on macOS/Linux?**
A: The Playwright layer is cross-platform; bookmark path detection and CLI browser tools are Windows-oriented. Bookmark operations on macOS/Linux may need path overrides.

**Q: How do I update after a new release?**
A: `git pull && uv sync` and reinstall Playwright browsers if the pinned Chromium changed (`playwright install chromium`).

## Section 10: Reference Card

Quick reference of every tool in one place:

| Tool | One-liner |
|------|-----------|
| `browse_page(url)` | Navigate and read a page |
| `click_element(selector)` | Click an element |
| `extract_text(selector)` | Read text from an element |
| `screenshot()` | Viewport PNG (base64) |
| `fill_input(selector, text)` | Type into an input |
| `press_key(key)` | Press a key |
| `close_browser()` | Release the browser |
| `list_browsers()` | Detect installed browsers |
| `browse_url_cli(url, browser)` | Headless CLI read |
| `browser_bookmarks(operation, browser, ...)` | Everything bookmark-related |
| `browser_agent(task)` | LLM-driven autonomous browsing |
| `morning_briefing(config_name)` | Daily page routine |
| `browse_items(items_json)` | Batch link processing |
| `browse_workflow(task)` | Logged multi-step browsing |
| `browser_help(topic)` | Documentation lookup |
| `browser_shutdown(confirm)` | Stop the server |

Configuration in one line: `BROWSER_MCP_PORT=10780`, `BROWSER_MCP_HOST=127.0.0.1`, `BROWSER_HEADLESS=true`, `LLM_BASE_URL=http://127.0.0.1:11434`, `LLM_MODEL=gemma4:12b`, `MCP_BRIDGE_URLS=` (optional comma-separated upstream proxies).

## Section 11: Power-User Patterns

### 11.1 Building a personal news clipper

Goal: maintain a weekly reading list from several sources without opening a browser.

1. Define the sources as a JSON list: sites, RSS-like pages, or search queries.
2. Each week, run `browse_items(items_json=<the list>, task="Extract the headline and first paragraph of each link", max_items=20)`.
3. Have your client produce a plain-text digest file and archive it (via file tools).
4. For links worth keeping, `browser_bookmarks(operation="add_bookmark", browser="firefox", url=..., title=..., folder="Read Later")`.

Because `browse_items` accepts any JSON array, you can generate the list programmatically (from a calendar, from git activity, from a database query) and let the server do the fetching.

### 11.2 Multi-step data collection with verification

Goal: collect tabular data from a paginated table.

1. `browse_page(url="https://example.com/table?page=1")`.
2. `extract_text(selector="table")` — the raw table text.
3. Ask your client to parse the text into rows (tab/newline separated) and accumulate them.
4. Find the next-page control: `extract_text()` to locate the pagination area, then `click_element(selector="a[rel=next]")` (or the site's next button).
5. Repeat until the last page; verify the row count grew each iteration (a common failure is clicking a stale selector that no longer navigates — the extracted URL tells you).

### 11.3 Cross-browser migration rehearsal

Goal: move from Chrome to Firefox without losing anything.

1. `browser_bookmarks(operation="export_bookmarks", browser="chrome", export_format="json", export_path="C:/backups/chrome.json")`.
2. `browser_bookmarks(operation="sync_bookmarks", browser="chrome", target_browser="firefox", dry_run=true)` — confirm the count matches the export.
3. `browser_bookmarks(operation="sync_bookmarks", browser="chrome", target_browser="firefox")`.
4. `browser_bookmarks(operation="list_bookmarks", browser="firefox")` — spot-check a few folders.
5. Keep the export file for a month as a safety net, then delete it.

### 11.4 Site monitoring loop

Goal: detect when a page changes (product in stock, article published).

1. `browse_page(url="<target>")` and capture `text` (or `screenshot()`).
2. Hash the text with a simple script and store the hash.
3. On a schedule, repeat step 1 and compare hashes; a difference triggers a notification.
4. When the change matters, `screenshot()` for evidence and hand the diff to your client for a summary.

The server's job is the fetch; the comparison is a few lines in any language. `browse_url_cli` is the lightest option for this pattern — no full Playwright session.

### 11.5 Using MCP_BRIDGE_URLS for combined automation

If you run other MCP servers over HTTP, you can proxy them through browser-mcp:

```powershell
$env:MCP_BRIDGE_URLS = "http://127.0.0.1:10946/mcp,http://127.0.0.1:10770/mcp"
uv run python -m browser_mcp --serve
```

Every proxied server's tools appear in the combined tool list, letting one client drive browsing plus, say, arXiv search or news ingestion in a single conversation. Bridge calls fail softly: a dead upstream returns a structured error instead of breaking the session.

### 11.6 Deterministic regression checks

For a fixed checklist of assertions (title contains X, element Y exists, HTTP status 200), encode it as a script that calls `browse_page` + `extract_text` per check and reports pass/fail. `browse_workflow` gives you the step log for free; reuse the same `task` string as a repeatable test. Keep `max_steps` small and assert on `success` and expected markers in the extracted text.

### 11.7 Responsible automation checklist

Before any session that touches other people's systems:

1. Confirm automation is permitted by the site's terms (many sites ban bots outright).
2. Keep request rates polite — no tight retry loops; the server's tools are single-action, so your client's loop cadence is your rate.
3. Never store real credentials in prompts or logs.
4. Prefer `dry_run` and exports before destructive bookmark operations.
5. Close the browser at the end of every session to release the singleton.
6. If a site visibly resists automation (CAPTCHA walls, aggressive blocking), stop and report — hammering it helps no one.

## Section 12: Glossary

| Term | Meaning |
|------|---------|
| stdio mode | MCP over stdin/stdout; default for Claude Desktop |
| HTTP mode | MCP streamable HTTP on port 10780 (`--serve`) |
| singleton | One shared Playwright page reused across tool calls |
| headless | Browser without a visible window |
| portmanteau | One tool with an `operation` discriminator (here: `browser_bookmarks`) |
| places.sqlite | Firefox bookmark database |
| brute-force access | Copying a locked Firefox DB to a temp file for reads |
| dry_run | Preview mode that writes nothing |
| CUA diagnostics | `GET /api/v1/diagnostics` used by installer smoke tests |
| MCP bridge | Proxying upstream MCP servers via `MCP_BRIDGE_URLS` |

## Section 13: Model-Specific Notes for AI Assistants

If you are an AI assistant using this server on behalf of a user, these notes align your behavior with the server's design:

- The 20,000-character text cap applies to every text extraction. When a page is longer, do not try to "get the rest" by calling the same tool repeatedly — instead read specific containers with `extract_text(selector=...)`, or ask the user whether a summary of the visible portion suffices.
- The browser is a singleton: your calls share page state. If you are uncertain about the current page, call `browse_page` to a known URL before proceeding; a fresh navigation is cheaper than reasoning about unknown state.
- `browser_bookmarks` results are flat lists of dicts; check `success` and the operation echo before assuming the shape you expected. Some operations (Firefox while running) degrade to read-only — surface that to the user rather than silently reporting an empty library.
- When chaining fleet servers, serialize lists to the `items_json` shape exactly: `[{"title": str, "url": str}]`. The `name` key is accepted as a title fallback; a missing `url` produces an error entry, not a crash.
- The `browser_agent` tool performs real actions on real websites. Treat its output as evidence to verify, not as a guarantee: confirm important outcomes with a follow-up `extract_text` or `screenshot` call.
- Prefer explicit, small steps for forms and checkouts: fill, then submit, then verify. Never fire multiple mutating actions without observing the result of each.
- When the user asks for automation on a site that requires login, remind them that the server launches a fresh, clean browser session (no saved cookies). If the task needs their logged-in session, discuss alternatives before proceeding.
- Respect the user's time and the site's load: batch with `max_items`, bound with `max_steps`, and do not retry failed navigations in tight loops. A single retry after a pause is the documented recovery pattern.



