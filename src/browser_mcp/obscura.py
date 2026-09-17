"""Optional Obscura fetch engine.

Obscura (https://github.com/h4ckf0r0day/obscura) is the fleet's Rust-native
stealth headless browser. It is a *fetch/scrape* engine, not a full automation
driver. This module provides a lightweight subprocess wrapper used as a fast,
stealth alternative to Playwright for read-only page fetching.

The engine binary is optional: `available()` returns False when it is not
built, and callers fall back to Playwright. Never raise when the binary is
missing - degrade gracefully.

Env override: OBSCURA_BIN points at the obscura executable directly.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

_CANDIDATE_PATHS = [
    Path(os.environ.get("OBSCURA_BIN", "")),
    Path(r"D:\Dev\repos\external\obscura\target\release\obscura.exe"),
    Path(r"D:\Dev\repos\external\obscura\target\debug\obscura.exe"),
    Path(r"D:\Dev\repos\external\obscura\obscura.exe"),
]

_binary: str | None = None
_probed = False


def find_binary() -> str | None:
    """Return the obscura executable path, or None if unavailable."""
    global _binary, _probed
    if _probed:
        return _binary
    for p in _CANDIDATE_PATHS:
        if p and p.is_file():
            _binary = str(p)
            break
    if _binary is None:
        _binary = shutil.which("obscura")
    _probed = True
    return _binary


def available() -> bool:
    """True when the Obscura engine binary can be executed."""
    return find_binary() is not None


def fetch(url: str, dump: str = "text", timeout: int = 30) -> str | None:
    """Fetch a page's text via Obscura. Returns text, or None on any failure."""
    binary = find_binary()
    if not binary:
        return None
    cmd = [binary, "fetch", url, "--dump", dump, "--timeout", str(timeout)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)
    except Exception as exc:
        logger.warning("obscura fetch error: %s", exc)
        return None
    if result.returncode != 0:
        logger.warning("obscura fetch rc=%s: %s", result.returncode, (result.stderr or "").strip()[:200])
        return None
    text = (result.stdout or "").strip()
    return text or None
