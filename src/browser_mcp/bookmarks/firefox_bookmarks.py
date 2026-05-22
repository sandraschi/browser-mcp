import logging
from typing import Any

from .firefox.age_analyzer import find_forgotten_bookmarks, find_old_bookmarks, get_bookmark_stats
from .firefox.bookmark_manager import BookmarkManager
from .firefox.bulk_operations import BulkOperations
from .firefox.core import FirefoxDatabaseUnlocker
from .firefox.link_checker import LinkChecker
from .firefox.search_tools import BookmarkSearcher
from .firefox.status import FirefoxStatusChecker
from .firefox.tag_manager import TagManager
from .firefox.utils import get_profile_directory

logger = logging.getLogger(__name__)

WRITE_OPERATIONS = {"add_bookmark", "batch_update_tags", "remove_unused_tags", "merge_tags", "clean_up_tags"}


def _check_firefox_for_write(operation: str) -> dict[str, Any] | None:
    if operation not in WRITE_OPERATIONS:
        return None
    status = FirefoxStatusChecker.is_firefox_running()
    if status.get("is_running"):
        return {"success": False, "error": "Firefox is running - cannot write to bookmark database", "operation": operation, "firefox_status": status, "solution": "Please close Firefox completely and try again"}
    return None


def _get_bruteforce_connection(profile_name: str | None):
    profile_path = get_profile_directory(profile_name)
    if not profile_path:
        return None, "Profile not found"
    db_path = profile_path / "places.sqlite"
    if not db_path.exists():
        return None, "places.sqlite not found"
    return FirefoxDatabaseUnlocker.get_database_connection_bruteforce(db_path)


async def _bruteforce_read_operation(operation: str, profile_name: str | None, folder_id: int | None, bookmark_id: int | None, search_query: str | None, search_type: str, similarity_threshold: float, age_days: int) -> dict[str, Any]:
    conn, method = _get_bruteforce_connection(profile_name)
    if not conn:
        return {"success": False, "error": f"Brute force access failed: {method}", "note": "Close Firefox and try again without force_access=True"}
    try:
        cursor = conn.cursor()
        if operation == "list_bookmarks":
            query = "SELECT b.id, b.title, p.url, b.dateAdded, b.lastModified FROM moz_bookmarks b LEFT JOIN moz_places p ON b.fk = p.id WHERE b.type = 1"
            if folder_id:
                query += f" AND b.parent = {folder_id}"
            query += " ORDER BY b.dateAdded DESC LIMIT 1000"
            cursor.execute(query)
            bookmarks = [{"id": row[0], "title": row[1] or "", "url": row[2] or "", "dateAdded": row[3], "lastModified": row[4]} for row in cursor.fetchall()]
            return {"success": True, "message": "Bookmarks listed (brute force access)", "access_method": method, "firefox_was_running": True, "bookmarks": bookmarks, "count": len(bookmarks)}
        elif operation == "get_bookmark":
            if not bookmark_id:
                return {"success": False, "error": "bookmark_id required"}
            cursor.execute("SELECT b.id, b.title, p.url, b.dateAdded, b.lastModified, b.parent FROM moz_bookmarks b LEFT JOIN moz_places p ON b.fk = p.id WHERE b.id = ?", (bookmark_id,))
            row = cursor.fetchone()
            if not row:
                return {"success": False, "error": f"Bookmark {bookmark_id} not found"}
            return {"success": True, "message": f"Bookmark {bookmark_id} retrieved (brute force)", "access_method": method, "bookmark": {"id": row[0], "title": row[1] or "", "url": row[2] or "", "dateAdded": row[3], "lastModified": row[4], "parent": row[5]}}
        elif operation == "search_bookmarks":
            if not search_query:
                return {"success": False, "error": "search_query required"}
            like_query = f"%{search_query}%"
            cursor.execute("SELECT b.id, b.title, p.url FROM moz_bookmarks b LEFT JOIN moz_places p ON b.fk = p.id WHERE b.type = 1 AND (b.title LIKE ? OR p.url LIKE ?) LIMIT 100", (like_query, like_query))
            results = [{"id": row[0], "title": row[1] or "", "url": row[2] or ""} for row in cursor.fetchall()]
            return {"success": True, "message": "Search completed (brute force)", "access_method": method, "search_query": search_query, "results": results, "count": len(results)}
        elif operation == "get_bookmark_stats":
            cursor.execute("SELECT COUNT(*) FROM moz_bookmarks WHERE type = 1")
            bookmark_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM moz_places")
            url_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT parent) FROM moz_bookmarks WHERE type = 1")
            folder_count = cursor.fetchone()[0]
            return {"success": True, "message": "Stats retrieved (brute force)", "access_method": method, "stats": {"bookmark_count": bookmark_count, "url_count": url_count, "folder_count": folder_count}}
        else:
            return {"success": False, "error": f"Brute force not implemented for {operation}", "note": "Close Firefox and try without force_access=True"}
    except Exception as e:
        logger.error(f"Brute force operation failed: {e}", exc_info=True)
        return {"success": False, "error": f"Brute force operation failed: {e!s}"}
    finally:
        if hasattr(conn, "temp_db_path"):
            try:
                conn.temp_db_path.unlink(missing_ok=True)
            except Exception:
                pass
        conn.close()


