# browser-mcp

<p align="center">
  <a href="https://github.com/casey/just"><img src="https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square&logo=just&logoColor=white" alt="Just"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.2-7c5cfc?style=flat-square" alt="FastMCP"></a>
</p>


> 📖 **[Installation Guide](INSTALL.md)** — quick start, manual setup, and troubleshooting

**FastMCP 3.2 Playwright browser automation server.**

Browse, click, screenshot, extract text, fill forms — all over MCP.

## Quick Start

```powershell
git clone https://github.com/sandraschi/browser-mcp
cd browser-mcp
just
```

This opens an interactive dashboard showing all available commands. Run `just bootstrap` to install dependencies, then `just serve` or `just dev` to start.

### Manual Setup

If you don't have `just` installed:

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
