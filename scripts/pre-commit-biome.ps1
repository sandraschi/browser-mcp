$ErrorActionPreference = "Stop"

# Detect the webapp root (web_sota/, webapp/frontend/, webapp/, web/)
$roots = @("web_sota", "webapp/frontend", "webapp", "web")
$webRoot = $null
foreach ($r in $roots) {
    if (Test-Path (Join-Path $PSScriptRoot "..\$r\package.json")) {
        $webRoot = Join-Path $PSScriptRoot "..\$r"
        break
    }
}
if (-not $webRoot) { exit 0 }

Push-Location $webRoot
try {
    npx biome check --write src/ 2>$null
    if ($LASTEXITCODE -ne 0) {
        # Biome not configured - fall back to no-op (eslint not installed either)
        Write-Host "biome unavailable or not configured - skipping" -ForegroundColor DarkYellow
        exit 0
    }
} finally {
    Pop-Location
}
exit 0
