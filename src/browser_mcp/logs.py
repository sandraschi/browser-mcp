"""In-memory ring buffer for the webapp Logs page.

Captures Python logging records from the root logger and exposes a tail
snapshot + clear API so the frontend can render live server logs without
touching the filesystem (safe under Tauri where log files are not portable).
"""

from __future__ import annotations

import logging
import threading
import time

_CAPACITY = 2000


class LogBufferHandler(logging.Handler):
    """Buffers formatted log lines in a bounded, thread-safe ring."""

    def __init__(self, capacity: int = _CAPACITY) -> None:
        super().__init__()
        self._capacity = capacity
        self._lock = threading.Lock()
        self._lines: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
        except Exception:
            message = record.getMessage()
        ts = time.strftime("%H:%M:%S", time.localtime(record.created))
        line = f"{ts} [{record.levelname}] {record.name}: {message}"
        with self._lock:
            self._lines.append(line)
            if len(self._lines) > self._capacity:
                del self._lines[: len(self._lines) - self._capacity]

    def snapshot(self, tail: int | None = None) -> list[str]:
        with self._lock:
            lines = list(self._lines)
        if tail is not None and tail >= 0 and len(lines) > tail:
            lines = lines[-tail:]
        return lines

    def clear(self) -> None:
        with self._lock:
            self._lines.clear()


LOG_BUFFER = LogBufferHandler()


def attach_log_buffer() -> None:
    """Attach the ring buffer to the root logger (idempotent)."""
    root = logging.getLogger()
    if LOG_BUFFER not in root.handlers:
        root.addHandler(LOG_BUFFER)
    if root.level > logging.INFO:
        root.setLevel(logging.INFO)
