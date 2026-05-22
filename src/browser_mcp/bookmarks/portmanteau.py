import logging
from typing import Any

from browser_mcp.server import mcp

from .chromium_common import (
    add_chromium_bookmark,
    delete_chromium_bookmark_entry,
    edit_chromium_bookmark_entry,
    list_chromium_bookmarks,
)
from .firefox_bookmarks import firefox_bookmarks as ff_bookmarks
from .sync import sync_bookmarks

logger = logging.getLogger(__name__)


@mcp.tool()
async def browser_bookmarks(
    operation: str = "list_bookmarks",
    browser: str = "chrome",
    profile_name: str | None = None,
    folder_id: int | None = None,
    bookmark_id: str | None = None,
    url: str | None = None,
    title: str | None = None,
    folder: str | None = None,
    new_title: str | None = None,
    new_folder: str | None = None,
    tags: list[str] | None = None,
    search_query: str | None = None,
    search_type: str = "all",
    limit: int = 100,
    export_format: str = "json",
    export_path: str | None = None,
    batch_size: int = 100,
    similarity_threshold: float = 0.85,
    age_days: int = 365,
    check_links: bool = False,
    allow_duplicates: bool = False,
    create_folders: bool = True,
    dry_run: bool = False,
    target_browser: str | None = None,
    force_access: bool = False,
) -> dict[str, Any]:
    """BROWSER_BOOKMARKS — Universal bookmark management across Chrome, Firefox, Edge, and Brave.

    Operations: list_bookmarks, get_bookmark, add_bookmark, edit_bookmark, delete_bookmark,
    search/search_bookmarks, sync_bookmarks, find_duplicates, export_bookmarks, list_tags,
    find_old_bookmarks, find_forgotten_bookmarks, get_bookmark_stats, find_broken_links.

    Browsers: firefox, chrome, edge, brave.

    ## Return Format
    {"success": bool, "browser": str, "operation": str, ... operation-specific fields}

    ## Examples
    await browser_bookmarks(operation="list_bookmarks", browser="firefox")
    await browser_bookmarks(operation="add_bookmark", browser="chrome", url="https://example.com", title="Example")
    """
    limit = max(1, min(limit, 10_000))
    browser_lower = browser.lower()

    if operation == "sync_bookmarks":
        if not target_browser:
            return {"success": False, "error": "sync_bookmarks requires 'target_browser' parameter"}
        return await sync_bookmarks(source_browser=browser, target_browser=target_browser, dry_run=dry_run, limit=limit)

    if browser_lower == "firefox":
        ff_operation = "search_bookmarks" if operation == "search" else operation
        result = await ff_bookmarks(
            operation=ff_operation, profile_name=profile_name, folder_id=folder_id,
            bookmark_id=int(bookmark_id) if bookmark_id and bookmark_id.isdigit() else None,
            url=url, title=title, tags=tags, search_query=search_query, search_type=search_type,
            export_format=export_format, export_path=export_path, batch_size=batch_size,
            similarity_threshold=similarity_threshold, age_days=age_days, check_links=check_links,
            force_access=force_access,
        )
        result["browser"] = "firefox"
        result["operation"] = operation
        return result

    if browser_lower in ("chrome", "edge", "brave"):
        if operation == "list_bookmarks":
            result = await list_chromium_bookmarks(browser_lower)
            result["browser"] = browser_lower
            result["operation"] = operation
            if "bookmarks" in result:
                result["total_count"] = len(result["bookmarks"])
                result["bookmarks"] = result["bookmarks"][:limit]
                result["returned_count"] = len(result["bookmarks"])
                result["pagination"] = {"limit": limit, "offset": 0, "has_more": result["total_count"] > result["returned_count"], "total_count": result["total_count"]}
            return result

        elif operation in ("add_bookmark"):
            if not url or not title:
                return {"success": False, "browser": browser_lower, "operation": operation, "error": "add_bookmark requires 'url' and 'title'"}
            result = await add_chromium_bookmark(browser_lower, title=title, url=url, folder=folder)
            result["browser"] = browser_lower
            result["operation"] = operation
            return result

        elif operation == "edit_bookmark":
            if not bookmark_id and not url:
                return {"success": False, "browser": browser_lower, "operation": operation, "error": "edit_bookmark requires 'bookmark_id' or 'url'"}
            result = await edit_chromium_bookmark_entry(browser_lower, id=bookmark_id, url=url, new_title=new_title, new_folder=new_folder, allow_duplicates=allow_duplicates, create_folders=create_folders, dry_run=dry_run)
            result["browser"] = browser_lower
            result["operation"] = operation
            return result

        elif operation == "delete_bookmark":
            if not bookmark_id and not url:
                return {"success": False, "browser": browser_lower, "operation": operation, "error": "delete_bookmark requires 'bookmark_id' or 'url'"}
            result = await delete_chromium_bookmark_entry(browser_lower, id=bookmark_id, url=url, dry_run=dry_run)
            result["browser"] = browser_lower
            result["operation"] = operation
            return result

        elif operation in ("search", "search_bookmarks"):
            if not search_query:
                return {"success": False, "browser": browser_lower, "operation": operation, "error": "search requires 'search_query'"}
            result = await list_chromium_bookmarks(browser_lower)
            bookmarks = result.get("bookmarks", [])
            query_lower = search_query.lower()
            matches = [b for b in bookmarks if query_lower in (b.get("title", "") or "").lower() or query_lower in (b.get("url", "") or "").lower()]
            return {"success": True, "browser": browser_lower, "operation": operation, "query": search_query, "results": matches[:limit], "total_matches": len(matches), "returned_count": min(len(matches), limit)}

        elif operation == "get_bookmark":
            if not bookmark_id and not url:
                return {"success": False, "browser": browser_lower, "operation": operation, "error": "get_bookmark requires 'bookmark_id' or 'url'"}
            result = await list_chromium_bookmarks(browser_lower)
            bookmarks = result.get("bookmarks", [])
            for b in bookmarks:
                if (bookmark_id and b.get("id") == bookmark_id) or (url and b.get("url") == url):
                    return {"success": True, "browser": browser_lower, "operation": operation, "bookmark": b}
            return {"success": False, "browser": browser_lower, "operation": operation, "error": f"Bookmark not found: {bookmark_id or url}"}

        else:
            return {"success": False, "browser": browser_lower, "operation": operation, "error": f"Operation '{operation}' not supported for {browser_lower}", "supported_operations": ["list_bookmarks", "add_bookmark", "edit_bookmark", "delete_bookmark", "get_bookmark", "search"], "note": "For advanced operations (duplicates, tags, export), use browser='firefox'"}

    return {"success": False, "operation": operation, "browser": browser, "error": f"Unknown browser type: {browser}", "supported_browsers": ["firefox", "chrome", "edge", "brave"]}
