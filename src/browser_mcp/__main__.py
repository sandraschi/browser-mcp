"""
CLI entry point: stdio (default) or HTTP (--serve).
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os

import uvicorn

from browser_mcp.config import load_settings
from browser_mcp.server import mcp


def _configure_logging(*, debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="browser-mcp (FastMCP 3.2)")
    parser.add_argument("--serve", action="store_true", help="Run FastAPI + MCP HTTP")
    parser.add_argument("--stdio", action="store_true", help="MCP stdio (default)")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    _configure_logging(debug=args.debug)

    transport = os.getenv("MCP_TRANSPORT", "").lower()
    use_http = args.serve or transport in {"http", "streamable"}

    settings = load_settings()

    if use_http:
        logger = logging.getLogger("browser-mcp")
        logger.info("Starting HTTP on %s:%d", settings.host, settings.port)
        uvicorn.run(
            "browser_mcp.app:app",
            host=settings.host,
            port=settings.port,
            reload=False,
        )
        return

    asyncio.run(mcp.run_stdio_async())


if __name__ == "__main__":
    main()
