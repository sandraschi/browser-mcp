"""
FastAPI app: /health + MCP streamable HTTP mount.
"""

from __future__ import annotations

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from browser_mcp.config import load_settings
from browser_mcp.server import mcp

mcp_http = mcp.http_app(path="/mcp")


def build_app() -> FastAPI:
    settings = load_settings()

    app = FastAPI(
        title="browser-mcp",
        version="0.1.0",
        lifespan=mcp_http.lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health():
        return {
            "ok": True,
            "service": "browser-mcp",
            "version": "0.2.0",
            "port": settings.port,
            "frontend_port": settings.frontend_port,
            "mcp_http": f"http://{settings.host}:{settings.port}{settings.mcp_http_path}",
        }

    app.mount(settings.mcp_http_path, mcp_http)
    return app


app = build_app()
