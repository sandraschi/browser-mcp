# browser-mcp User Guide

Browser automation, bookmark management, and AI browsing workflows. Navigate pages, click elements, extract text, take screenshots, fill forms, press keys, manage bookmarks across Chrome/Firefox/Edge/Brave, run multi-step browsing tasks, configure a morning briefing routine, and process link lists with structured summaries. Designed for integration with other MCP servers.

## Table of Contents

1. Installation
2. Quick Start
3. Tutorials (15 walkthroughs)
4. Bookmark Operations Reference
5. Configuration Reference
6. Morning Briefing Configuration
7. Troubleshooting
8. FAQ

---

## Installation

### Prerequisites
- Python 3.11+
- Playwright (browser automation engine)
- Chrome, Firefox, Edge, or Brave (for browsing)

### Quick Start

```bash
# Clone and enter directory
git clone https://github.com/sandraschi/browser-mcp.git
cd browser-mcp

# Install Python dependencies
uv sync

# Install the Playwright Chromium browser
uv run playwright install chromium

# Run in stdio mode (default — for Cursor, Claude Desktop)
uv run python -m browser_mcp

# For HTTP mode (FastAPI + streamable MCP)
uv run python -m browser_mcp --serve
```

### HTTP Mode

```bash
uv run python -m browser_mcp --serve
# Server: http://127.0.0.1:10780
# Health: http://127.0.0.1:10780/health
# MCP:    http://127.0.0.1:10780/mcp
```

## Tutorials

### Tutorial 1: Browse a Web Page

Navigate to any URL and extract the visible text:

```
browse_page(url="https://news.ycombinator.com")
```

This is the most common operation. It returns the page title, URL, all visible text (truncated at 20K characters), and the HTTP status code. Use it to read articles, check page content, or monitor website updates.

### Tutorial 2: Click Elements and Navigate

Navigate to a page, click a link, then read the target content:

```
browse_page(url="https://news.ycombinator.com")
click_element(selector=".athing .titleline a")
extract_text(selector="body")
```

The browser stays open between calls, so clicking advances the in-memory page state.

### Tutorial 3: Take a Screenshot

Capture a visual of the current viewport:

```
browse_page(url="https://example.com")
screenshot()
```

Returns a base64-encoded PNG. The screenshot is viewport-only (not full page). Use this for visual verification, page layout inspection, or archiving.

### Tutorial 4: Fill Forms and Submit

Automate a search:

```
browse_page(url="https://www.google.com")
fill_input(selector="textarea[name=q]", text="MCP browser automation")
press_key(key="Enter")
extract_text(selector="#search")
```

### Tutorial 5: List Installed Browsers

```
list_browsers()
```

Detects Chrome, Firefox (with profiles), Edge, and Brave on your system.

### Tutorial 6: CLI Browsing (No Playwright)

For quick text extraction without loading Playwright:

```
browse_url_cli(url="https://example.com", browser="chrome")
```

### Tutorial 7: List Firefox Bookmarks

```
browser_bookmarks(operation="list_bookmarks", browser="firefox")
```

Returns all bookmarks with IDs, titles, URLs, and timestamps.

### Tutorial 8: Add Bookmark to Chrome

```
browser_bookmarks(
  operation="add_bookmark",
  browser="chrome",
  url="https://github.com/sandraschi/browser-mcp",
  title="browser-mcp repo"
)
```

### Tutorial 9: Search Bookmarks

```
browser_bookmarks(
  operation="search_bookmarks",
  browser="firefox",
  search_query="python"
)
```

### Tutorial 10: Find Duplicate Bookmarks

```
browser_bookmarks(
  operation="find_duplicates",
  browser="firefox",
  similarity_threshold=0.85
)
```

### Tutorial 11: Export Bookmarks

```
browser_bookmarks(
  operation="export_bookmarks",
  browser="firefox",
  export_format="json"
)
```

### Tutorial 12: Morning Briefing

Run the default morning briefing:

