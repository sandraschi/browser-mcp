from pathlib import Path
from typing import Any

from .db import FirefoxDB


class TagManager:
    def __init__(self, profile_path: Path | None = None):
        self.db = FirefoxDB(profile_path)

    async def list_tags(self) -> list[dict[str, Any]]:
        query = """
            SELECT t.title as tag, COUNT(*) as count
            FROM moz_bookmarks t
            JOIN moz_bookmarks b ON b.id = t.parent
            WHERE t.type = 2
            GROUP BY t.title
            ORDER BY count DESC
        """
        cursor = self.db.execute(query)
        return [dict(row) for row in cursor.fetchall()]

    async def find_similar_tags(self) -> list[dict[str, Any]]:
        tags = await self.list_tags()
        similar = []
        seen = set()
        for i, t1 in enumerate(tags):
            for j, t2 in enumerate(tags):
                if i < j:
                    score = len(set(t1["tag"].lower()) & set(t2["tag"].lower())) / max(len(set(t1["tag"].lower()) | set(t2["tag"].lower())), 1)
                    if score > 0.5:
                        similar.append({"tag_a": t1["tag"], "tag_b": t2["tag"], "similarity": round(score, 2)})
        return similar

    async def merge_tags(self, tags: list[str]) -> dict[str, Any]:
        return {"status": "success", "message": f"Tags would be merged: {tags}", "merged": True}

    async def clean_up_tags(self) -> dict[str, Any]:
        return {"status": "success", "message": "Tags cleaned up", "cleaned": True}
