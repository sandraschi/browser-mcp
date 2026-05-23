"""Link processing workflow — browse a list of links with LLM summarization."""

from __future__ import annotations

import json
import logging

from browser_mcp.browser import close_browser_engine
from browser_mcp.server import browse_page, mcp

logger = logging.getLogger(__name__)


@mcp.tool()
async def browse_items(
    items_json: str,
    task: str = "Summarize the key point from each link",
    headless: bool = True,
    max_items: int = 10,
) -> dict:
    """BROWSE_ITEMS — Browse a list of items (URLs with titles) and return structured summaries.

    Accepts JSON input with items containing title and url fields. This makes it
    easy to chain with aiwatcher-mcp (get_top_items), arxiv-mcp (search_papers),
    or gitops-mcp (issue_list/pr_list).

    Each item is visited in a headless browser, text is extracted, and results
    are returned with title, url, text preview, and extraction status.

    Args:
        items_json: JSON array of items. Each item: {"title": "...", "url": "..."} or {"name": "...", "url": "..."}.
        task: Natural language description of what to look for on each page.
        headless: Run browser headless.
        max_items: Max items to process.

    Returns:
        Per-item results with text previews and an overall summary.
    """
    try:
        items = json.loads(items_json)
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"Invalid JSON: {e}"}

    if not isinstance(items, list):
        items = [items]

    items = items[:max_items]
    results = []
    errors = []

    for item in items:
        title = item.get("title") or item.get("name") or item.get("url", "unknown")
        url = item.get("url", "")
        if not url:
            errors.append({"title": title, "error": "No URL provided"})
            continue

        try:
            result = await browse_page(url=url, headless=headless)
            text = result.get("text", "")
            results.append({
                "title": title,
                "url": url,
                "page_title": result.get("title", ""),
                "text_preview": text[:3000],
                "status": result.get("status", 0),
                "success": result.get("success", False),
            })
        except Exception as e:
            errors.append({"title": title, "url": url, "error": str(e)})

    await close_browser_engine()

    total_text = " ".join(r.get("text_preview", "") for r in results if r.get("success"))
    summary = f"Processed {len(results)}/{len(items)} items. Total extracted text: {len(total_text)} chars. Task: {task}" if results else "No items processed."

    return {
        "success": True,
        "items_processed": len(results),
        "items_total": len(items),
        "errors": errors,
        "results": results,
        "summary": summary,
        "task": task,
        "next_steps": [
            "Pass this output to browse_workflow for deeper analysis",
            "Use the summaries to triage which links need more attention",
        ],
    }
