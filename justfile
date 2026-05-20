set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]

# browser-mcp justfile
set shell := ["powershell.exe", "-NoProfile", "-Command"]

# Open the interactive recipe dashboard in the browser
default:
    @pwsh.exe -NoProfile -ExecutionPolicy Bypass -File ../mcp-central-docs/scripts/just-dashboard.ps1 -Path .

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
