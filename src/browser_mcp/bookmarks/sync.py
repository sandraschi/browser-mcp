from typing import Any

from .chromium_common import add_chromium_bookmark, list_chromium_bookmarks
from .firefox.links import add_bookmark as add_firefox
from .firefox.links import list_bookmarks as list_firefox


def _normalize(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for it in items:
        title = it.get("title") or it.get("name")
        url = it.get("url")
        if url:
            out.append({"title": title or url, "url": url})
    return out


async def sync_bookmarks(
    source_browser: str, target_browser: str, dry_run: bool = False, limit: int = 100
) -> dict[str, Any]:
    try:
        if source_browser.lower() in ("chrome", "edge", "brave"):
            result = await list_chromium_bookmarks(source_browser)
        else:
            result = await list_firefox()
        items = result.get("bookmarks", [])
        normalized = _normalize(items)[:limit]
        if dry_run:
            return {
                "success": True,
                "message": f"Would sync {len(normalized)} bookmarks from {source_browser} to {target_browser}",
                "dry_run": True,
                "count": len(normalized),
            }
        synced = 0
        for item in normalized:
            if target_browser.lower() in ("chrome", "edge", "brave"):
                r = await add_chromium_bookmark(target_browser, title=item["title"], url=item["url"])
            else:
                r = await add_firefox(url=item["url"], title=item["title"])
            if r.get("status") == "success":
                synced += 1
        return {"success": True, "message": f"Synced {synced}/{len(normalized)} bookmarks", "count": synced}
    except Exception as e:
        return {"success": False, "error": str(e)}
