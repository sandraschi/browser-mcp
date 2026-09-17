import logging
from typing import Any

from browser_mcp import tags as tag_store
from browser_mcp.server import mcp

from .chromium_common import (
    add_chromium_bookmark,
    check_url_exists,
    delete_chromium_bookmark_entry,
    edit_chromium_bookmark_entry,
    list_chromium_bookmarks,
)
from .firefox_bookmarks import firefox_bookmarks as ff_bookmarks
from .sync import sync_bookmarks

logger = logging.getLogger(__name__)


async def chromium_stats(browser: str) -> dict[str, Any]:
    result = await list_chromium_bookmarks(browser)
    if "bookmarks" not in result:
        result.update({"success": False, "browser": browser, "operation": "get_bookmark_stats"})
        return result
    items = result["bookmarks"]
    folders: dict[str, int] = {}
    for b in items:
        parent = b.get("parent") or "(root)"
        folders[parent] = folders.get(parent, 0) + 1
    return {
        "success": True,
        "browser": browser,
        "operation": "get_bookmark_stats",
        "total_count": len(items),
        "folder_count": len(folders),
        "folders": [{"folder": k, "count": v} for k, v in sorted(folders.items(), key=lambda kv: -kv[1])],
        "tagged_count": sum(1 for b in items if tag_store.get_tags(b.get("url", ""))),
    }


async def chromium_find_old(browser: str, age_days: int = 365) -> dict[str, Any]:
    import time

    result = await list_chromium_bookmarks(browser)
    if "bookmarks" not in result:
        result.update({"success": False, "browser": browser, "operation": "find_old_bookmarks"})
        return result
    cutoff = time.time() - age_days * 86400
    old = [b for b in result["bookmarks"] if b.get("date_added") and b["date_added"] < cutoff]
    return {
        "success": True,
        "browser": browser,
        "operation": "find_old_bookmarks",
        "age_days": age_days,
        "count": len(old),
        "bookmarks": old,
    }