```
morning_briefing(config_name="default")
```

Available profiles: `default`, `dev`, `research`, `fleet`

### Tutorial 13: Browse a List of Links

Chain with aiwatcher-mcp to research news items:

```
browse_items(
  items_json='[{"title":"HN Frontpage","url":"https://news.ycombinator.com"},{"title":"GitHub Trending","url":"https://github.com/trending"}]',
  task="Summarize what each page is about",
  max_items=5
)
```

### Tutorial 14: Multi-Step Browsing Workflow

```
browse_workflow(
  task="Go to Hacker News, find the top story, click it, and extract the article text",
  initial_url="https://news.ycombinator.com",
  max_steps=5
)
```

### Tutorial 15: Sync Bookmarks Between Browsers

Dry run Firefox to Chrome:

```
browser_bookmarks(
  operation="sync_bookmarks",
  browser="firefox",
  target_browser="chrome",
  dry_run=true
)
```

## Bookmark Operations Reference

### Firefox (17 operations)

| Operation | Parameters | Description |
|-----------|-----------|-------------|
| `list_bookmarks` | `folder_id?` | List all bookmarks |
| `get_bookmark` | `bookmark_id` | Get single bookmark |
| `add_bookmark` | `url, title, tags?` | Add bookmark |
| `search_bookmarks` | `search_query, search_type?` | Search by title/URL |
| `find_duplicates` | `similarity_threshold?` | Detect duplicates |
| `export_bookmarks` | `export_format, export_path?` | Export to JSON/HTML |
| `list_tags` | — | List all tags |
| `find_similar_tags` | — | Find tags to merge |
| `merge_tags` | `tags` (min 2) | Merge tags |
| `clean_up_tags` | — | Repair tag DB |
| `remove_unused_tags` | — | Delete unused tags |
| `batch_update_tags` | `tags, batch_size?` | Bulk tag update |
| `find_old_bookmarks` | `age_days` | Bookmarks older than N days |
| `find_forgotten_bookmarks` | `age_days` | Bookmarks unvisited N+ days |
| `get_bookmark_stats` | — | Count bookmarks/URLs/folders |
| `find_broken_links` | `check_links?` | Validate URLs |
| `refresh_bookmarks` | — | Refresh (stub) |

### Chrome/Edge/Brave (6 operations)

| Operation | Parameters | Description |
|-----------|-----------|-------------|
| `list_bookmarks` | — | List all bookmarks |
| `get_bookmark` | `bookmark_id` or `url` | Find bookmark |
| `add_bookmark` | `url, title, folder?` | Add bookmark |
| `edit_bookmark` | `bookmark_id` or `url`, `new_title?`, `new_folder?` | Edit bookmark |
| `delete_bookmark` | `bookmark_id` or `url` | Delete bookmark |
| `search` / `search_bookmarks` | `search_query` | Search by title/URL |

### Cross-Browser

| Operation | Parameters | Description |
|-----------|-----------|-------------|
| `sync_bookmarks` | `browser, target_browser, dry_run?` | Copy bookmarks |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `BROWSER_MCP_HOST` | `127.0.0.1` | HTTP bind address |
| `BROWSER_MCP_PORT` | `10780` | HTTP port |
| `BROWSER_HEADLESS` | `true` | Default headless mode |
| `MCP_TRANSPORT` | `stdio` | Transport mode |

## Morning Briefing Profiles

Edit `conf/morning_pages.json`:

```json
{
  "profiles": {
    "my_profile": {
      "label": "My Daily Read",
      "pages": [
        {"name": "HN", "url": "https://news.ycombinator.com", "task": "Top 10 stories"},
        {"name": "ArXiv AI", "url": "https://arxiv.org/list/cs.AI/recent", "task": "Recent ML papers"}
      ],
      "integration": {"aiwatcher_hours": 24, "aiwatcher_limit": 5}
    }
  }
}
```

