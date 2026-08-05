"""PyInstaller entry point."""
import _strptime  # noqa: F401
import os
import sys
sys.path.insert(0, "src")
import _strptime  # noqa: F401
import uvicorn
from browser_mcp.app import app
port = int(os.environ.get("BROWSER_MCP_PORT", os.environ.get("PORT", "10780")))
host = os.environ.get("BROWSER_MCP_HOST", "127.0.0.1")
uvicorn.run(app, host=host, port=port)

