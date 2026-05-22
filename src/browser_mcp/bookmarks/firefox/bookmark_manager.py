from pathlib import Path
from typing import Any

from .db import FirefoxDB
from .exceptions import FirefoxNotClosedError
from .status import FirefoxStatusChecker


class BookmarkManager:
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

    def get_bookmarks(self, folder_id: int | None = None) -> list[dict[str, Any]]:
        db = self._get_db_connection()
        query = """
            SELECT b.id, b.title, p.url, b.dateAdded, b.lastModified, b.parent
            FROM moz_bookmarks b
            JOIN moz_places p ON b.fk = p.id
            WHERE b.type = 1
        """
        params = []
        if folder_id is not None:
            query += " AND b.parent = ?"
            params.append(folder_id)
        cursor = db.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    async def list_bookmarks(self, folder_id: int | None = None) -> list[dict[str, Any]]:
        return self.get_bookmarks(folder_id)

    async def get_bookmark(self, bookmark_id: int) -> dict[str, Any] | None:
        db = self._get_db_connection()
        cursor = db.execute(
            "SELECT b.id, b.title, p.url, b.dateAdded, b.lastModified, b.parent "
            "FROM moz_bookmarks b JOIN moz_places p ON b.fk = p.id "
            "WHERE b.type = 1 AND b.id = ?",
            (bookmark_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    async def add_bookmark(self, url: str, title: str | None, tags: list[str] | None = None) -> int:
        db = self._get_db_connection()
        from .links import add_bookmark as add_link
        result = await add_link(url=url, title=title, profile_name=str(self.profile_path) if self.profile_path else None)
        return result.get("bookmark_id", 0)