## Troubleshooting

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| Navigation timeout (30s) | Slow page or wrong URL | Check URL, retry |
| Element not found | Wrong CSS selector | Inspect page for correct selector |
| Browser not launching | Playwright not installed | `uv run playwright install chromium` |
| Bookmark file not found | Browser hasn't synced | Bookmark something first in browser |
| Permission denied | Browser running (Chrome locks bookmarks file) | Close browser |
| Firefox "is running" error | Firefox open | Close Firefox completely |
| CLI browser not found | Not on PATH | Install browser or use browse_page |

## Playwright Installation Details

For the full browser automation experience, you need Playwright with Chromium installed:

```bash
# Install Playwright Python package (already done via uv sync)
# Then install the Chromium browser binary:
uv run playwright install chromium

# For Firefox support in Playwright:
uv run playwright install firefox

# For WebKit (Safari) support:
uv run playwright install webkit

# List installed browsers:
uv run playwright install --list
```

Playwright downloads browser binaries to `%USERPROFILE%\AppData\Local\ms-playwright`. These are self-contained and do not interfere with your installed browsers.

## CSS Selector Quick Reference

```
# Common selectors for browser-mcp tools:

# By ID
input#search  — <input id="search">
button#submit — <button id="submit">

# By class
.storylink   — <a class="storylink">
.nav-link    — <span class="nav-link">
.post-title  — <h2 class="post-title">

# By tag
h1           — First <h1>
article      — First <article>

# By attribute
[href]        — Any element with href attribute
[type="submit"] — <button type="submit">
[name="q"]    — <input name="q">
[href*="login"] — href containing "login"

# Combined
a.storylink        — <a> with class storylink
div#content p      — <p> inside <div id="content">
ul > li:first-child — First <li> in a <ul>
```

## HTTP Mode Deployment

```bash
# Start the HTTP server
uv run python -m browser_mcp --serve

# Health check
curl http://127.0.0.1:10780/health
# Returns: {"ok": true, "service": "browser-mcp", "version": "0.3.0", ...}

# Custom port
$env:BROWSER_MCP_PORT=10999; uv run python -m browser_mcp --serve
```

## Docker Deployment

```dockerfile
FROM python:3.12-slim
RUN pip install uv
WORKDIR /app
COPY . .
RUN uv sync
RUN uv run playwright install chromium
CMD ["uv", "run", "python", "-m", "browser_mcp"]
```

## Chaining with Other MCP Servers

### aiwatcher-mcp Pipeline

1. `aiwatcher-mcp.get_top_items(hours=24)` → returns list of articles with URLs
2. `browser-mcp.browse_items(items_json=result)` → visit each URL and extract text

### arxiv-mcp Pipeline

1. `arxiv-mcp.search_papers(query="MCP servers")` → returns paper list with URLs
2. `browser-mcp.browse_items(items_json=papers, task="Extract main results")` → deep read

### gitops-mcp Pipeline

1. `gitops-mcp.issue_list(owner="sandraschi", state="open")` → returns issue list
2. `browser-mcp.browse_items(items_json=issues)` → browse each issue

## Performance Notes

- First browser launch takes 2-5 seconds (Playwright startup + Chromium launch)
- Subsequent calls on the same page are near-instant (already loaded)
- Each page navigation takes 1-10 seconds depending on page complexity
- The browser instance consumes ~200MB RAM while active
- Call `close_browser()` when done to free resources
- CLI mode (`browse_url_cli`) is faster but less capable — no JavaScript execution

## Security Considerations

- The browser runs with default security settings — JavaScript is enabled
- Anti-bot systems may detect Playwright and block access
- Screenshots may capture sensitive information on the page
- Bookmark operations read/write your actual browser profile data
- The browser shares no cookies with your personal browser sessions
- Each browser launch starts fresh with no saved credentials

## FAQ

**Q: Do I need to install Playwright?**
A: Yes, for `browse_page`, `click_element`, `extract_text`, `screenshot`, `fill_input`, `press_key`, and the workflow tools. Run `uv run playwright install chromium`. CLI mode (`browse_url_cli`) only needs the respective browser on PATH.

