"""
FastAPI app: /health + MCP streamable HTTP mount + webapp REST surface.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from browser_mcp.config import load_settings
from browser_mcp.logs import LOG_BUFFER, attach_log_buffer
from browser_mcp.server import mcp

logger = logging.getLogger(__name__)

mcp_http = mcp.http_app(path="/")

_started_at = time.time()

# Fire-and-forget tasks kept alive by reference (RUF006)
_bg_tasks: list[asyncio.Task] = []

# uvicorn Server instance (registered by entrypoints) for graceful shutdown
_uvicorn_server: Any = None


def register_uvicorn(server: Any) -> None:
    """Hand the running uvicorn Server to /api/shutdown for graceful exit."""
    global _uvicorn_server
    _uvicorn_server = server


OLLAMA_BASE = os.getenv("BROWSER_MCP_OLLAMA_BASE", "http://127.0.0.1:11434")
LMSTUDIO_BASE = os.getenv("BROWSER_MCP_LMSTUDIO_BASE", "http://127.0.0.1:1234")
VLLM_BASE = os.getenv("BROWSER_MCP_VLLM_BASE", "http://127.0.0.1:8000")

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

_VERSION = "0.3.0"
_TOOL_COUNT_CACHE: int | None = None


async def _tool_count_async() -> int:
    """Cached MCP tool count, computed in the running loop (never asyncio.run)."""
    global _TOOL_COUNT_CACHE
    if _TOOL_COUNT_CACHE is None:
        try:
            tools = await mcp.list_tools()
            _TOOL_COUNT_CACHE = len(tools)
        except Exception:
            _TOOL_COUNT_CACHE = 0
    return _TOOL_COUNT_CACHE


async def _settings_payload() -> dict[str, Any]:
    settings = load_settings()
    return {
        "service": "browser-mcp",
        "version": _VERSION,
        "port": settings.port,
        "frontend_port": settings.frontend_port,
        "uptime_seconds": int(time.time() - _started_at),
        "tool_count": await _tool_count_async(),
    }


def _detect_browsers() -> dict[str, dict[str, Any]]:
    """Detect installed browsers from common install paths (cheap, local)."""
    pf = os.environ.get("ProgramFiles", "") or r"C:\Program Files"
    pf86 = os.environ.get("ProgramFiles(x86)", "") or r"C:\Program Files (x86)"
    checks = {
        "chrome": [r"Google\Chrome\Application\chrome.exe", r"Google\Chrome SxS\Application\chrome.exe"],
        "firefox": [r"Mozilla Firefox\firefox.exe"],
        "edge": [r"Microsoft\Edge\Application\msedge.exe"],
        "brave": [r"BraveSoftware\Brave-Browser\Application\brave.exe"],
    }
    result: dict[str, dict[str, Any]] = {}
    for name, paths in checks.items():
        found = next(
            (os.path.join(base, p) for p in paths for base in (pf, pf86) if os.path.exists(os.path.join(base, p))),
            None,
        )
        result[name] = {"installed": bool(found), "path": found}
    return result


def _firefox_places() -> Path | None:
    base = Path(os.environ.get("APPDATA", "")) / "Mozilla" / "Firefox" / "Profiles"
    if not base.exists():
        return None
    for prof in base.glob("*/places.sqlite"):
        return prof
    return None


def _bookmark_sources() -> dict[str, dict[str, Any]]:
    """Report which browsers expose a readable bookmark source."""
    from browser_mcp.bookmarks import chromium_common as cc

    result: dict[str, dict[str, Any]] = {}
    for name, paths in (
        ("chrome", cc.CHROME_BOOKMARK_PATHS),
        ("edge", cc.EDGE_BOOKMARK_PATHS),
        ("brave", cc.BRAVE_BOOKMARK_PATHS),
    ):
        p = cc._find_first_existing(list(paths))
        result[name] = {"available": p is not None, "path": str(p) if p else None}
    fp = _firefox_places()
    result["firefox"] = {"available": fp is not None, "path": str(fp) if fp else None}
    return result


async def _probe_llm() -> list[dict[str, Any]]:
    """Probe Ollama / LM Studio / vLLM and report reachability + models."""
    targets = [
        ("ollama", 11434, OLLAMA_BASE, "/api/tags", "models", "name"),
        ("lmstudio", 1234, LMSTUDIO_BASE, "/v1/models", "data", "id"),
        ("vllm", 8000, VLLM_BASE, "/v1/models", "data", "id"),
    ]
    providers: list[dict[str, Any]] = []

    async def _probe(name: str, port: int, base: str, path: str, key: str, field: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=2.5) as client:
                r = await client.get(f"{base}{path}")
            if r.status_code == 200:
                models = [m.get(field, "") for m in r.json().get(key, [])]
                providers.append({"name": name, "port": port, "base": base, "status": "detected", "models": models})
                return
        except Exception as exc:
            logger.debug("LLM provider probe failed for %s: %s", name, exc)
        providers.append({"name": name, "port": port, "base": base, "status": "not_found", "models": []})

    await asyncio.gather(*(_probe(n, port, base, path, key, field) for n, port, base, path, key, field in targets))
    return providers


def build_app() -> FastAPI:
    settings = load_settings()

    attach_log_buffer()

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
        # Lightweight liveness + readiness (local FS checks only, no network).
        browsers = _detect_browsers()
        sources = _bookmark_sources()
        browser_installed = any(b["installed"] for b in browsers.values())
        bookmarks_available = any(s["available"] for s in sources.values())
        return {
            "status": "ok",
            "ready": browser_installed or bookmarks_available,
            **await _settings_payload(),
            "checks": {
                "browser": browser_installed,
                "bookmarks": bookmarks_available,
            },
        }

    @app.get("/api/status")
    async def status():
        settings = load_settings()
        browsers = _detect_browsers()
        sources = _bookmark_sources()
        providers = await _probe_llm()
        return {
            "status": "ok",
            **await _settings_payload(),
            "host": settings.host,
            "headless": settings.headless,
            "platform": sys.platform,
            "python_version": sys.version.split()[0],
            "mcp_transport": settings.mcp_http_path,
            "browsers": browsers,
            "bookmarks_sources": sources,
            "llm": providers,
            "llm_detected": any(p["status"] == "detected" for p in providers),
        }

    @app.get("/api/capabilities")
    async def capabilities():
        settings = load_settings()
        return {
            "status": "ok",
            "server": "browser-mcp",
            "version": _VERSION,
            "mcp_transport": settings.mcp_http_path,
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
        providers = await _probe_llm()
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
            except Exception as exc:
                logger.debug("Fleet webapp probe failed for %s:%s: %s", label, port, exc)

        await asyncio.gather(*(_probe(label, port) for label, port in _FLEET_WEBAPPS))
        return {"status": "ok", "webapps": apps}

    @app.post("/api/shutdown")
    async def shutdown(confirm: bool = False):
        if not confirm:
            return JSONResponse(
                {"status": "error", "message": "Set confirm=true to shut down the server."}, status_code=400
            )
        server = _uvicorn_server
        if server is not None:
            server.should_exit = True
            return {"status": "ok", "message": "Graceful shutdown initiated"}

        async def _exit() -> None:
            await asyncio.sleep(0.3)
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
        tool_count = await _tool_count_async()
        browsers = _detect_browsers()
        sources = _bookmark_sources()
        return {
            "success": True,
            "backend": {"port": settings.port, "status": "running", "version": _VERSION},
            "system": {"cpu_percent": cpu, "memory_percent": mem, "disk_percent": disk},
            "tools": {"total": tool_count},
            "browsers": browsers,
            "bookmarks_sources": sources,
            "cua_status": {"tesseract_available": False, "window_found": False},
        }

    @app.get("/api/browsers")
    async def browsers():
        detected = _detect_browsers()
        return {"status": "ok", "browsers": detected, "count": sum(1 for b in detected.values() if b["installed"])}

    @app.get("/api/bookmarks/sources")
    async def bookmarks_sources():
        sources = _bookmark_sources()
        return {
            "status": "ok",
            "sources": sources,
            "available": [name for name, s in sources.items() if s["available"]],
        }

    @app.get("/api/bookmarks")
    async def api_bookmarks(browser: str = "chrome", limit: int = 100_000):
        """Bulk bookmark list for the webapp (plain JSON - avoids MCP SSE for large data)."""
        from browser_mcp.bookmarks.portmanteau import browser_bookmarks

        result = await browser_bookmarks(operation="list_bookmarks", browser=browser, limit=limit)
        if "bookmarks" not in result:
            return {"status": "error", "browser": browser, "error": result.get("error", "failed to load")}
        return {
            "status": "ok",
            "browser": browser,
            "bookmarks": result["bookmarks"],
            "total_count": result.get("total_count", len(result["bookmarks"])),
        }

    @app.get("/api/bookmarks/tags")
    async def api_bookmark_tags():
        from browser_mcp import tags

        return {"status": "ok", "tag_map": tags.all_tags_by_url(), "tags": tags.list_tags()}

    @app.get("/api/logs")
    async def logs(tail: int = 200):
        tail = max(0, min(tail, 5000))
        return {"lines": LOG_BUFFER.snapshot(tail=tail), "count": len(LOG_BUFFER.snapshot(tail=tail))}

    @app.post("/api/logs/clear")
    async def logs_clear():
        LOG_BUFFER.clear()
        return {"status": "ok", "lines": []}

    app.mount(settings.mcp_http_path, mcp_http)
    return app


app = build_app()
