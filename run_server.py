"""PyInstaller entry point."""

import _strptime  # noqa: F401
import os
import sys

sys.path.insert(0, "src")
import uvicorn

from browser_mcp.app import app, register_uvicorn

port = int(os.environ.get("BROWSER_MCP_PORT", os.environ.get("PORT", "10780")))
host = os.environ.get("BROWSER_MCP_HOST", "127.0.0.1")
config = uvicorn.Config(app, host=host, port=port)
server = uvicorn.Server(config)
register_uvicorn(server)
server.run()
