# Session Context (Browser MCP)

You have access to browser automation tools: Playwright page control, cross-browser bookmarks, and agentic browsing workflows.

**Before starting work:**
1. Check installed browsers: `list_browsers()`
2. Open a page: `browse_page(url="https://example.com")`
3. List bookmarks: `browser_bookmarks(browser="firefox", operation="list_bookmarks")`

**At end of work:**
- Close the browser: `close_browser()`