**Q: Can I see the browser window?**
A: Set `BROWSER_HEADLESS=false` or pass `headless=false` to individual tools.

**Q: How long does a browser session last?**
A: The browser stays open until you call `close_browser()`. It is safe to call tools repeatedly — they reuse the same page.

**Q: Does `browser_bookmarks` work while the browser is running?**
A: For Chrome/Edge/Brave, reading the Bookmarks JSON file works while the browser is open. Writing requires caution. For Firefox, write operations require the browser to be closed.

**Q: Can I browse with Firefox instead of Chrome?**
A: Playwright uses Chromium by default. For Firefox Playwright, `uv run playwright install firefox`. For CLI mode, `browse_url_cli(browser="firefox")`.

**Q: What is the `morning_pages.json` file?**
A: Located at `conf/morning_pages.json`. It defines browsing profiles with page URLs, tasks, and integration hints. Custom profiles can be added.

**Q: What happens if the browser crashes?**
A: The singleton engine auto-restarts on the next tool call. Previous page state is lost.

**Q: Can I browse multiple pages simultaneously?**
A: No — the server uses a singleton browser instance. Consecutive calls share the same page. Call `close_browser()` between unrelated sessions.

**Q: Does `screenshot` capture the full page?**
A: No — it captures only the current viewport (default 1280x720). Full-page screenshots are not currently supported.

## Bookmark File Format

Chromium-based browsers (Chrome, Edge, Brave) store bookmarks in a JSON file. The structure is:

```json
{
  "roots": {
    "bookmark_bar": {
      "children": [
        {
          "type": "url",
          "id": "1",
          "name": "Example",
          "url": "https://example.com"
        },
        {
          "type": "folder",
          "id": "2",
          "name": "My Folder",
          "children": [
            {"type": "url", "id": "3", "name": "Nested", "url": "https://nested.com"}
          ]
        }
      ]
    },
    "other": {...},
    "synced": {...}
  }
}
```

Firefox stores bookmarks in a SQLite database (`places.sqlite`) with tables for bookmarks (`moz_bookmarks`), URLs (`moz_places`), tags, and keywords. The `browser_bookmarks` tool handles both formats transparently.

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `BROWSER_MCP_HOST` | `127.0.0.1` | HTTP server bind address |
| `BROWSER_MCP_PORT` | `10780` | HTTP server port |
| `BROWSER_MCP_HTTP_PATH` | `/mcp` | MCP streamable HTTP mount path |
| `BROWSER_MCP_FRONTEND_PORT` | `10781` | Webapp frontend dev port |
| `BROWSER_HEADLESS` | `true` | Default headless mode (true/false) |
| `MCP_TRANSPORT` | `stdio` | MCP transport mode (stdio/http/streamable) |
| `MCP_BRIDGE_URLS` | (empty) | Comma-separated MCP HTTP proxy URLs |

## Playwright Troubleshooting

If Playwright fails to launch or crashes:

```bash
# Verify Chromium is installed
uv run playwright install --list

# Force reinstall Chromium
uv run playwright install chromium --force

# Check for system dependencies (Linux only)
# uv run playwright install-deps

# Test Playwright directly
uv run python -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); print(p.chromium.launch(headless=True).version)"
```

## Bookmark Troubleshooting

**Chrome "Permission denied"**: Chrome must be closed to write to the Bookmarks file. Open Chrome, then close it fully, then retry the operation.

**Firefox "is running" error**: Firefox locks `places.sqlite` while open. Close Firefox completely before any write operation. Use `force_access=true` with read operations to bypass (creates a copy of the database).

**Edge/Brave bookmarks not found**: These browsers must have been opened and had at least one bookmark created before the Bookmarks file exists.

**Q: How do I handle cookie-based login?**
A: Login manually in a headed session (`headless=false`), then continue browsing. Cookies persist until `close_browser()` is called.
