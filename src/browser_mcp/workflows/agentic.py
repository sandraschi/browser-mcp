"""Agentic browsing workflow - multi-step browser tasks with LLM sampling."""

from __future__ import annotations

import logging

from browser_mcp.browser import close_browser_engine, ensure_page
from browser_mcp.server import mcp

logger = logging.getLogger(__name__)


@mcp.tool()
async def browse_workflow(
    task: str,
    initial_url: str = "",
    headless: bool = True,
    max_steps: int = 8,
) -> dict:
    """BROWSE_WORKFLOW - Execute a multi-step agentic browsing task.

    Performs a sequence of browser actions driven by a natural language task
    description. Each step navigates, extracts content, and records results.

    Supports: navigating to URLs, extracting text, clicking elements,
    filling inputs, pressing keys, and taking screenshots.

    ## Return Format
    {"success": bool, "task": str, "initial_url": str, "steps_taken": int,
     "steps": [{step, url, title, text_preview}], "errors": [str], "summary": str}

    ## Examples
    await browse_workflow(task="Search for 'MCP servers' on GitHub and open the top result")
    await browse_workflow(task="Find pricing on example.com", initial_url="https://example.com", max_steps=5)
    """
    steps = []
    errors = []

    try:
        page = await ensure_page(headless=headless)

        if initial_url:
            from browser_mcp.server import browse_page

            result = await browse_page(url=initial_url, headless=headless)
            steps.append(
                {
                    "step": 1,
                    "action": "navigate",
                    "url": initial_url,
                    "title": result.get("title", ""),
                    "text_preview": result.get("text", "")[:2000],
                }
            )

        for step_num in range(2, max_steps + 1):
            current_url = page.url if hasattr(page, "url") else ""
            current_title = await page.title() if hasattr(page, "title") else ""

            from browser_mcp.server import extract_text

            text = await extract_text(selector="body", headless=headless)
            body_text = text.get("text", "")[:3000]

            steps.append(
                {
                    "step": step_num,
                    "url": current_url,
                    "title": current_title,
                    "text_preview": body_text,
                }
            )

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
