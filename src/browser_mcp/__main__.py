"""
CLI entry point: stdio (default), HTTP (--serve), or quick info subcommands.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os

import uvicorn

from browser_mcp import __version__
from browser_mcp.config import load_settings
from browser_mcp.server import mcp


def _configure_logging(*, debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def _cmd_version() -> None:
    print(f"browser-mcp {__version__}")


def _cmd_browsers() -> None:
    import asyncio as _asyncio

    from browser_mcp.server import list_browsers

    result = _asyncio.run(list_browsers())
    for name, info in result["browsers"].items():
        status = "installed" if info["installed"] else "missing"
        print(f"{name:<8} {status}" + (f"  {info['path']}" if info.get("path") else ""))


def _cmd_health() -> None:
    import asyncio as _asyncio

    from browser_mcp import app as _app
    from browser_mcp.server import list_browsers

    browsers = _asyncio.run(list_browsers())
    installed = [n for n, b in browsers["browsers"].items() if b["installed"]]
    sources = _app._bookmark_sources()
    providers = _asyncio.run(_app._probe_llm())
    llm = [p["name"] for p in providers if p["status"] == "detected"]
    print(f"service:     browser-mcp {__version__}")
    print(f"browsers:    {', '.join(installed) if installed else 'none detected'}")
    print(f"bookmarks:   {', '.join(n for n, s in sources.items() if s['available']) or 'no sources'}")
    print(f"llm:         {', '.join(llm) or 'none detected'}")
    print(f"tools:       {_asyncio.run(_app._tool_count_async())}")


def main() -> None:
    parser = argparse.ArgumentParser(description="browser-mcp (FastMCP 3.2)")
    parser.add_argument("--serve", action="store_true", help="Run FastAPI + MCP HTTP")
    parser.add_argument("--stdio", action="store_true", help="MCP stdio (default)")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--version", action="store_true", help="Print version and exit")
    parser.add_argument("--list-browsers", action="store_true", help="List detected browsers and exit")
    parser.add_argument("--health", action="store_true", help="Print a quick health summary and exit")
    args = parser.parse_args()

    if args.version:
        _cmd_version()
        return
    if args.list_browsers:
        _cmd_browsers()
        return
    if args.health:
        _cmd_health()
        return

    _configure_logging(debug=args.debug)

    transport = os.getenv("MCP_TRANSPORT", "").lower()
    use_http = args.serve or transport in {"http", "streamable"}

    settings = load_settings()

    if use_http:
        logger = logging.getLogger("browser-mcp")
        logger.info("Starting HTTP on %s:%d", settings.host, settings.port)
        from browser_mcp.app import app, register_uvicorn

        config = uvicorn.Config(app, host=settings.host, port=settings.port, reload=False)
        server = uvicorn.Server(config)
        register_uvicorn(server)
        server.run()
        return

    asyncio.run(mcp.run_stdio_async())


if __name__ == "__main__":
    main()
