"""
Browser Use agentic browsing tool — wraps browser-use Agent for natural language tasks.
Registered in server.py via import.
"""

from __future__ import annotations

import logging
import os
from typing import Annotated

from fastmcp.tools import ToolResult
from pydantic import Field

from ..server import mcp

logger = logging.getLogger(__name__)

LLM_DEFAULT = "http://127.0.0.1:11434"
LLM_MODEL = os.environ.get("LLM_MODEL", "gemma4:12b")
LLM_BASE = (os.environ.get("LLM_BASE_URL") or "").rstrip("/") or LLM_DEFAULT


@mcp.tool(version="0.1.0", annotations={"readOnlyHint": False})
async def browser_agent(
    task: Annotated[str, Field(description="Natural language task. Example: 'Find the price of the RTX 5090 on Amazon'.")],
    headless: Annotated[bool, Field(description="Run browser headless. Set False to watch.")] = True,
    max_steps: Annotated[int, Field(description="Max browser steps before giving up.", ge=1, le=50)] = 20,
) -> ToolResult:
    """
    Execute a natural-language browsing task using an AI agent.

    The agent uses browser-use with the configured LLM (Ollama by default)
    to autonomously navigate websites, click elements, fill forms, and
    extract information based on your task description.

    ## Return Format
    {"success": bool, "result": str | None, "steps": int, "error": str | None}

    ## Examples
    await browser_agent(task="Find the cheapest RTX 5090 on Amazon")
    await browser_agent(task="Log in to Gmail and check for unread emails from Sandra", headless=False)
    """
    try:
        from browser_use import Agent, BrowserProfile
    except ImportError:
        return ToolResult(
            content={
                "success": False,
                "error": "browser-use not installed. Run: uv add browser-use",
            }
        )

    try:
        from browser_use import ChatBrowserUse
        llm = ChatBrowserUse(model=f"openai/{LLM_MODEL}", base_url=LLM_BASE)
    except Exception:
        import openai
        client = openai.AsyncOpenAI(base_url=f"{LLM_BASE}/v1", api_key="not-needed")
        llm = client

    profile = BrowserProfile(
        headless=headless,
        allowed_domains=None,
        cdp_url=None,
    )

    agent = Agent(
        task=task,
        llm=llm,
        browser_profile=profile,
        max_steps=max_steps,
    )

    try:
        history = await agent.run()
        final = history.final_result() if hasattr(history, "final_result") else str(history.urls[-1] if history.urls else None)
        return ToolResult(
            content={
                "success": True,
                "result": final,
                "steps": len(getattr(history, "action_names", [])),
                "urls": list(getattr(history, "urls", [])),
            }
        )
    except Exception as e:
        logger.exception("browser-use agent failed: %s", e)
        return ToolResult(
            content={
                "success": False,
                "error": str(e),
                "steps": 0,
            }
        )
