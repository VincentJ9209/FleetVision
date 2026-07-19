#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$WorkspaceRoot,

    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$Config = "configs/data/team_pairing_audit_config.yaml",
    [string]$Python = "G:\Project\FleetVision\.venv\Scripts\python.exe",
    [ValidateRange(1, 65535)]
    [int]$Port = 8501
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

try {
    $AppScript = Join-Path $ProjectRoot "scripts\phase05s_run_team_pairing_review_app.py"
    $ConfigPath = if ([IO.Path]::IsPathRooted($Config)) {
        $Config
    }
    else {
        Join-Path $ProjectRoot $Config
    }

    foreach ($RequiredPath in @(
        $ProjectRoot,
        $Python,
        $AppScript,
        $ConfigPath,
        $WorkspaceRoot
    )) {
        if (-not (Test-Path -LiteralPath $RequiredPath)) {
            throw "Required path missing: $RequiredPath"
        }
    }

    Set-Location $ProjectRoot
    Write-Host "WRAPPER_OUTCOME=PASS"
    Write-Host "NETWORK_BIND=127.0.0.1"

    & $Python -m streamlit run $AppScript `
        --server.address=127.0.0.1 `
        --server.port=$Port `
        --server.headless=true `
        --browser.gatherUsageStats=false `
        -- `
        --config $Config `
        --project-root $ProjectRoot `
        --workspace-root $WorkspaceRoot

    exit $LASTEXITCODE
}
catch {
    Write-Host "WRAPPER_OUTCOME=BLOCKED"
    Write-Host "BLOCKING_REASON=$($_.Exception.Message)"
    throw
}
