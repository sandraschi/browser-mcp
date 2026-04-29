# browser-mcp justfile
set shell := ["powershell.exe", "-NoProfile", "-Command"]

install:
    uv sync
    playwright install chromium

lint:
    uv run ruff check src/ tests/

fmt:
    uv run ruff format src/ tests/

test:
    uv run pytest -q

check:
    uv run python -c "import browser_mcp; print('OK')"
