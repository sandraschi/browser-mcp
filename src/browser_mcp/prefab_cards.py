"""Prefab UI cards for list/status tools (in-chat rich UI)."""

from __future__ import annotations

from fastmcp.tools import ToolResult
from prefab_ui import PrefabApp
from prefab_ui.components import Row, Text

from browser_mcp.server import mcp


@mcp.tool(app=True, annotations={"readOnlyHint": True})
async def show_browsers_card() -> ToolResult:
    """SHOW_BROWSERS_CARD — Installed browsers as a rich in-chat card.

    Renders the detection result of `list_browsers()` as a structured card
    with one row per browser.

    ## Return Format
    ToolResult with PrefabApp (or plain text fallback).

    ## Examples
    await show_browsers_card()
    """
    from browser_mcp.server import list_browsers

    result = await list_browsers()
    with PrefabApp(title="Installed Browsers") as app:
        for name, info in result.get("browsers", {}).items():
            if info.get("installed"):
                detail = info.get("path", "")
                if info.get("profiles"):
                    detail += f" ({len(info['profiles'])} profiles)"
                Row(children=[Text(content=name.capitalize()), Text(content=f"installed - {detail}")])
            else:
                Row(children=[Text(content=name.capitalize()), Text(content="not found")])
    return ToolResult(
        content=f"Installed browsers: {', '.join(n for n, i in result.get('browsers', {}).items() if i.get('installed')) or 'none detected'}",
        structured_content=app,
    )
