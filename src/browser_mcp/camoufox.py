"""Optional Camoufox stealth-render engine.

Camoufox (https://github.com/daijro/camoufox) is a Firefox fork with
fingerprint rotation built for scraping: every launch gets a fresh identity
drawn from real-world device distributions, so it blends into normal traffic
where vanilla Playwright gets challenged. It speaks the Playwright API, so
this module mirrors ``obscura.py``: same never-raise contract, same
``available()`` / ``fetch()`` shape, one more rung on the engine ladder.

The package is optional: ``available()`` returns False when it is not
installed, and callers fall back (Obscura / Playwright). Never raise when the
package or the browser binary is missing - degrade gracefully and let the
caller try the next engine.

Install (one time): ``uv sync --extra stealth`` then ``python -m camoufox fetch``.
Env override: CAMOUFOX_HEADLESS=0 runs headful (virtual display on servers).
"""

from __future__ import annotations

import importlib.util
import logging
import os

logger = logging.getLogger(__name__)

_package: bool | None = None


def available() -> bool:
    """True when the ``camoufox`` package imports (binary may still need fetch)."""
    global _package
    if _package is None:
        _package = importlib.util.find_spec("camoufox") is not None
    return _package


def install_hint() -> str:
    return "uv sync --extra stealth; python -m camoufox fetch"


async def fetch(url: str, timeout: int = 30) -> tuple[str, str] | None:
    """Render a page with Camoufox. Returns (title, html), or None on any failure."""
    if not available():
        return None
    try:
        from camoufox.async_api import AsyncCamoufox
    except ImportError as exc:
        logger.warning("camoufox import failed (packages half-installed?): %s", exc)
        return None
    headless = os.environ.get("CAMOUFOX_HEADLESS", "1") != "0"
    try:
        async with AsyncCamoufox(headless=headless) as browser:
            page = await browser.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=max(timeout, 5) * 1000)
            try:
                await page.wait_for_timeout(1500)
            except Exception as exc:
                logger.debug("camoufox settle-wait skipped: %s", exc)
            html = await page.content()
            try:
                title = await page.title()
            except Exception:
                title = ""
            if not html:
                return None
            return (title or ""), html
    except Exception as exc:
        msg = str(exc)
        if "Executable doesn't exist" in msg or ("fetch" in msg.lower() and "camoufox" in msg.lower()):
            logger.warning("camoufox browser binary missing - run `python -m camoufox fetch` once")
        else:
            logger.warning("camoufox fetch failed for %s: %s", url[:120], exc)
        return None
