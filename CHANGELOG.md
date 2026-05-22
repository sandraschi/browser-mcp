# Changelog

## 0.2.0 (2026-05-23)

- **Bookmark management**: 17 operations across Chrome, Firefox, Edge, Brave
  - CRUD, search, cross-browser sync, dedup, tags, age analysis, link checking
  - Migrated from `database-operations-mcp` to its proper home
- **Browser detection**: `list_browsers()` — detect installed Chrome, Firefox, Edge, Brave
- **CLI browsing**: `browse_url_cli()` — headless DOM/screenshot via subprocess (no Playwright)
- **Webapp dashboard**: React + Vite on port 10781 with Dashboard + Bookmarks pages
- **Fleet port allocation**: Frontend port 10781 registered in WEBAPP_PORTS.md
- **Fleet registration**: Enabled in MASTER_MCP_CONFIG

## 0.1.0 (2026-04-29)

- Initial scaffold: browse_page, click_element, extract_text, screenshot, fill_input, press_key, close_browser
- Dual transport: stdio (Claude Desktop) + HTTP (port 10780)
