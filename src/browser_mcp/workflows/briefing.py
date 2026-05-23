"""Morning briefing workflow — configurable daily page routine."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from browser_mcp.browser import close_browser_engine, ensure_page
from browser_mcp.server import browse_page, mcp

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent.parent / "conf" / "morning_pages.json"


def _load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {"profiles": {"default": {"label": "Default", "pages": [], "integration": {}}}}
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


@mcp.tool()
async def morning_briefing(
    config_name: str = "default",
    headless: bool = True,
    max_pages: int = 5,
) -> dict:
    """MORNING_BRIEFING — Run your configurable morning browsing routine.

    Visits a set of pages defined in the morning_pages.json config profile,
    extracts content from each, and returns a structured briefing.

    Built-in profiles: default (HN + GitHub), dev (HN + Python + Lobsters),
    research (arXiv + Reddit ML), fleet (repo activity).

    Config file: conf/morning_pages.json — add custom profiles.

    Args:
        config_name: Profile name from morning_pages.json (default, dev, research, fleet).
        headless: Run browser headless.
        max_pages: Max pages to visit (prevents runaway).

    Returns:
        Briefing with per-page summaries and overall digest.
    """
    config = _load_config()
    profile = config.get("profiles", {}).get(config_name)
    if not profile:
        available = list(config.get("profiles", {}).keys())
        return {"success": False, "error": f"Profile '{config_name}' not found", "available_profiles": available}

    pages = profile.get("pages", [])[:max_pages]
    results = []
    errors = []

    for page_cfg in pages:
        try:
            page = await ensure_page(headless=headless)
            result = await browse_page(url=page_cfg["url"], headless=headless)
            results.append({
                "name": page_cfg["name"],
                "url": page_cfg["url"],
                "task": page_cfg.get("task", ""),
                "title": result.get("title", ""),
                "text_preview": result.get("text", "")[:5000],
                "status": result.get("status", 0),
                "success": result.get("success", False),
            })
        except Exception as e:
            errors.append({"url": page_cfg["url"], "name": page_cfg["name"], "error": str(e)})

    await close_browser_engine()

    integration = profile.get("integration", {})
    aiwatcher_hint = ""
    if integration.get("aiwatcher_hours"):
        aiwatcher_hint = (
            f"AIWatcher top items from the last {integration['aiwatcher_hours']}h "
            f"(limit {integration['aiwatcher_limit']}): use browse_items tool with "
            f"aiwatcher-mcp get_top_items output"
        )

    return {
        "success": True,
        "profile": config_name,
        "label": profile.get("label", config_name),
        "briefing_date": __import__("datetime").datetime.now().isoformat(),
        "pages_visited": len(results),
        "pages": results,
        "errors": errors,
        "suggestions": {
            "aiwatcher": aiwatcher_hint,
            "next_steps": [
                "Call browse_items with aiwatcher-mcp's top items",
                "Check specific repo issues with browse_workflow",
            ],
        },
    }
