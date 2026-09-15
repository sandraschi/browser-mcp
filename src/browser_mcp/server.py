"""
FastMCP 3.4 server - Browser automation, bookmark management, and AI browsing workflows.

Tools (automation):
  browse_page(url)              - navigate and extract visible text
  click_element(selector)       - click elements by CSS selector
  extract_text(selector)        - extract text from any element
  screenshot()                  - viewport PNG screenshot
  fill_input(selector, text)    - type into input fields
  press_key(key)                - press keyboard keys
  close_browser()               - release Playwright resources
  list_browsers()               - detect installed browsers and profiles
  browse_url_cli(url, browser)  - headless CLI mode (no Playwright overhead)

Tools (bookmarks):
  browser_bookmarks(...)        - 17 operations across Chrome, Firefox, Edge, Brave

Tools (AI workflows):
  browser_agent(task)           - browser-use agentic browsing (LLM-driven)
  morning_briefing(config)      - configurable daily page routine
  browse_items(items_json)      - browse a list of links with structured summaries
  browse_workflow(task)         - multi-step agentic browsing from a natural language task

Tools (system):
  browser_help(topic)           - server documentation
  browser_shutdown(confirm)     - graceful server shutdown
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os

from fastmcp import FastMCP
from fastmcp.server import create_proxy

logger = logging.getLogger(__name__)

# Fire-and-forget tasks kept alive by reference (RUF006)
_bg_tasks: list[asyncio.Task] = []

mcp = FastMCP(
    "browser-mcp",
    instructions="Browser automation and bookmark management - Playwright + CDP + native bookmarks.",
    version="0.3.0",
)

# Register bookmark tools by importing the registration module
# Register Prefab UI cards (in-chat rich UI for list/status tools)
from browser_mcp import prefab_cards  # noqa: F401
from browser_mcp.bookmarks import portmanteau  # noqa: F401

# Register browser-use agentic browsing tool
from browser_mcp.workflows import browser_use_agent  # noqa: F401

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


def _effective_headless(headless: bool | None) -> bool:
    if headless is None:
        cfg = __import__("browser_mcp.config", fromlist=["load_settings"]).load_settings()
        return cfg.headless
    return headless


# ── Tools ─────────────────────────────────────────────────────────────────────


@mcp.tool()
async def browse_page(url: str, headless: bool | None = None, engine: str = "auto") -> dict:
    """BROWSE_PAGE - Navigate to a URL and extract all visible text content.

    Visits the URL (waiting for DOM content), then returns the page title,
    final URL, HTTP status, and visible inner text (first 20K chars).

    engine: "auto" (Obscura fast path when available, else Playwright),
    "obscura" (force Obscura fetch), or "playwright" (force Playwright).

    ## Return Format
    {"success": bool, "title": str, "url": str, "text": str, "status": int, "engine": str}
    On failure: {"success": false, "error": str, "error_type": str}

    ## Examples
    await browse_page(url="https://example.com")
    await browse_page(url="https://example.com", engine="obscura")
    """
    engine = (engine or "auto").lower()
    if engine in ("auto", "obscura"):
        from browser_mcp import obscura

        if obscura.available():
            text = obscura.fetch(url, timeout=30)
            if text is not None:
                lines = text.splitlines()
                title = lines[0][:200] if lines else ""
                return {
                    "success": True,
                    "title": title,
                    "url": url,
                    "text": text[:20000],
                    "status": 200,
                    "engine": "obscura",
                }
        if engine == "obscura":
            return {"success": False, "error": "Obscura unavailable or fetch failed", "error_type": "obscura"}

    headless_eff = _effective_headless(headless)

    try:
        page = await ensure_page(headless=headless_eff)
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
            "engine": "playwright",
        }
    except Exception as exc:
        logger.exception("browse_page failed: %s", exc)
        return {"success": False, "error": str(exc), "error_type": type(exc).__name__}


@mcp.tool()
async def click_element(selector: str, headless: bool | None = None) -> dict:
    """CLICK_ELEMENT - Click an element on the current page by CSS selector.

    ## Return Format
    {"success": bool, "clicked": str, "url": str}
    On failure: {"success": false, "error": str, "error_type": str}

    ## Examples
    await click_element(selector="button#submit")
    await click_element(selector=".nav-link")
    """
    try:
        page = await ensure_page(headless=_effective_headless(headless))
        await page.click(selector)
        await asyncio.sleep(0.5)
        return {"success": True, "clicked": selector, "url": page.url}
    except Exception as exc:
        logger.exception("click_element failed: %s", exc)
        return {"success": False, "error": str(exc), "error_type": type(exc).__name__}


@mcp.tool()
async def extract_text(selector: str = "body", headless: bool | None = None) -> dict:
    """EXTRACT_TEXT - Extract inner text from a CSS selector.

    ## Return Format
    {"success": bool, "text": str, "url": str, "selector": str}
    On failure: {"success": false, "error": str, "error_type": str}

    ## Examples
    await extract_text()
    await extract_text(selector="article.main")
    """
    try:
        page = await ensure_page(headless=_effective_headless(headless))
        text = await page.inner_text(selector)
        return {"success": True, "text": text[:20000], "url": page.url, "selector": selector}
    except Exception as exc:
        logger.exception("extract_text failed: %s", exc)
        return {"success": False, "error": str(exc), "error_type": type(exc).__name__}


@mcp.tool()
async def screenshot(headless: bool | None = None) -> dict:
    """SCREENSHOT - Take a PNG screenshot of the current viewport.

    Returns the image as base64 so hosts can render or save it.

    ## Return Format
    {"success": bool, "screenshot_b64": str, "url": str, "format": "png"}
    On failure: {"success": false, "error": str, "error_type": str}

    ## Examples
    await screenshot()
    await screenshot(headless=False)
    """
    try:
        page = await ensure_page(headless=_effective_headless(headless))
        png_bytes = await page.screenshot(full_page=False)
        b64 = base64.b64encode(png_bytes).decode()
        return {"success": True, "screenshot_b64": b64, "url": page.url, "format": "png"}
    except Exception as exc:
        logger.exception("screenshot failed: %s", exc)
        return {"success": False, "error": str(exc), "error_type": type(exc).__name__}


@mcp.tool()
async def fill_input(selector: str, text: str, headless: bool | None = None) -> dict:
    """FILL_INPUT - Type text into an input field (clears existing value first).

    ## Return Format
    {"success": bool, "selector": str}
    On failure: {"success": false, "error": str, "error_type": str}

    ## Examples
    await fill_input(selector="#search", text="MCP servers")
    """
    try:
        page = await ensure_page(headless=_effective_headless(headless))
        await page.fill(selector, text)
        return {"success": True, "selector": selector}
    except Exception as exc:
        logger.exception("fill_input failed: %s", exc)
        return {"success": False, "error": str(exc), "error_type": type(exc).__name__}


@mcp.tool()
async def press_key(key: str, headless: bool | None = None) -> dict:
    """PRESS_KEY - Press a keyboard key (Enter, Escape, ArrowDown, Tab, etc.).

    ## Return Format
    {"success": bool, "key": str}
    On failure: {"success": false, "error": str, "error_type": str}

    ## Examples
    await press_key(key="Enter")
    await press_key(key="ArrowDown")
    """
    try:
        page = await ensure_page(headless=_effective_headless(headless))
        await page.keyboard.press(key)
        return {"success": True, "key": key}
    except Exception as exc:
        logger.exception("press_key failed: %s", exc)
        return {"success": False, "error": str(exc), "error_type": type(exc).__name__}


@mcp.tool()
async def close_browser() -> dict:
    """CLOSE_BROWSER - Close the browser and release Playwright resources.

    ## Return Format
    {"success": bool, "message": str}

    ## Examples
    await close_browser()
    """
    await close_browser_engine()
    return {"success": True, "message": "Browser closed"}


# ── Browser detection & CLI tools ─────────────────────────────────────────────


@mcp.tool()
async def list_browsers() -> dict:
    """LIST_BROWSERS - Detect installed browsers and available profiles.

    Scans common installation paths for Chrome, Firefox, Edge, and Brave.
    Also reports Firefox profiles from profiles.ini.

    ## Return Format
    {"success": bool, "browsers": {"<name>": {"installed": bool, "path"?: str, "profiles"?: [str]}}}

    ## Examples
    await list_browsers()
    """
    import os as _os

    browsers: dict = {}
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
    try:
        from .bookmarks.firefox.utils import parse_profiles_ini

        profiles = parse_profiles_ini()
        if profiles:
            browsers["firefox"]["profiles"] = list(profiles.keys())
    except Exception:
        logger.warning("list_browsers: could not parse Firefox profiles", exc_info=True)
    return {"success": True, "browsers": browsers}


@mcp.tool()
async def browse_url_cli(url: str, browser: str = "chrome", engine: str = "auto") -> dict:
    """BROWSE_URL_CLI - Navigate to a URL using a headless engine (no Playwright session).

    Prefers the Obscura fast/stealth fetch path when available (engine="auto"
    or "obscura"); otherwise falls back to chrome/firefox headless CLI. Use
    engine="playwright" to force the native browser CLI path.

    ## Return Format
    {"success": bool, "browser": str, "url": str, "text"|"screenshot": str, "engine": str}
    On failure: {"success": false, "error": str}

    ## Examples
    await browse_url_cli(url="https://example.com")
    await browse_url_cli(url="https://example.com", engine="obscura")
    """
    engine = (engine or "auto").lower()
    if engine in ("auto", "obscura"):
        from browser_mcp import obscura

        if obscura.available():
            text = obscura.fetch(url, timeout=30)
            if text is not None:
                return {"success": True, "browser": "obscura", "url": url, "text": text[:20000], "engine": "obscura"}
        if engine == "obscura":
            return {"success": False, "error": "Obscura unavailable or fetch failed", "engine": "obscura"}

    import subprocess
    import tempfile

    browser = browser.lower()
    if browser == "chrome":
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ["chrome", "--headless", "--dump-dom", url],
                capture_output=True,
                text=True,
                timeout=30,
            )
            text = result.stdout[:20000] if result.stdout else (result.stderr or "No output")
            return {"success": True, "browser": "chrome", "url": url, "text": text, "engine": "browser-cli"}
        except FileNotFoundError:
            return {"success": False, "error": "Chrome not found on PATH. Install Chrome or use browse_page instead."}
        except Exception as e:
            logger.warning("browse_url_cli (chrome) failed: %s", e)
            return {"success": False, "error": str(e)}
    elif browser == "firefox":
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            result = await asyncio.to_thread(
                subprocess.run,
                ["firefox", "--headless", "--screenshot", tmp.name, url],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return {"success": True, "browser": "firefox", "url": url, "screenshot": tmp.name, "engine": "browser-cli"}
        except FileNotFoundError:
            return {"success": False, "error": "Firefox not found on PATH. Install Firefox or use browse_page instead."}
        except Exception as e:
            logger.warning("browse_url_cli (firefox) failed: %s", e)
            return {"success": False, "error": str(e)}
    return {"success": False, "error": f"Unsupported browser: {browser}"}


# ── System tools ──────────────────────────────────────────────────────────────


@mcp.tool()
async def browser_help(topic: str = "overview") -> dict:
    """BROWSER_HELP - Server documentation and tool index.

    Topics: overview, automation, bookmarks, workflows, configuration.

    ## Return Format
    {"success": bool, "topic": str, "help": str}

    ## Examples
    await browser_help()
    await browser_help(topic="bookmarks")
    """
    docs = {
        "overview": (
            "browser-mcp: Playwright browser automation + cross-browser bookmark management.\n"
            "Tools: browse_page, click_element, extract_text, screenshot, fill_input, press_key,\n"
            "close_browser, list_browsers, browse_url_cli, browser_bookmarks (17 ops), browser_agent,\n"
            "morning_briefing, browse_items, browse_workflow, browser_help, browser_shutdown.\n"
            "HTTP mode: BROWSER_MCP_PORT=10780 uv run python -m browser_mcp --serve\n"
            "MCP endpoint: http://127.0.0.1:10780/mcp (streamable HTTP)"
        ),
        "automation": (
            "browse_page(url) - navigate and extract visible text\n"
            "click_element(selector) - click by CSS selector\n"
            "extract_text(selector) - inner text of an element\n"
            "screenshot() - viewport PNG as base64\n"
            "fill_input(selector, text) - type into inputs\n"
            "press_key(key) - keyboard keys\n"
            "close_browser() - release Playwright resources"
        ),
        "bookmarks": (
            "browser_bookmarks(operation, browser, ...) - list, get, add, edit, delete, search,\n"
            "sync, dedupe, tags, age analysis, broken-link check, export across chrome/firefox/edge/brave."
        ),
        "workflows": (
            "browser_agent(task) - browser-use agentic browsing with an LLM\n"
            "morning_briefing(config) - daily page routine from JSON config\n"
            "browse_items(items_json) - browse a list of links with summaries\n"
            "browse_workflow(task) - multi-step agentic browsing"
        ),
        "configuration": (
            "BROWSER_MCP_PORT (default 10780), BROWSER_MCP_HOST (127.0.0.1),\n"
            "HEADLESS (true), LLM_BASE_URL (http://127.0.0.1:11434), LLM_MODEL,\n"
            "MCP_BRIDGE_URLS (comma-separated upstream proxies)"
        ),
    }
    body = docs.get(topic.lower(), docs["overview"])
    return {"success": True, "topic": topic, "help": body}


@mcp.tool(annotations={"destructiveHint": True})
async def browser_shutdown(confirm: bool = False) -> dict:
    """BROWSER_SHUTDOWN - Gracefully shut down the browser-mcp server.

    Requires confirm=True to prevent accidental termination. In HTTP mode the
    server process exits after a short delay; in stdio mode the parent client
    closing the stream ends the process.

    ## Return Format
    {"success": bool, "message": str}

    ## Examples
    await browser_shutdown(confirm=True)
    """
    if not confirm:
        return {"success": False, "message": "Set confirm=True to shut down the server."}

    async def _exit() -> None:
        await asyncio.sleep(0.3)
        os._exit(0)

    _shutdown_task = asyncio.create_task(_exit())
    _bg_tasks.append(_shutdown_task)
    return {"success": True, "message": "Server shutting down"}


# Register workflow tools (imported here to avoid circular imports with agentic.py)
from browser_mcp.workflows import (
    agentic,  # noqa: F401
    briefing,  # noqa: F401
    link_processor,  # noqa: F401
)
