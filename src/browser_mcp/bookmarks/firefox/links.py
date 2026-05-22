import sqlite3
from datetime import datetime
from typing import Any

from .utils import get_places_db_path


async def list_bookmarks(profile_name: str | None = None, folder_id: int | None = None, limit: int = 50, offset: int = 0) -> dict[str, Any]:
    places_db = get_places_db_path(profile_name)
    if not places_db or not places_db.exists():
        return {"status": "error", "message": f"Could not find Firefox bookmarks database for profile: {profile_name or 'default'}"}
    try:
        conn = sqlite3.connect(f"file:{places_db}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
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
        query += " ORDER BY b.dateAdded DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cursor.execute(query, params)
        bookmarks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return {"status": "success", "bookmarks": bookmarks, "count": len(bookmarks)}
    except sqlite3.Error as e:
        return {"status": "error", "message": f"Database error: {e}"}


async def get_bookmark(bookmark_id: int, profile_name: str | None = None) -> dict[str, Any]:
    places_db = get_places_db_path(profile_name)
    if not places_db or not places_db.exists():
        return {"status": "error", "message": "Database not found"}
    try:
        conn = sqlite3.connect(f"file:{places_db}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.id, b.title, p.url, b.dateAdded, b.lastModified, b.parent
            FROM moz_bookmarks b
            JOIN moz_places p ON b.fk = p.id
            WHERE b.id = ?
        """, (bookmark_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {"status": "success", "bookmark": dict(row)}
        return {"status": "error", "message": "Bookmark not found"}
    except sqlite3.Error as e:
        return {"status": "error", "message": f"Database error: {e}"}


async def add_bookmark(url: str, title: str | None = None, profile_name: str | None = None, tags: list[str] | None = None) -> dict[str, Any]:
    places_db = get_places_db_path(profile_name)
    if not places_db or not places_db.exists():
        return {"status": "error", "message": "Database not found"}
    try:
        conn = sqlite3.connect(str(places_db))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("INSERT INTO moz_places (url, title, rev_host, visit_count) VALUES (?, ?, ?, 1)",
                      (url, title or "", "dummy"))
        place_id = cursor.lastrowid
        now = int(datetime.now().timestamp() * 1000000)
        cursor.execute("INSERT INTO moz_bookmarks (type, fk, parent, position, title, dateAdded, lastModified) VALUES (1, ?, (SELECT id FROM moz_bookmarks WHERE type=2 AND title='toolbar' LIMIT 1), 0, ?, ?, ?)",
                      (place_id, title or "", now, now))
        bookmark_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return {"status": "success", "bookmark_id": bookmark_id, "url": url, "title": title}
    except sqlite3.Error as e:
        return {"status": "error", "message": f"Database error: {e}"}
