# browser-mcp (MCPB Bundle)

FastMCP 3.2 server for Playwright browser automation — browse, click, screenshot, extract

## Usage

Add to \claude_desktop_config.json\:
\\\json
{
  "mcpServers": {
    "browser-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "\D:\Dev\repos", "python", "-m", "browser_mcp"],
      "env": { "PYTHONPATH": "\D:\Dev\repos/src" }
    }
  }
}
\\\

## Tools

- **health**: health
- **browse_page**: browse_page
- **click_element**: click_element
- **extract_text**: extract_text
- **screenshot**: screenshot
- **fill_input**: fill_input
- **press_key**: press_key
- **close_browser**: close_browser
- **list_browsers**: list_browsers
- **browse_url_cli**: browse_url_cli
- **browser_bookmarks**: browser_bookmarks
- **browse_workflow**: browse_workflow
- **morning_briefing**: morning_briefing
- **browse_items**: browse_items

## Requirements

- Python 3.12+
- uv
