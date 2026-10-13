"""Polite httpx fast path for read-only page fetching.

Sits below the browser engines on the cost ladder: plain HTTP GET with a
fleet user-agent, redirect following, and a 2MB cap. Most pages (RSS article
bodies, docs, DDG lite) never need a browser - this answers them in
milliseconds. When the response smells like a bot challenge, callers escalate
to Obscura / Camoufox / Playwright instead of parsing garbage.

Never raise for transport failures - ``fetch()`` returns None and the caller
tries the next rung. Raises ValueError only for non-http(s) URLs.
"""

from __future__ import annotations

import logging
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

POLITE_UA = "browser-mcp/0.3 fastfetch (fleet polite fetch)"
MAX_HTML_BYTES = 2_000_000

BLOCKED_MARKERS = (
    "anomaly-modal",
    "challenge-form",
    "just a moment",
    "attention required",
    "are you a robot",
    "not a robot",
    "captcha",
    "cloudflare",
)


def valid_url(url: str) -> str:
    u = (url or "").strip()
    parts = urlparse(u)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise ValueError(f"refusing non-http(s) URL: {u[:120]}")
    return u


def looks_blocked(status: int, html: str) -> bool:
    if status in (401, 403, 429, 503):
        return True
    return any(m in (html or "").lower() for m in BLOCKED_MARKERS)


def extract(html: str, max_chars: int = 20000) -> tuple[str, str]:
    """Return (title, text) from raw HTML. Chrome-style: article/main/body."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html or "", "lxml")
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
        tag.decompose()
    main = soup.find("article") or soup.find("main") or soup.body or soup
    text = " ".join(main.get_text(" ", strip=True).split())
    return title[:300], text[: max(1, max_chars)]


async def fetch(url: str, timeout: float = 20.0) -> tuple[int, str] | None:
    """GET a page. Returns (status, html), or None on transport failure."""
    try:
        target = valid_url(url)
    except ValueError:
        raise
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(min(timeout, 25.0), connect=8.0),
            headers={"User-Agent": POLITE_UA},
            follow_redirects=True,
        ) as client:
            resp = await client.get(target)
            html = resp.text or ""
            if len(html.encode("utf-8", "ignore")) > MAX_HTML_BYTES:
                html = html[:MAX_HTML_BYTES]
            return resp.status_code, html
    except Exception as exc:
        logger.debug("fastfetch failed for %s: %s", url[:120], exc)
        return None
