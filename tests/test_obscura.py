"""Offline tests for the optional Obscura fetch engine.

These never hit the network or the engine - they only check the module's
detection API and that the MCP tools accept the `engine` param.
"""

from __future__ import annotations

import pytest

from browser_mcp import obscura


def test_obscura_available_is_bool() -> None:
    assert isinstance(obscura.available(), bool)


def test_obscura_find_binary_returns_str_or_none() -> None:
    result = obscura.find_binary()
    assert result is None or isinstance(result, str)


@pytest.mark.asyncio
async def test_browse_page_accepts_engine_param() -> None:
    import inspect

    from browser_mcp.server import browse_page

    sig = inspect.signature(browse_page)
    assert "engine" in sig.parameters
    assert sig.parameters["engine"].default == "auto"


@pytest.mark.asyncio
async def test_browse_url_cli_accepts_engine_param() -> None:
    import inspect

    from browser_mcp.server import browse_url_cli

    sig = inspect.signature(browse_url_cli)
    assert "engine" in sig.parameters
    assert sig.parameters["engine"].default == "auto"
