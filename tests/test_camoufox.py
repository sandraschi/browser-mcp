"""Offline tests for the Camoufox engine + httpx fast path.

Never hit the network or launch a browser - detection API, signature checks,
and pure parse/blocked helpers only.
"""

from __future__ import annotations

import pytest

from browser_mcp import camoufox, fastfetch


def test_camoufox_available_is_bool() -> None:
    assert isinstance(camoufox.available(), bool)


def test_camoufox_install_hint_mentions_fetch() -> None:
    assert "camoufox fetch" in camoufox.install_hint()


def test_fastfetch_valid_url_rejects_non_http() -> None:
    with pytest.raises(ValueError):
        fastfetch.valid_url("file:///etc/passwd")
    with pytest.raises(ValueError):
        fastfetch.valid_url("not a url")


def test_fastfetch_valid_url_accepts_http() -> None:
    assert fastfetch.valid_url("https://example.com/a") == "https://example.com/a"


def test_fastfetch_blocked_markers() -> None:
    assert fastfetch.looks_blocked(403, "<html>ok</html>")
    assert fastfetch.looks_blocked(200, "<div class='anomaly-modal'>robot?</div>")
    assert fastfetch.looks_blocked(200, "<title>Just a moment...</title>")
    assert not fastfetch.looks_blocked(200, "<html><body>hello</body></html>")


def test_fastfetch_extract_static_html() -> None:
    pytest.importorskip("bs4")
    html = "<html><head><title>T</title></head><body><article><p>Hello world</p></article></body></html>"
    title, text = fastfetch.extract(html)
    assert title == "T"
    assert "Hello world" in text


@pytest.mark.asyncio
async def test_browse_page_accepts_engine_and_html_params() -> None:
    import inspect

    from browser_mcp.server import browse_page

    sig = inspect.signature(browse_page)
    assert sig.parameters["engine"].default == "auto"
    assert sig.parameters["include_html"].default is False
