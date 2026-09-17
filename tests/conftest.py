"""Shared fixtures for browser-mcp tests.

Declared doubles (per TESTING_GUIDE.md): these fixtures provide isolated,
in-memory / temp-dir stand-ins so unit and API tests run without touching a
real browser profile or making network calls.

- chromium_bookmarks: a temp Chromium-style Bookmarks JSON on disk.
- chromium_tree: the parsed dict fixture for direct function tests.
- api_client: FastAPI TestClient against the built app (no server required).
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from browser_mcp.app import build_app

SAMPLE_TREE = {
    "roots": {
        "bookmark_bar": {
            "type": "folder",
            "name": "Bookmarks bar",
            "id": "1",
            "children": [
                {"type": "url", "id": "2", "name": "Example", "url": "https://example.com"},
            ],
        },
        "other": {
            "type": "folder",
            "name": "Other bookmarks",
            "id": "3",
            "children": [
                {
                    "type": "folder",
                    "name": "Dev",
                    "id": "4",
                    "children": [
                        {"type": "url", "id": "5", "name": "GitHub", "url": "https://github.com"},
                    ],
                },
            ],
        },
        "synced": {"type": "folder", "name": "Mobile bookmarks", "id": "6", "children": []},
    }
}


@pytest.fixture
def chromium_tree() -> dict:
    """The parsed Chromium bookmarks tree used as a shared sample."""
    return json.loads(json.dumps(SAMPLE_TREE))


@pytest.fixture
def chromium_bookmarks(tmp_path) -> str:
    """Write a temp Chromium Bookmarks JSON and return its path string."""
    path = tmp_path / "Bookmarks"
    path.write_text(json.dumps(SAMPLE_TREE), encoding="utf-8")
    return str(path)


@pytest.fixture
def api_client() -> TestClient:
    """A TestClient over the built FastAPI app (no live server)."""
    return TestClient(build_app())
