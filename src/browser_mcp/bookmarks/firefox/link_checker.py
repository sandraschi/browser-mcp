from pathlib import Path
from typing import Any

import aiohttp

from .db import FirefoxDB


class LinkChecker:
    def __init__(self, profile_path: Path | None = None):
        self.db = FirefoxDB(profile_path)
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.session:
            await self.session.close()

    async def find_broken_links(self, check_links: bool = True) -> dict[str, Any]:
        cursor = self.db.execute("""
            SELECT b.id, b.title, p.url
            FROM moz_bookmarks b
            JOIN moz_places p ON b.fk = p.id
            WHERE b.type = 1 AND p.url IS NOT NULL
        """)
        bookmarks = [dict(row) for row in cursor.fetchall()]
        broken = []
        if not check_links:
            return {"broken_links": [], "count": 0}
        async with aiohttp.ClientSession() as session:
            for bm in bookmarks:
                try:
                    async with session.head(bm["url"], allow_redirects=True, timeout=10) as resp:
                        if resp.status >= 400:
                            broken.append({"bookmark_id": bm["id"], "title": bm["title"], "url": bm["url"], "status": resp.status})
                except Exception:
                    broken.append({"bookmark_id": bm["id"], "title": bm["title"], "url": bm["url"], "error": "Connection failed"})
        return {"broken_links": broken, "count": len(broken)}
