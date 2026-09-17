"""API endpoint tests for the REST surface added/improved in the endpoint pass.

Covers: /api/browsers, /api/bookmarks/sources, /api/status, /api/shutdown
(confirm gating), /api/logs, /api/logs/clear, and the in-memory log ring buffer.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from browser_mcp.logs import LOG_BUFFER


def test_browsers_route_shape(api_client: TestClient) -> None:
    r = api_client.get("/api/browsers")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    for name in ("chrome", "firefox", "edge", "brave"):
        assert name in body["browsers"]
        assert "installed" in body["browsers"][name]
    assert body["count"] == sum(1 for b in body["browsers"].values() if b["installed"])


def test_bookmarks_sources_route_shape(api_client: TestClient) -> None:
    r = api_client.get("/api/bookmarks/sources")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    for name in ("chrome", "firefox", "edge", "brave"):
        assert name in body["sources"]
        assert "available" in body["sources"][name]
    assert set(body["available"]).issubset(body["sources"].keys())


def test_status_route_has_rich_fields(api_client: TestClient) -> None:
    r = api_client.get("/api/status")
    assert r.status_code == 200
    body = r.json()
    for key in ("service", "version", "browsers", "bookmarks_sources", "llm", "llm_detected", "platform"):
        assert key in body, f"status missing {key}"


def test_health_has_checks(api_client: TestClient) -> None:
    r = api_client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "checks" in body
    assert "browser" in body["checks"]
    assert "bookmarks" in body["checks"]


def test_shutdown_requires_confirm(api_client: TestClient) -> None:
    r = api_client.post("/api/shutdown")
    assert r.status_code == 400
    assert r.json()["status"] == "error"


def test_logs_route_returns_lines(api_client: TestClient) -> None:
    LOG_BUFFER.clear()
    r = api_client.get("/api/logs?tail=50")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body["lines"], list)


def test_logs_clear(api_client: TestClient) -> None:
    LOG_BUFFER.clear()
    LOG_BUFFER.emit(_make_record("boom"))
    assert len(LOG_BUFFER.snapshot()) == 1
    r = api_client.post("/api/logs/clear")
    assert r.status_code == 200
    assert not any("boom" in line for line in LOG_BUFFER.snapshot())


def test_log_buffer_ring_capacity() -> None:
    LOG_BUFFER.clear()
    for i in range(3000):
        LOG_BUFFER.emit(_make_record(f"line {i}"))
    assert len(LOG_BUFFER.snapshot()) <= 2000
    assert LOG_BUFFER.snapshot()[-1].endswith("line 2999")


def _make_record(message: str):
    import logging

    return logging.LogRecord(
        name="test", level=logging.INFO, pathname=__file__, lineno=1, msg=message, args=(), exc_info=None
    )