async def firefox_bookmarks(operation: str, profile_name: str | None = None, folder_id: int | None = None, bookmark_id: int | None = None, url: str | None = None, title: str | None = None, tags: list[str] | None = None, search_query: str | None = None, search_type: str = "all", export_format: str = "json", export_path: str | None = None, batch_size: int = 100, similarity_threshold: float = 0.85, age_days: int = 365, check_links: bool = False, force_access: bool = False) -> dict[str, Any]:
    read_operations = {"list_bookmarks", "get_bookmark", "search_bookmarks", "find_duplicates", "list_tags", "find_similar_tags", "find_old_bookmarks", "find_forgotten_bookmarks", "get_bookmark_stats"}
    if force_access and operation in read_operations:
        status = FirefoxStatusChecker.is_firefox_running()
        if status.get("is_running"):
            logger.info(f"Firefox running, using brute force for {operation}")
            return await _bruteforce_read_operation(operation, profile_name, folder_id, bookmark_id, search_query, search_type, similarity_threshold, age_days)
    firefox_error = _check_firefox_for_write(operation)
    if firefox_error:
        logger.warning(f"Blocking {operation} - Firefox is running")
        return firefox_error
    if operation == "list_bookmarks":
        try:
            manager = BookmarkManager(get_profile_directory(profile_name))
            bookmarks = await manager.list_bookmarks(folder_id)
            return {"success": True, "message": "Bookmarks listed successfully", "bookmarks": bookmarks, "count": len(bookmarks), "profile_name": profile_name}
        except Exception as e:
            return {"success": False, "error": str(e), "bookmarks": [], "count": 0}
    elif operation == "get_bookmark":
        try:
            if not bookmark_id:
                raise ValueError("Bookmark ID is required")
            manager = BookmarkManager(get_profile_directory(profile_name))
            bookmark = await manager.get_bookmark(bookmark_id)
            return {"success": True, "message": f"Bookmark {bookmark_id} retrieved", "bookmark": bookmark, "bookmark_id": bookmark_id}
        except Exception as e:
            return {"success": False, "error": str(e)}
    elif operation == "add_bookmark":
        try:
            if not url:
                raise ValueError("URL is required")
            manager = BookmarkManager(get_profile_directory(profile_name))
            bid = await manager.add_bookmark(url, title, tags)
            return {"success": True, "message": "Bookmark added", "bookmark_id": bid, "url": url, "title": title}
        except Exception as e:
            return {"success": False, "error": str(e)}
    elif operation == "search_bookmarks":
        try:
            if not search_query:
                raise ValueError("Search query is required")
            searcher = BookmarkSearcher(get_profile_directory(profile_name))
            results = await searcher.search_bookmarks(search_query, search_type)
            return {"success": True, "message": f"Search completed for '{search_query}'", "results": results, "count": len(results), "search_query": search_query}
        except Exception as e:
            return {"success": False, "error": str(e), "results": [], "count": 0}
    elif operation == "find_duplicates":
        try:
            searcher = BookmarkSearcher(get_profile_directory(profile_name))
            duplicates = await searcher.find_duplicates(similarity_threshold)
            return {"success": True, "message": "Duplicate search completed", "duplicates": duplicates, "duplicate_groups": len(duplicates)}
        except Exception as e:
            return {"success": False, "error": str(e), "duplicates": [], "duplicate_groups": 0}
    elif operation == "export_bookmarks":
        try:
            bulk_ops = BulkOperations(get_profile_directory(profile_name))
            result = await bulk_ops.export_bookmarks(export_format, export_path)
            return {"success": True, "message": f"Bookmarks exported to {export_format}", "export_format": export_format, "export_result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    elif operation == "batch_update_tags":
        try:
            if not tags:
                raise ValueError("Tags are required")
            bulk_ops = BulkOperations(get_profile_directory(profile_name))
            result = await bulk_ops.batch_update_tags(tags, batch_size)
            return {"success": True, "message": "Batch tag update completed", "tags": tags, "update_result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    elif operation == "remove_unused_tags":
        try:
            bulk_ops = BulkOperations(get_profile_directory(profile_name))
            result = await bulk_ops.remove_unused_tags()
            return {"success": True, "message": "Unused tags removed", "removal_result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    elif operation == "list_tags":
        try:
            tag_manager = TagManager(get_profile_directory(profile_name))
            tags_list = await tag_manager.list_tags()
            return {"success": True, "message": "Tags listed", "tags": tags_list, "count": len(tags_list)}
        except Exception as e:
            return {"success": False, "error": str(e), "tags": [], "count": 0}
    elif operation == "find_similar_tags":
        try:
            tag_manager = TagManager(get_profile_directory(profile_name))
            similar_tags = await tag_manager.find_similar_tags()
            return {"success": True, "message": "Similar tags found", "similar_tags": similar_tags, "groups": len(similar_tags)}
        except Exception as e:
            return {"success": False, "error": str(e), "similar_tags": [], "groups": 0}
    elif operation == "merge_tags":
        try:
            if not tags or len(tags) < 2:
                raise ValueError("At least 2 tags are required for merging")
            tag_manager = TagManager(get_profile_directory(profile_name))
            result = await tag_manager.merge_tags(tags)
            return {"success": True, "message": "Tags merged", "merged_tags": tags, "merge_result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    elif operation == "clean_up_tags":
        try:
            tag_manager = TagManager(get_profile_directory(profile_name))
            result = await tag_manager.clean_up_tags()
            return {"success": True, "message": "Tags cleaned up", "cleanup_result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    elif operation == "find_old_bookmarks":
        try:
            result = await find_old_bookmarks(age_days, str(get_profile_directory(profile_name)) if profile_name else None)
            return {"success": True, "message": f"Found bookmarks created more than {age_days} days ago", "age_days": age_days, "bookmarks": result.get("bookmarks", []), "count": result.get("bookmark_count", 0)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    elif operation == "find_forgotten_bookmarks":
        try:
            result = await find_forgotten_bookmarks(age_days, str(get_profile_directory(profile_name)) if profile_name else None)
            return {"success": True, "message": f"Found {result.get('bookmark_count', 0)} bookmarks not visited in {age_days}+ days", "days_unvisited": age_days, "bookmarks": result.get("bookmarks", []), "count": result.get("bookmark_count", 0)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    elif operation == "refresh_bookmarks":
        return {"success": True, "message": "Bookmark refresh (stub)", "note": "Full link refresh requires async batch processing"}
    elif operation == "get_bookmark_stats":
        try:
            result = await get_bookmark_stats(str(get_profile_directory(profile_name)) if profile_name else None)
            return {"success": True, "message": "Bookmark statistics retrieved", "stats": result}
        except Exception as e:
            return {"success": False, "error": str(e), "stats": {}}
    elif operation == "find_broken_links":
        try:
            link_checker = LinkChecker(get_profile_directory(profile_name))
            result = await link_checker.find_broken_links(check_links)
            return {"success": True, "message": "Broken links check completed", "broken_links": result.get("broken_links", []), "count": result.get("count", 0)}
        except Exception as e:
            return {"success": False, "error": str(e), "broken_links": [], "count": 0}
    else:
        return {"success": False, "error": f"Unknown operation: {operation}", "available_operations": ["list_bookmarks", "get_bookmark", "add_bookmark", "search_bookmarks", "find_duplicates", "export_bookmarks", "batch_update_tags", "remove_unused_tags", "list_tags", "find_similar_tags", "merge_tags", "clean_up_tags", "find_old_bookmarks", "find_forgotten_bookmarks", "refresh_bookmarks", "get_bookmark_stats", "find_broken_links"]}
