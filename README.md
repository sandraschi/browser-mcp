# browser-mcp

**FastMCP 3.2 Playwright browser automation server.**

Browse, click, screenshot, extract text, fill forms — all over MCP.

## Tools

| Tool | Description |
|------|-------------|
| `browse_page(url)` | Navigate to URL, extract visible text |
| `click_element(selector)` | Click an element by CSS selector |
| `extract_text(selector)` | Extract text from a selector |
| `screenshot()` | Viewport screenshot as base64 PNG |
| `fill_input(selector, text)` | Type into an input field |
| `press_key(key)` | Press a keyboard key |
| `close_browser()` | Close browser, release resources |

## Usage

```bash
# stdio mode (Claude Desktop)
uv run browser-mcp --stdio

# HTTP mode (port 10780)
uv run browser-mcp --serve
```

## Config

| Env Var | Default | Description |
|---------|---------|-------------|
| `BROWSER_MCP_HOST` | 127.0.0.1 | HTTP bind address |
| `BROWSER_MCP_PORT` | 10780 | HTTP port |
| `BROWSER_HEADLESS` | true | Run headless or visible |
