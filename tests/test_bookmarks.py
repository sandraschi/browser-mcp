"""Unit tests for Chromium bookmark file logic (read / flatten / write / edit / delete).

Uses the `chromium_bookmarks` temp-file and `chromium_tree` fixtures from
conftest.py - no real browser profile is touched.
"""

from __future__ import annotations

from pathlib import Path

from browser_mcp.bookmarks.chromium_common import (
    _chrome_time_to_epoch,
    _flatten_chromium_tree,
    delete_chromium_bookmark,
    edit_chromium_bookmark,
    read_chromium_bookmarks,
    write_chromium_bookmark,
)


def test_read_chromium_bookmarks_flattens(chromium_bookmarks: str) -> None:
    result = read_chromium_bookmarks(Path(chromium_bookmarks))
    assert result["status"] == "success"
    urls = [b["url"] for b in result["bookmarks"]]
    assert urls == ["https://example.com", "https://github.com"]
    assert result["count"] == 2


def test_read_missing_file_returns_error() -> None:
    result = read_chromium_bookmarks(Path("C:/does/not/exist/Bookmarks"))
    assert result["status"] == "error"
    assert result["error_code"] == "CHROMIUM_FILE_NOT_FOUND"


def test_read_invalid_json_returns_error(tmp_path) -> None:
    bad = tmp_path / "Bookmarks"
    bad.write_text("{ not valid json", encoding="utf-8")
    result = read_chromium_bookmarks(bad)
    assert result["status"] == "error"
    assert result["error_code"] == "CHROMIUM_INVALID_JSON"


def test_flatten_tree_includes_folders_and_synced(chromium_tree: dict) -> None:
    flat = _flatten_chromium_tree(chromium_tree["roots"]["bookmark_bar"])
    flat += _flatten_chromium_tree(chromium_tree["roots"]["other"])
    flat += _flatten_chromium_tree(chromium_tree["roots"]["synced"])
    assert [b["url"] for b in flat] == ["https://example.com", "https://github.com"]


def test_write_adds_bookmark(chromium_bookmarks: str) -> None:
    result = write_chromium_bookmark(Path(chromium_bookmarks), title="Python", url="https://python.org")
    assert result["status"] == "success"
    urls = [b["url"] for b in read_chromium_bookmarks(Path(chromium_bookmarks))["bookmarks"]]
    assert "https://python.org" in urls


def test_write_skips_duplicate(chromium_bookmarks: str) -> None:
    result = write_chromium_bookmark(Path(chromium_bookmarks), title="Example", url="https://example.com")
    assert result["duplicate"] is True


def test_edit_changes_title(chromium_bookmarks: str) -> None:
    result = edit_chromium_bookmark(Path(chromium_bookmarks), id="2", new_title="Renamed")
    assert result["status"] == "success"
    assert result["bookmark"]["title"] == "Renamed"


def test_edit_missing_bookmark_errors(chromium_bookmarks: str) -> None:
    result = edit_chromium_bookmark(Path(chromium_bookmarks), id="999", new_title="Nope")
    assert result["status"] == "error"


def test_delete_removes_bookmark(chromium_bookmarks: str) -> None:
    result = delete_chromium_bookmark(Path(chromium_bookmarks), url="https://example.com")
    assert result["status"] == "success"
    urls = [b["url"] for b in read_chromium_bookmarks(Path(chromium_bookmarks))["bookmarks"]]
    assert "https://example.com" not in urls


def test_delete_dry_run_does_not_touch_file(chromium_bookmarks: str) -> None:
    result = delete_chromium_bookmark(Path(chromium_bookmarks), url="https://example.com", dry_run=True)
    assert result["status"] == "planned"
    urls = [b["url"] for b in read_chromium_bookmarks(Path(chromium_bookmarks))["bookmarks"]]
    assert "https://example.com" in urls


def test_chrome_time_to_epoch() -> None:
    # Windows FILETIME epoch (1601-01-01) = 11644473600 seconds before unix epoch.
    assert _chrome_time_to_epoch(11644473600000000) == 0
    assert _chrome_time_to_epoch(11644473610000000) == 10
    assert _chrome_time_to_epoch(None) == 0


def test_flatten_includes_id_and_date_added(chromium_tree: dict) -> None:
    flat = _flatten_chromium_tree(chromium_tree["roots"]["other"])
    github = next(b for b in flat if b["url"] == "https://github.com")
    assert github["id"] == "5"
    assert "date_added" in github
    assert github["date_added"] == 0  # fixture has no date_added -> 0
    assert github["parent"] == "Dev"
