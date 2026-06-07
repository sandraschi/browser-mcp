# browser-mcp starter
param([switch]$BackendOnly)
$ErrorActionPreference = "Stop"
$Repo = $PSScriptRoot
$UV = "C:\Users\sandr\.local\bin\uv.exe"
Write-Host "=== browser-mcp ===" -ForegroundColor Cyan
& $UV run python -m browser_mcp
