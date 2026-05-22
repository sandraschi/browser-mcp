from pathlib import Path
from typing import Any

from .db import FirefoxDB
from .exceptions import FirefoxNotClosedError
from .status import FirefoxStatusChecker


class BookmarkSearcher:
    def __init__(self, profile_path: Path | None = None):
        self.profile_path = profile_path
        self.db = None

    def _ensure_safe_access(self) -> dict[str, Any]:
        return FirefoxStatusChecker.check_database_access_safe(self.profile_path)

    def _get_db_connection(self) -> FirefoxDB:
        if self.db is None:
            safety_check = self._ensure_safe_access()
            if not safety_check["safe"]:
                raise FirefoxNotClosedError(safety_check["message"])
            self.db = FirefoxDB(self.profile_path)
        return self.db

    async def search_bookmarks(self, query: str, search_type: str = "all") -> list[dict[str, Any]]:
        db = self._get_db_connection()
        search_term = f"%{query}%"
        sql = """
            SELECT b.id, b.title, p.url, b.dateAdded, b.lastModified, b.parent
            FROM moz_bookmarks b
            JOIN moz_places p ON b.fk = p.id
            WHERE b.type = 1 AND (b.title LIKE ? OR p.url LIKE ?)
            LIMIT 100
        """
        cursor = db.execute(sql, (search_term, search_term))
        return [dict(row) for row in cursor.fetchall()]

    async def find_duplicates(self, similarity_threshold: float = 0.85) -> list[dict[str, Any]]:
        db = self._get_db_connection()
        cursor = db.execute("""
            SELECT p.url, GROUP_CONCAT(b.id) as ids, COUNT(*) as count
            FROM moz_bookmarks b
            JOIN moz_places p ON b.fk = p.id
            WHERE b.type = 1
            GROUP BY p.url
            HAVING COUNT(*) >= 2
            ORDER BY count DESC
        """)
        results = []
        for row in cursor.fetchall():
            item = dict(row)
            item["ids"] = [int(x) for x in item["ids"].split(",")]
            results.append(item)
        return results
