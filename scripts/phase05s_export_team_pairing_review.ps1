#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$WorkspaceRoot,

    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$Config = "configs/data/team_pairing_audit_config.yaml",
    [string]$Timestamp = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Entrypoint = Join-Path $ProjectRoot "scripts\phase05s_export_team_pairing_review.py"
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Project Python missing: $Python"
}
if (-not (Test-Path -LiteralPath $Entrypoint -PathType Leaf)) {
    throw "Exporter entrypoint missing: $Entrypoint"
}

$Arguments = @(
    $Entrypoint,
    "--project-root", $ProjectRoot,
    "--config", $Config,
    "--workspace-root", $WorkspaceRoot
)
if ($Timestamp) {
    $Arguments += @("--timestamp", $Timestamp)
}

& $Python @Arguments
if ($LASTEXITCODE -ne 0) {
    throw "Team Pairing completed export failed."
}
