"""
FastMCP 3.2 server — Playwright browser automation tools.

Tools:
  browse_page(url)        — fetch page content as markdown-like text
  click_element(selector) — click an element on the current page
  extract_text(selector)  — extract text from an element
  screenshot()            — take a viewport screenshot, return base64
  fill_input(selector, text) — type text into an input field
  press_key(key)          — press a keyboard key
"""

from __future__ import annotations

import asyncio
import base64
import logging

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "browser-mcp",
    instructions="Playwright browser automation — browse, click, screenshot, extract text from web pages.",
    version="0.1.0",
)

# ── Browser lifecycle ─────────────────────────────────────────────────────────

_playwright = None
_browser = None
_page = None
_lock: asyncio.Lock | None = None


def _get_lock() -> asyncio.Lock:
    global _lock
    if _lock is None:
        _lock = asyncio.Lock()
    return _lock


async def _ensure_page(headless: bool = True):
    """Start (or reuse) a browser + page. Idempotent."""
    global _playwright, _browser, _page

    if _page:
        try:
            await _page.title()
            return _page
        except Exception:
            await _close()

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


async def _close():
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


# ── Tools ─────────────────────────────────────────────────────────────────────


@mcp.tool()
async def browse_page(url: str, headless: bool | None = None) -> dict:
    """BROWSE_PAGE — Navigate to a URL and extract all visible text content.

    Args:
        url: The full URL to visit (https://...).
        headless: Run browser headless (default: True). Set False to see the window.

    Returns:
        Page title, URL, visible text content (first 20K chars), and HTTP status.
    """
    cfg = __import__("browser_mcp.config", fromlist=["load_settings"]).load_settings()
    headless = headless if headless is not None else cfg.headless

    try:
        page = await _ensure_page(headless=headless)
        resp = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(1)

        title = await page.title()
        body_text = await page.evaluate("() => document.body?.innerText || ''")
        status = resp.status if resp else 0

        return {
            "success": True,
            "title": title,
            "url": page.url,
            "text": body_text[:20000],
            "status": status,
        }
    except Exception as exc:
        logger.error("browse_page failed: %s", exc)
        return {"success": False, "error": str(exc), "error_type": type(exc).__name__}


@mcp.tool()
async def click_element(selector: str, headless: bool | None = None) -> dict:
    """CLICK_ELEMENT — Click an element on the current page by CSS selector.

    Args:
        selector: CSS selector (e.g. 'button#submit', '.nav-link', 'a[href*="login"]').

    Returns:
        success, clicked selector, optional error.
    """
    try:
        page = await _ensure_page(headless=headless)
        await page.click(selector)
        await asyncio.sleep(0.5)
        return {"success": True, "clicked": selector, "url": page.url}
    except Exception as exc:
        logger.error("click_element failed: %s", exc)
        return {"success": False, "error": str(exc), "error_type": type(exc).__name__}


@mcp.tool()
async def extract_text(selector: str = "body", headless: bool | None = None) -> dict:
    """EXTRACT_TEXT — Extract inner text from a CSS selector.

    Args:
        selector: CSS selector (default 'body').

    Returns:
        The text content (first 20K chars), and the URL.
    """
    try:
        page = await _ensure_page(headless=headless)
        text = await page.inner_text(selector)
        return {"success": True, "text": text[:20000], "url": page.url, "selector": selector}
    except Exception as exc:
        logger.error("extract_text failed: %s", exc)
        return {"success": False, "error": str(exc), "error_type": type(exc).__name__}


@mcp.tool()
async def screenshot(headless: bool | None = None) -> dict:
    """SCREENSHOT — Take a PNG screenshot of the current viewport.

    Returns:
        Base64-encoded PNG and the current URL.
    """
    try:
        page = await _ensure_page(headless=headless)
        png_bytes = await page.screenshot(full_page=False)
        b64 = base64.b64encode(png_bytes).decode()
        return {"success": True, "screenshot_b64": b64, "url": page.url, "format": "png"}
    except Exception as exc:
        logger.error("screenshot failed: %s", exc)
        return {"success": False, "error": str(exc), "error_type": type(exc).__name__}


@mcp.tool()
async def fill_input(selector: str, text: str, headless: bool | None = None) -> dict:
    """FILL_INPUT — Type text into an input field (clears existing value first).

    Args:
        selector: CSS selector for the input field.
        text: The text to type.

    Returns:
        success status.
    """
    try:
        page = await _ensure_page(headless=headless)
        await page.fill(selector, text)
        return {"success": True, "selector": selector}
    except Exception as exc:
        logger.error("fill_input failed: %s", exc)
        return {"success": False, "error": str(exc), "error_type": type(exc).__name__}


@mcp.tool()
async def press_key(key: str, headless: bool | None = None) -> dict:
    """PRESS_KEY — Press a keyboard key (Enter, Escape, ArrowDown, Tab, etc.).

    Args:
        key: Playwright key name (e.g. 'Enter', 'Escape', 'Tab', 'ArrowDown').

    Returns:
        success status.
    """
    try:
        page = await _ensure_page(headless=headless)
        await page.keyboard.press(key)
        return {"success": True, "key": key}
    except Exception as exc:
        logger.error("press_key failed: %s", exc)
        return {"success": False, "error": str(exc), "error_type": type(exc).__name__}


@mcp.tool()
async def close_browser() -> dict:
    """CLOSE_BROWSER — Close the browser and release resources."""
    await _close()
    return {"success": True, "message": "Browser closed"}
