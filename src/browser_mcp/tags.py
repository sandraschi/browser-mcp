"""Sidecar tag store for bookmarks.

Browsers (especially Chromium) have no native bookmark tags in the Bookmarks
JSON file. This module provides a small SQLite store keyed by bookmark URL so
the webapp can tag/filter bookmarks. Tags are webapp-side metadata - they do
not appear in the browser itself.

Env override: BROWSER_MCP_DATA_DIR (default `data/` under the repo root).
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from pathlib import Path

DB_PATH = Path(os.environ.get("BROWSER_MCP_DATA_DIR", "data")) / "bookmark_tags.db"
_lock = threading.Lock()


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS tags (url TEXT PRIMARY KEY, tags TEXT NOT NULL)")
    return conn


def _normalize(tags) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for t in tags or []:
        s = str(t).strip().lower()
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return sorted(out)


def get_tags(url: str) -> list[str]:
    with _lock:
        conn = _conn()
        try:
            row = conn.execute("SELECT tags FROM tags WHERE url = ?", (url,)).fetchone()
            return json.loads(row[0]) if row else []
        finally:
            conn.close()


def set_tags(url: str, tags) -> list[str]:
    normalized = _normalize(tags)
    with _lock:
        conn = _conn()
        try:
            if normalized:
                conn.execute(
                    "INSERT INTO tags (url, tags) VALUES (?, ?) ON CONFLICT(url) DO UPDATE SET tags = excluded.tags",
                    (url, json.dumps(normalized)),
                )
            else:
                conn.execute("DELETE FROM tags WHERE url = ?", (url,))
            conn.commit()
            return normalized
        finally:
            conn.close()


def remove_tag(url: str, tag: str) -> list[str]:
    current = get_tags(url)
    updated = [t for t in current if t != str(tag).strip().lower()]
    return set_tags(url, updated)


def list_tags() -> list[dict[str, str | int]]:
    """Aggregate all tags across bookmarks into [{tag, count}] sorted by count desc."""
    counts: dict[str, int] = {}
    with _lock:
        conn = _conn()
        try:
            for (row,) in conn.execute("SELECT tags FROM tags"):
                for t in json.loads(row):
                    counts[t] = counts.get(t, 0) + 1
        finally:
            conn.close()
    return [{"tag": tag, "count": count} for tag, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]


def all_tags_by_url() -> dict[str, list[str]]:
    """Return {url: [tags]} for every tagged bookmark (for bulk UI hydration)."""
    result: dict[str, list[str]] = {}
    with _lock:
        conn = _conn()
        try:
            for url, tjson in conn.execute("SELECT url, tags FROM tags"):
                result[url] = json.loads(tjson)
        finally:
            conn.close()
    return result
