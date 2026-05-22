from typing import Any

from .chromium_common import add_chromium_bookmark, list_chromium_bookmarks
from .firefox.links import add_bookmark as add_firefox
from .firefox.links import list_bookmarks as list_firefox


def _read(browser: str):
    b = browser.lower()
    if b == "firefox":
        return list_firefox
    if b in ("chrome", "edge", "brave"):
        return list_chromium_bookmarks
    raise ValueError(f"Unsupported browser: {browser}")


def _write(browser: str):
    b = browser.lower()
    if b == "firefox":
        return add_firefox
    if b in ("chrome", "edge", "brave"):
        return add_chromium_bookmark
    raise ValueError(f"Unsupported browser: {browser}")


def _normalize(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for it in items:
        title = it.get("title") or it.get("name")
        url = it.get("url")
        if url:
            out.append({"title": title or url, "url": url})
    return out


async def sync_bookmarks(source_browser: str, target_browser: str, dry_run: bool = False, limit: int = 100) -> dict[str, Any]:
    try:
        read_fn = _read(source_browser)
        write_fn = _write(target_browser)
        if source_browser in ("chrome", "edge", "brave"):
            result = await read_fn(source_browser)
            items = result.get("bookmarks", [])
        else:
            result = await read_fn()
            items = result.get("bookmarks", [])
        normalized = _normalize(items)[:limit]
        if dry_run:
            return {"success": True, "message": f"Would sync {len(normalized)} bookmarks from {source_browser} to {target_browser}", "dry_run": True, "count": len(normalized)}
        synced = 0
        for item in normalized:
            if target_browser in ("chrome", "edge", "brave"):
                r = await write_fn(target_browser, title=item["title"], url=item["url"])
            else:
                r = await write_fn(url=item["url"], title=item["title"])
            if r.get("status") == "success":
                synced += 1
        return {"success": True, "message": f"Synced {synced}/{len(normalized)} bookmarks", "count": synced}
    except Exception as e:
        return {"success": False, "error": str(e)}
