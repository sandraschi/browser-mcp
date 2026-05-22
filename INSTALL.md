# Installation

## Quick Start

```powershell
# Prerequisites: Python 3.13+, uv (https://docs.astral.sh/uv/)

git clone https://github.com/sandraschi/browser-mcp
cd browser-mcp

# Install Python dependencies
uv sync

# Install Playwright browsers
uv run playwright install chromium

# Start the server (HTTP mode — port 10780)
uv run browser-mcp --serve

# In another terminal — start the webapp dashboard (port 10781)
cd webapp
npm install
npm run dev
```

Open `http://localhost:10781` in your browser.

---

## MCP Client Configuration

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "browser-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "C:/path/to/browser-mcp",
        "run",
        "browser-mcp"
      ],
      "env": {
        "PYTHONPATH": "C:/path/to/browser-mcp/src",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

### OpenCode

```json
{
  "browser-mcp": {
    "command": "uv",
    "args": ["--directory", "C:/path/to/browser-mcp", "run", "browser-mcp"],
    "env": {
      "PYTHONPATH": "C:/path/to/browser-mcp/src",
      "PYTHONUNBUFFERED": "1"
    }
  }
}
```

---

## Manual Setup

```powershell
# Create and activate virtual environment
uv venv
.venv\Scripts\activate

# Install with dev dependencies
uv sync --group dev

# Install Playwright browsers
uv run playwright install chromium

# Run tests
uv run pytest -q

# Run linter
uv run ruff check src/
```

---

## Docker (coming soon)

Docker support is planned. Track progress in [issue #1](https://github.com/sandraschi/browser-mcp/issues/1).

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `playwright` not found | Run `uv run playwright install chromium` |
| Port 10780 in use | Kill the process: `Get-NetTCPConnection -LocalPort 10780 \| Stop-Process -Id $_.OwningProcess` |
| Firefox bookmarks locked | Close Firefox completely, or use `force_access=True` for read operations |
| Chrome bookmarks not found | Ensure Chrome has bookmarks saved to the default profile |
| `uv` not found | Install it: `powershell -c "irm https://astral.sh/uv/install.ps1 \| iex"` |
| Other | [Open a GitHub issue](https://github.com/sandraschi/browser-mcp/issues) |

---

*See [README.md](README.md) for full feature documentation.*
