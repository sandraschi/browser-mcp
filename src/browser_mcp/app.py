"""
FastAPI app: /health + MCP streamable HTTP mount.
"""

from __future__ import annotations

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from browser_mcp.config import load_settings
from browser_mcp.server import mcp

mcp_http = mcp.http_app(path="/")


def build_app() -> FastAPI:
    settings = load_settings()

    app = FastAPI(
        title="browser-mcp",
        version="0.3.0",
        lifespan=mcp_http.lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:10777",
            "http://localhost:10777",
            "http://127.0.0.1:10780",
            "http://localhost:10780",
            "http://127.0.0.1:10781",
            "http://localhost:10781",
            "http://tauri.localhost",
            "https://tauri.localhost",
            "tauri://localhost",
        ],
        allow_origin_regex=r"https?://(?:[a-zA-Z0-9-]+\.ts\.net|.*?\.tail-[a-f0-9]+\.ts\.net|tauri\.localhost|localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|100\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?$|^tauri://localhost$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health():
        return {
            "ok": True,
            "service": "browser-mcp",
            "version": "0.3.0",
            "port": settings.port,
            "frontend_port": settings.frontend_port,
            "mcp_http": f"http://{settings.host}:{settings.port}{settings.mcp_http_path}",
        }

    @app.get("/api/v1/diagnostics")
    async def diagnostics():
        try:
            import psutil

            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage("/").percent
        except ImportError:
            cpu = mem = disk = None
        tool_count = len(getattr(mcp, "_tools", {})) if hasattr(mcp, "_tools") else 0
        return {
            "success": True,
            "backend": {"port": settings.port, "status": "running"},
            "system": {"cpu_percent": cpu, "memory_percent": mem, "disk_percent": disk},
            "tools": {"total": tool_count},
            "cua_status": {"tesseract_available": False, "window_found": False},
        }

    app.mount(settings.mcp_http_path, mcp_http)
    return app


app = build_app()