async def chromium_tags(
    browser: str,
    *,
    operation: str,
    url: str | None = None,
    tags: list[str] | None = None,
    tag: str | None = None,
) -> dict[str, Any]:
    if operation == "list_tags":
        return {"success": True, "browser": browser, "operation": operation, "tags": tag_store.list_tags()}
    if operation == "get_all_tags":
        return {
            "success": True,
            "browser": browser,
            "operation": operation,
            "tag_map": tag_store.all_tags_by_url(),
        }
    if not url:
        return {"success": False, "browser": browser, "operation": operation, "error": "url required"}
    if operation == "get_tags":
        return {
            "success": True,
            "browser": browser,
            "operation": operation,
            "url": url,
            "tags": tag_store.get_tags(url),
        }
    if operation == "set_tags":
        updated = tag_store.set_tags(url, tags or [])
        return {"success": True, "browser": browser, "operation": operation, "url": url, "tags": updated}
    if operation == "remove_tag":
        if not tag:
            return {"success": False, "browser": browser, "operation": operation, "error": "tag required"}
        updated = tag_store.remove_tag(url, tag)
        return {"success": True, "browser": browser, "operation": operation, "url": url, "tags": updated}
    return {"success": False, "browser": browser, "operation": operation, "error": "unknown tag operation"}


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
    tag: str | None = None,
    search_query: str | None = None,
    search_type: str = "all",
    limit: int = 100,
    offset: int = 0,
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
    """BROWSER_BOOKMARKS - Universal bookmark management across Chrome, Firefox, Edge, and Brave.

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
    limit = max(1, min(limit, 100_000))
    browser_lower = browser.lower()

    if operation == "sync_bookmarks":
        if not target_browser:
            return {"success": False, "error": "sync_bookmarks requires 'target_browser' parameter"}
        return await sync_bookmarks(source_browser=browser, target_browser=target_browser, dry_run=dry_run, limit=limit)

    if browser_lower == "firefox":
        ff_operation = "search_bookmarks" if operation == "search" else operation
        result = await ff_bookmarks(
            operation=ff_operation,
            profile_name=profile_name,
            folder_id=folder_id,
            bookmark_id=int(bookmark_id) if bookmark_id and bookmark_id.isdigit() else None,
            url=url,
            title=title,
            tags=tags,
            search_query=search_query,
            search_type=search_type,
            export_format=export_format,
            export_path=export_path,
            batch_size=batch_size,
            similarity_threshold=similarity_threshold,
            age_days=age_days,
            check_links=check_links,
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
                offset = max(0, offset)
                all_items = result["bookmarks"]
                result["total_count"] = len(all_items)
                result["bookmarks"] = all_items[offset : offset + limit]
                result["returned_count"] = len(result["bookmarks"])
                result["pagination"] = {
                    "limit": limit,
                    "offset": offset,
                    "page": (offset // limit) + 1 if limit else 1,
                    "total_pages": max(1, (len(all_items) + limit - 1) // limit) if limit else 1,
                    "has_more": (offset + limit) < len(all_items),
                    "total_count": len(all_items),
                }
            return result

        elif operation in ("get_bookmark_stats",):
            return await chromium_stats(browser_lower)

        elif operation in ("find_old_bookmarks", "find_forgotten_bookmarks"):
            return await chromium_find_old(browser_lower, age_days=age_days)

        elif operation == "check_link":
            if not url:
                return {
                    "success": False,
                    "browser": browser_lower,
                    "operation": operation,
                    "error": "check_link requires 'url'",
                }
            return await check_url_exists(url)

        elif operation in ("list_tags", "get_tags", "set_tags", "remove_tag", "get_all_tags"):
            return await chromium_tags(browser_lower, operation=operation, url=url, tags=tags, tag=tag)

        elif operation in ("add_bookmark"):
            if not url or not title:
                return {
                    "success": False,
                    "browser": browser_lower,
                    "operation": operation,
                    "error": "add_bookmark requires 'url' and 'title'",
                }
            result = await add_chromium_bookmark(browser_lower, title=title, url=url, folder=folder)
            result["browser"] = browser_lower
            result["operation"] = operation
            return result

        elif operation == "edit_bookmark":
            if not bookmark_id and not url:
                return {
                    "success": False,
                    "browser": browser_lower,
                    "operation": operation,
                    "error": "edit_bookmark requires 'bookmark_id' or 'url'",
                }
            result = await edit_chromium_bookmark_entry(
                browser_lower,
                id=bookmark_id,
                url=url,
                new_title=new_title,
                new_folder=new_folder,
                allow_duplicates=allow_duplicates,
                create_folders=create_folders,
                dry_run=dry_run,
            )
            result["browser"] = browser_lower
            result["operation"] = operation
            return result

        elif operation == "delete_bookmark":
            if not bookmark_id and not url:
                return {
                    "success": False,
                    "browser": browser_lower,
                    "operation": operation,
                    "error": "delete_bookmark requires 'bookmark_id' or 'url'",
                }
            result = await delete_chromium_bookmark_entry(browser_lower, id=bookmark_id, url=url, dry_run=dry_run)
            result["browser"] = browser_lower
            result["operation"] = operation
            return result

        elif operation in ("search", "search_bookmarks"):
            if not search_query:
                return {
                    "success": False,
                    "browser": browser_lower,
                    "operation": operation,
                    "error": "search requires 'search_query'",
                }
            result = await list_chromium_bookmarks(browser_lower)
            bookmarks = result.get("bookmarks", [])
            query_lower = search_query.lower()
            matches = [
                b
                for b in bookmarks
                if query_lower in (b.get("title", "") or "").lower() or query_lower in (b.get("url", "") or "").lower()
            ]
            return {
                "success": True,
                "browser": browser_lower,
                "operation": operation,
                "query": search_query,
                "results": matches[:limit],
                "total_matches": len(matches),
                "returned_count": min(len(matches), limit),
            }

        elif operation == "get_bookmark":
            if not bookmark_id and not url:
                return {
                    "success": False,
                    "browser": browser_lower,
                    "operation": operation,
                    "error": "get_bookmark requires 'bookmark_id' or 'url'",
                }
            result = await list_chromium_bookmarks(browser_lower)
            bookmarks = result.get("bookmarks", [])
            for b in bookmarks:
                if (bookmark_id and b.get("id") == bookmark_id) or (url and b.get("url") == url):
                    return {"success": True, "browser": browser_lower, "operation": operation, "bookmark": b}
            return {
                "success": False,
                "browser": browser_lower,
                "operation": operation,
                "error": f"Bookmark not found: {bookmark_id or url}",
            }

        else:
            return {
                "success": False,
                "browser": browser_lower,
                "operation": operation,
                "error": f"Operation '{operation}' not supported for {browser_lower}",
                "supported_operations": [
                    "list_bookmarks",
                    "add_bookmark",
                    "edit_bookmark",
                    "delete_bookmark",
                    "get_bookmark",
                    "search",
                ],
                "note": "For advanced operations (duplicates, tags, export), use browser='firefox'",
            }

    return {
        "success": False,
        "operation": operation,
        "browser": browser,
        "error": f"Unknown browser type: {browser}",
        "supported_browsers": ["firefox", "chrome", "edge", "brave"],
    }
