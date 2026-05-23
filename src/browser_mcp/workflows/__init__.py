"""AI browser workflows — multi-step agentic browsing, morning briefings, link processing."""

from browser_mcp.workflows.agentic import browse_workflow
from browser_mcp.workflows.briefing import morning_briefing
from browser_mcp.workflows.link_processor import browse_items

__all__ = ["browse_items", "browse_workflow", "morning_briefing"]
