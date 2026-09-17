"""Unit tests for the sidecar tag store (uses a temp DB, never the real one)."""

from __future__ import annotations

import pytest

from browser_mcp import tags


@pytest.fixture
def tagdb(tmp_path, monkeypatch):
    monkeypatch.setattr(tags, "DB_PATH", tmp_path / "bookmark_tags.db")


def test_tags_empty_by_default(tagdb) -> None:
    assert tags.get_tags("https://example.com") == []
    assert tags.list_tags() == []


def test_set_get_normalizes_and_sorts(tagdb) -> None:
    tags.set_tags("https://example.com", ["B", "a", "b", ""])
    assert tags.get_tags("https://example.com") == ["a", "b"]


def test_list_tags_aggregates_counts(tagdb) -> None:
    tags.set_tags("https://one", ["dev", "docs"])
    tags.set_tags("https://two", ["dev"])
    result = tags.list_tags()
    assert {"tag": "dev", "count": 2} in result
    assert {"tag": "docs", "count": 1} in result


def test_remove_tag(tagdb) -> None:
    tags.set_tags("https://one", ["dev", "docs"])
    tags.remove_tag("https://one", "docs")
    assert tags.get_tags("https://one") == ["dev"]


def test_set_empty_clears(tagdb) -> None:
    tags.set_tags("https://one", ["dev"])
    tags.set_tags("https://one", [])
    assert tags.get_tags("https://one") == []
    assert tags.all_tags_by_url() == {}


def test_all_tags_by_url(tagdb) -> None:
    tags.set_tags("https://one", ["dev"])
    tags.set_tags("https://two", ["docs"])
    assert tags.all_tags_by_url() == {"https://one": ["dev"], "https://two": ["docs"]}
