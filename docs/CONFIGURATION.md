# Configuration

All configuration is via environment variables read at startup (`src/browser_mcp/config.py`).

| Variable | Default | Description |
|----------|---------|-------------|
| `BROWSER_MCP_PORT` | `10780` | HTTP/MCP server port |
| `BROWSER_MCP_HOST` | `127.0.0.1` | Bind host |
| `BROWSER_MCP_HTTP_PATH` | `/mcp` | MCP streamable HTTP path |
| `BROWSER_HEADLESS` | `true` | Default headless mode for automation |
| `BROWSER_MCP_FRONTEND_PORT` | `10781` | Vite dev port |
| `LLM_BASE_URL` | `http://127.0.0.1:11434` | OpenAI-compatible LLM base (browser-use agent, chat) |
| `LLM_MODEL` | `gemma4:12b` | Default model |
| `MCP_BRIDGE_URLS` | (empty) | Comma-separated upstream MCP URLs to proxy |
| `MCP_TRANSPORT` | (empty) | `http` forces HTTP mode in `python -m browser_mcp` |

## Ports

- Backend: `10780` (REST `/api/*`, health `/health`, MCP `/mcp`, Swagger `/docs`)
- Frontend (dev): `10781` (Vite, proxies `/api`, `/mcp`, `/health` to the backend)

## LLM

The chat page and `browser_agent` need a local LLM (Ollama recommended, port 11434).
LM Studio (1234) is auto-detected by `GET /api/llm/discover` for the webapp Settings page.

## .env

Copy `.env.example` to `.env` at the repo root. The Tauri build bundles only
`.env.example` (never `.env`) so personal keys never ship in the installer.
