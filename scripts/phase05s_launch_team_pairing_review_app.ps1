#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$WorkspaceRoot,
    [string]$ProjectRoot = "G:\Project\FleetVision_Worktrees\phase05s-a3-team-pairing-audit",
    [string]$Config = "configs/data/team_pairing_audit_config.yaml",
    [ValidateRange(1, 65535)][int]$Port = 8501
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Python = "G:\Project\FleetVision\.venv\Scripts\python.exe"
$AppScript = Join-Path $ProjectRoot "scripts\phase05s_run_team_pairing_review_app.py"

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Project Python not found: $Python"
}
if (-not (Test-Path -LiteralPath $AppScript -PathType Leaf)) {
    throw "Streamlit entrypoint not found: $AppScript"
}

Set-Location $ProjectRoot

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
