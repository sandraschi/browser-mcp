# browser-mcp — Claude Code Guide

## Overview
FastMCP 3.2 server for Playwright browser automation — browse, click, screenshot, and cross-browser bookmark management.

## Entry Points
- `uv run browser-mcp` → `browser_mcp.__main__:main`
- Backend: `uv run uvicorn browser_mcp.app:app --host 127.0.0.1 --port 10780`

## Standards
- FastMCP 3.4+ portmanteau tool pattern — tools use `operation` enum param
- Responses: structured dicts with `success`, `message`, domain-specific fields
- Dual transport: stdio (Claude Desktop) + HTTP (`MCP_TRANSPORT=http`)
- See [mcp-central-docs](https://github.com/sandraschi/mcp-central-docs) for fleet-wide coding standards

## Key Files
- `README.md` — full documentation
- `pyproject.toml` — build config and entry points
- `src/browser_mcp/server.py` — FastMCP tools
- `src/browser_mcp/app.py` — FastAPI + MCP HTTP mount
