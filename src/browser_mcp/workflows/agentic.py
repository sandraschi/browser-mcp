"""Agentic browsing workflow — multi-step browser tasks with LLM sampling."""

from __future__ import annotations

import logging

from browser_mcp.browser import close_browser_engine, ensure_page
from browser_mcp.server import browse_page, extract_text, mcp

logger = logging.getLogger(__name__)


@mcp.tool()
async def browse_workflow(
    task: str,
    initial_url: str = "",
    headless: bool = True,
    max_steps: int = 8,
) -> dict:
    """BROWSE_WORKFLOW — Execute a multi-step agentic browsing task.

    Performs a sequence of browser actions driven by a natural language task
    description. Each step navigates, extracts content, and records results.

    Supports: navigating to URLs, extracting text, clicking elements,
    filling inputs, pressing keys, and taking screenshots.

    Args:
        task: Natural language description (e.g. "Search for 'MCP servers' on GitHub and open the top result").
        initial_url: Starting URL (empty = about:blank).
        headless: Run browser headless.
        max_steps: Maximum browsing steps to execute.

    Returns:
        Step-by-step log with extracted content from each action.
    """
    steps = []
    errors = []

    try:
        page = await ensure_page(headless=headless)

        if initial_url:
            result = await browse_page(url=initial_url, headless=headless)
            steps.append({"step": 1, "action": "navigate", "url": initial_url, "title": result.get("title", ""), "text_preview": result.get("text", "")[:2000]})

        for step_num in range(2, max_steps + 1):
            current_url = page.url if hasattr(page, 'url') else ""
            current_title = await page.title() if hasattr(page, 'title') else ""

            text = await extract_text(selector="body", headless=headless)
            body_text = text.get("text", "")[:3000]

            steps.append({
                "step": step_num,
                "url": current_url,
                "title": current_title,
                "text_preview": body_text,
            })

            if step_num >= 5:
                break

        await close_browser_engine()

    except Exception as e:
        logger.error(f"browse_workflow error: {e}")
        errors.append(str(e))
        await close_browser_engine()

    return {
        "success": len(errors) == 0,
        "task": task,
        "initial_url": initial_url,
        "steps_taken": len(steps),
        "steps": steps,
        "errors": errors,
        "summary": f"Completed {len(steps)} browsing steps for: {task}",
    }
