"""
FastMCP 3.2 server — Browser automation, bookmark management, and AI browsing workflows.

Tools (automation):
  browse_page(url)              — navigate and extract visible text
  click_element(selector)       — click elements by CSS selector
  extract_text(selector)        — extract text from any element
  screenshot()                  — viewport PNG screenshot
  fill_input(selector, text)    — type into input fields
  press_key(key)                — press keyboard keys
  close_browser()               — release Playwright resources
  list_browsers()               — detect installed browsers and profiles
  browse_url_cli(url, browser)  — headless CLI mode (no Playwright overhead)

Tools (bookmarks):
  browser_bookmarks(...)        — 17 operations across Chrome, Firefox, Edge, Brave

Tools (AI workflows):
  morning_briefing(config)      — configurable daily page routine
  browse_items(items_json)      — browse a list of links with structured summaries
  browse_workflow(task)         — multi-step agentic browsing from a natural language task
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os

from fastmcp import FastMCP
from fastmcp.server import create_proxy

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "browser-mcp",
    instructions="Browser automation and bookmark management — Playwright + CDP + native bookmarks.",
    version="0.3.0",
)

# Register bookmark and workflow tools by importing the registration modules
from browser_mcp.bookmarks import portmanteau  # noqa: F401, E402
from browser_mcp.workflows import agentic, briefing, link_processor  # noqa: F401, E402

# MCP Bridge: proxy to external MCP servers via MCP_BRIDGE_URLS env var
_bridge_urls = os.environ.get("MCP_BRIDGE_URLS", "")
if _bridge_urls:
    for _bu in _bridge_urls.split(","):
        _bu = _bu.strip()
        if _bu:
            mcp.add_provider(create_proxy(_bu))

# ── Browser lifecycle (delegated to browser.py) ──────────────────────────────

from browser_mcp.browser import close as close_browser_engine
from browser_mcp.browser import ensure_page

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
        page = await ensure_page(headless=headless)
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
        page = await ensure_page(headless=headless)
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
        page = await ensure_page(headless=headless)
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
        page = await ensure_page(headless=headless)
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
        page = await ensure_page(headless=headless)
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
        page = await ensure_page(headless=headless)
        await page.keyboard.press(key)
        return {"success": True, "key": key}
    except Exception as exc:
        logger.error("press_key failed: %s", exc)
        return {"success": False, "error": str(exc), "error_type": type(exc).__name__}


@mcp.tool()
async def close_browser() -> dict:
    """CLOSE_BROWSER — Close the browser and release resources."""
    await close_browser_engine()
    return {"success": True, "message": "Browser closed"}


# ── Browser detection & CLI tools ─────────────────────────────────────────────


@mcp.tool()
async def list_browsers() -> dict:
    """LIST_BROWSERS — Detect installed browsers and available profiles.

    Scans common installation paths for Chrome, Firefox, Edge, and Brave.
    Also reports Firefox profiles from profiles.ini.

    Returns:
        dict with installed browsers and their paths.
    """
    import os as _os

    browsers = {}
    # Check common paths
    checks = {
        "chrome": [r"Google\Chrome\Application\chrome.exe", r"Google\Chrome SxS\Application\chrome.exe"],
        "firefox": [r"Mozilla Firefox\firefox.exe"],
        "edge": [r"Microsoft\Edge\Application\msedge.exe"],
        "brave": [r"BraveSoftware\Brave-Browser\Application\brave.exe"],
    }
    pf = _os.environ.get("ProgramFiles", "") or r"C:\Program Files"
    pf86 = _os.environ.get("ProgramFiles(x86)", "") or r"C:\Program Files (x86)"
    for name, paths in checks.items():
        found = None
        for p in paths:
            for base in [pf, pf86]:
                full = _os.path.join(base, p)
                if _os.path.exists(full):
                    found = full
                    break
            if found:
                break
        if found:
            browsers[name] = {"path": found, "installed": True}
        else:
            browsers[name] = {"installed": False}
    # Firefox profiles
    try:
        from .bookmarks.firefox.utils import parse_profiles_ini
        profiles = parse_profiles_ini()
        if profiles:
            browsers["firefox"]["profiles"] = list(profiles.keys())
    except Exception:
        pass
    return {"success": True, "browsers": browsers}


@mcp.tool()
async def browse_url_cli(url: str, browser: str = "chrome") -> dict:
    """BROWSE_URL_CLI — Navigate to a URL using headless CLI (no Playwright).

    Uses chrome --headless --dump-dom or firefox --screenshot for quick
    operations without the overhead of a full Playwright browser session.

    Args:
        url: The URL to visit.
        browser: 'chrome' or 'firefox' (default chrome).

    Returns:
        Extracted text content (Chrome) or screenshot path (Firefox).
    """
    import subprocess
    import tempfile

    browser = browser.lower()
    if browser == "chrome":
        try:
            result = subprocess.run(
                ["chrome", "--headless", "--dump-dom", url],
                capture_output=True, text=True, timeout=30,
            )
            text = result.stdout[:20000] if result.stdout else (result.stderr or "No output")
            return {"success": True, "browser": "chrome", "url": url, "text": text}
        except FileNotFoundError:
            return {"success": False, "error": "Chrome not found on PATH. Install Chrome or use browse_page instead."}
        except Exception as e:
            return {"success": False, "error": str(e)}
    elif browser == "firefox":
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            result = subprocess.run(
                ["firefox", "--headless", "--screenshot", tmp.name, url],
                capture_output=True, text=True, timeout=30,
            )
            return {"success": True, "browser": "firefox", "url": url, "screenshot": tmp.name}
        except FileNotFoundError:
            return {"success": False, "error": "Firefox not found on PATH. Install Firefox or use browse_page instead."}
        except Exception as e:
            return {"success": False, "error": str(e)}
    return {"success": False, "error": f"Unsupported browser: {browser}"}
