"""
FastAPI app: /health + MCP streamable HTTP mount + webapp REST surface.
"""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from browser_mcp.config import load_settings
from browser_mcp.server import mcp

mcp_http = mcp.http_app(path="/")

_started_at = time.time()

# Fire-and-forget tasks kept alive by reference (RUF006)
_bg_tasks: list[asyncio.Task] = []

OLLAMA_BASE = os.getenv("BROWSER_MCP_OLLAMA_BASE", "http://127.0.0.1:11434")
LMSTUDIO_BASE = os.getenv("BROWSER_MCP_LMSTUDIO_BASE", "http://127.0.0.1:1234")

# Fleet webapp ports probed by the Apps hub (bounded, 1s timeout each)
_FLEET_WEBAPPS = [
    ("aiwatcher", 10947),
    ("arxiv", 10771),
    ("calibre", 10721),
    ("email", 10812),
    ("plex", 10741),
    ("opencode-cli", 10950),
    ("meta", 10719),
    ("depot", 10726),
]


def _settings_payload() -> dict[str, Any]:
    settings = load_settings()
    return {
        "service": "browser-mcp",
        "version": "0.3.0",
        "port": settings.port,
        "frontend_port": settings.frontend_port,
        "uptime_seconds": int(time.time() - _started_at),
        "tool_count": len(getattr(mcp, "_tools", {}) or {}),
    }


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
        return {"status": "ok", **_settings_payload()}

    @app.get("/api/status")
    async def status():
        return {"status": "ok", **_settings_payload()}

    @app.get("/api/capabilities")
    async def capabilities():
        return {
            "status": "ok",
            "server": "browser-mcp",
            "version": "0.3.0",
            "features": {
                "browser_automation": True,
                "bookmarks": True,
                "agentic_workflows": True,
                "chat": True,
                "local_llm": True,
                "apps_hub": True,
                "native": True,
            },
        }

    @app.get("/api/skills")
    async def skills():
        return {"skills": [], "count": 0}

    @app.get("/api/llm/discover")
    async def llm_discover():
        providers = []
        async with httpx.AsyncClient(timeout=3.0) as client:
            ollama_ok = False
            try:
                r = await client.get(f"{OLLAMA_BASE}/api/tags")
                if r.status_code == 200:
                    models = [m.get("name", "") for m in r.json().get("models", [])]
                    providers.append(
                        {"name": "ollama", "port": 11434, "base": OLLAMA_BASE, "status": "detected", "models": models}
                    )
                    ollama_ok = True
            except Exception:
                pass
            if not ollama_ok:
                providers.append(
                    {"name": "ollama", "port": 11434, "base": OLLAMA_BASE, "status": "not_found", "models": []}
                )
            lm_ok = False
            try:
                r = await client.get(f"{LMSTUDIO_BASE}/v1/models")
                if r.status_code == 200:
                    models = [m.get("id", "") for m in r.json().get("data", [])]
                    providers.append(
                        {
                            "name": "lmstudio",
                            "port": 1234,
                            "base": LMSTUDIO_BASE,
                            "status": "detected",
                            "models": models,
                        }
                    )
                    lm_ok = True
            except Exception:
                pass
            if not lm_ok:
                providers.append(
                    {"name": "lmstudio", "port": 1234, "base": LMSTUDIO_BASE, "status": "not_found", "models": []}
                )
        return {"status": "ok", "providers": providers}

    @app.post("/api/llm/chat")
    async def llm_chat(request: Request):
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "invalid JSON body"}, status_code=400)
        messages = body.get("messages") or []
        model = body.get("model") or "gemma4:12b"
        if not messages:
            return JSONResponse({"error": "messages required"}, status_code=400)
        payload = {"model": model, "messages": messages, "stream": False}
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                r = await client.post(f"{OLLAMA_BASE}/v1/chat/completions", json=payload)
                if r.status_code != 200:
                    return JSONResponse(
                        {"error": f"ollama returned HTTP {r.status_code}: {r.text[:200]}"}, status_code=502
                    )
                return r.json()
        except Exception as exc:
            return JSONResponse({"error": f"ollama unreachable at {OLLAMA_BASE}: {exc}"}, status_code=503)

    @app.get("/api/fleet/webapps")
    async def fleet_webapps():
        apps = []

        async def _probe(label: str, port: int) -> None:
            try:
                async with httpx.AsyncClient(timeout=1.0) as client:
                    r = await client.get(f"http://127.0.0.1:{port}/health")
                    if r.status_code < 500:
                        apps.append({"label": label, "port": port, "url": f"http://127.0.0.1:{port}", "up": True})
            except Exception:
                pass

        await asyncio.gather(*(_probe(label, port) for label, port in _FLEET_WEBAPPS))
        return {"status": "ok", "webapps": apps}

    @app.post("/api/shutdown")
    async def shutdown():
        async def _exit() -> None:
            await asyncio.sleep(0.5)
            os._exit(0)

        _shutdown_task = asyncio.create_task(_exit())
        _bg_tasks.append(_shutdown_task)
        return {"status": "ok", "message": "shutting down"}

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
