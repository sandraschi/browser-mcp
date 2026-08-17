param([switch]$Headless, [switch]$BackendOnly, [switch]$NoBrowser)
$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $PSCommandPath
$BackendPort = 10780
$FrontendPort = 10781

$Host.UI.RawUI.WindowTitle = "browser-mcp - backend :$BackendPort / frontend :$FrontendPort"
if (-not $Headless) {
    Write-Host ""
    Write-Host "  browser-mcp" -ForegroundColor Cyan
    Write-Host "  BACKEND   http://127.0.0.1:$BackendPort   (REST /health, /api/*, MCP /mcp)" -ForegroundColor Gray
    Write-Host "  FRONTEND  http://127.0.0.1:$FrontendPort  (webapp UI)" -ForegroundColor Gray
    Write-Host ""
}

Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-NetTCPConnection -LocalPort $FrontendPort -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

$UV = "C:\Users\sandr\.local\bin\uv.exe"
$env:BROWSER_MCP_PORT = "$BackendPort"
$env:BROWSER_MCP_HOST = "127.0.0.1"
$BackendJob = Start-Job -Name "backend" -ScriptBlock {
    param($Root, $UV)
    Set-Location $Root
    & $UV run python -m browser_mcp --serve
} -ArgumentList $ScriptRoot, $UV

$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$BackendPort/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch {}
    Start-Sleep 1
}
if (-not $ready) {
    Receive-Job $BackendJob
    throw "Backend did not become ready on port $BackendPort after 60s"
}

if (-not $BackendOnly) {
    $WebRoot = Join-Path $ScriptRoot "webapp"
    $npm = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
    if (-not $npm) { throw "npm not found on PATH" }
    Start-Process -NoNewWindow -FilePath $npm -ArgumentList "run dev -- --port $FrontendPort --host" -WorkingDirectory $WebRoot

    if (-not $Headless -and -not $NoBrowser) {
        Start-Sleep 2
        Start-Process "http://127.0.0.1:$FrontendPort"
    }
}

while ($true) {
    if ($BackendJob.State -eq "Completed" -or $BackendJob.State -eq "Failed") {
        Receive-Job $BackendJob
        break
    }
    Start-Sleep 2
}
