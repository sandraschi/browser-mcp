"""Core smoke tests: server import, tool registration, REST surface."""

from __future__ import annotations

import pytest

from browser_mcp.app import build_app
from browser_mcp.config import load_settings
from browser_mcp.server import mcp


def test_settings_defaults() -> None:
    settings = load_settings()
    assert settings.host == "127.0.0.1"
    assert settings.port == 10780
    assert settings.frontend_port == 10781
    assert settings.mcp_http_path == "/mcp"


@pytest.mark.asyncio
async def test_tools_registered() -> None:
    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    for expected in [
        "browse_page",
        "click_element",
        "extract_text",
        "screenshot",
        "fill_input",
        "press_key",
        "close_browser",
        "list_browsers",
        "browse_url_cli",
        "browser_bookmarks",
        "browser_agent",
        "morning_briefing",
        "browse_items",
        "browse_workflow",
        "browser_help",
        "browser_shutdown",
    ]:
        assert expected in names, f"tool {expected} not registered"


@pytest.mark.asyncio
async def test_tools_have_help_and_shutdown() -> None:
    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    assert "browser_help" in names
    assert "browser_shutdown" in names


@pytest.mark.asyncio
async def test_docstrings_have_return_format() -> None:
    tools = await mcp.list_tools()
    for tool in tools:
        doc = tool.fn.__doc__ or ""
        assert "## Return Format" in doc, f"{tool.name} docstring missing '## Return Format'"
        assert "## Examples" in doc, f"{tool.name} docstring missing '## Examples'"


def test_browser_help_returns_docs() -> None:
    import asyncio

    from browser_mcp.server import browser_help

    result = asyncio.run(browser_help())
    assert result["success"] is True
    assert "browse_page" in result["help"]


def test_browser_shutdown_requires_confirm() -> None:
    import asyncio

    from browser_mcp.server import browser_shutdown

    result = asyncio.run(browser_shutdown(confirm=False))
    assert result["success"] is False
    assert "confirm" in result["message"].lower()


@pytest.mark.asyncio
async def test_health_route() -> None:
    app = build_app()
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["service"] == "browser-mcp"


@pytest.mark.asyncio
async def test_diagnostics_route() -> None:
    app = build_app()
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/v1/diagnostics")
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert "tools" in body


@pytest.mark.asyncio
async def test_capabilities_route() -> None:
    app = build_app()
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/capabilities")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
        assert r.json()["features"]["browser_automation"] is True


@pytest.mark.asyncio
async def test_skills_route_empty_but_valid() -> None:
    app = build_app()
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/skills")
        assert r.status_code == 200
        assert isinstance(r.json()["skills"], list)


@pytest.mark.asyncio
async def test_llm_chat_rejects_empty_messages() -> None:
    app = build_app()
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/api/llm/chat", json={"messages": []})
        assert r.status_code == 400
