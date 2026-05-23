from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)

_playwright = None
_browser = None
_page = None
_lock: asyncio.Lock | None = None


def _get_lock() -> asyncio.Lock:
    global _lock
    if _lock is None:
        _lock = asyncio.Lock()
    return _lock


async def ensure_page(headless: bool = True):
    global _playwright, _browser, _page

    if _page:
        try:
            await _page.title()
            return _page
        except Exception:
            await close()

    from playwright.async_api import async_playwright

    _playwright = await async_playwright().start()
    _browser = await _playwright.chromium.launch(
        headless=headless,
        args=["--disable-blink-features=AutomationControlled"],
    )
    context = await _browser.new_context(
        viewport={"width": 1280, "height": 720},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
    )
    _page = await context.new_page()
    return _page


async def close():
    global _playwright, _browser, _page
    try:
        if _browser:
            await _browser.close()
        if _playwright:
            await _playwright.stop()
    except Exception as exc:
        logger.warning("browser close error: %s", exc)
    finally:
        _playwright = None
        _browser = None
        _page = None
