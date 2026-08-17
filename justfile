set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]
import 'scripts/just/fleet.just'

# browser-mcp justfile
set shell := ["powershell.exe", "-NoProfile", "-Command"]

# Open the interactive recipe dashboard in the browser
default:
    @just --list

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

# Start the backend in HTTP mode (REST + MCP on 10780)
serve:
    uv run python -m browser_mcp --serve

# Run all verification gates (lint, format, types, tests)
certify:
    uv run ruff check src/ tests/
    uv run ruff format src/ tests/ --check
    uv run pyright src/
    uv run pytest tests/ -q

# Build the Tauri NSIS desktop installer (full pipeline: frontend -> Rust -> NSIS)
build-native:
	$env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
	Set-Location '{{justfile_directory()}}\native'
	npx @tauri-apps/cli build --bundles nsis


# Bootstrap: install dev deps + pre-commit hook
bootstrap:
    uv sync --group dev
    uv run pre-commit install
    Write-Host "Pre-commit hooks installed." -ForegroundColor Green