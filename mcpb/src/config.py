"""
Settings from environment — single source of config.
Never scatter os.getenv outside this module.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    mcp_http_path: str
    headless: bool
    frontend_port: int

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            host=os.getenv("BROWSER_MCP_HOST", "127.0.0.1"),
            port=int(os.getenv("BROWSER_MCP_PORT", "10780")),
            mcp_http_path=os.getenv("BROWSER_MCP_HTTP_PATH", "/mcp"),
            headless=os.getenv("BROWSER_HEADLESS", "true").lower() == "true",
            frontend_port=int(os.getenv("BROWSER_MCP_FRONTEND_PORT", "10781")),
        )


_settings: Settings | None = None


def load_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings
