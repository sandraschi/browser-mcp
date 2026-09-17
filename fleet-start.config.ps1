# Per-repo fleet start config for browser-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'browser-mcp'
    BackendPort  = 10780
    FrontendPort = 10781
    HealthPath   = '/health'
    WebRoot      = 'webapp'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'browser_mcp.app:app'
        SyncExtras    = @('dev')
        Env           = @{ WEB_PORT = '10780' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
