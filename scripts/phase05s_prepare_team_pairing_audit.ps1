#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$WorkspaceRoot,

    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$Config = "configs/data/team_pairing_audit_config.yaml",
    [string]$Python = "G:\Project\FleetVision\.venv\Scripts\python.exe",
    [string]$CreatedAtUtc = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

try {
    $Entrypoint = Join-Path $ProjectRoot "scripts\phase05s_prepare_team_pairing_audit.py"
    $ConfigPath = if ([IO.Path]::IsPathRooted($Config)) {
        $Config
    }
    else {
        Join-Path $ProjectRoot $Config
    }

    foreach ($RequiredPath in @($ProjectRoot, $Python, $Entrypoint, $ConfigPath)) {
        if (-not (Test-Path -LiteralPath $RequiredPath)) {
            throw "Required path missing: $RequiredPath"
        }
    }
    if (Test-Path -LiteralPath $WorkspaceRoot) {
        throw "Workspace already exists; overwrite is forbidden: $WorkspaceRoot"
    }

    $Arguments = @(
        $Entrypoint,
        "--project-root", $ProjectRoot,
        "--config", $Config,
        "--workspace-root", $WorkspaceRoot
    )
    if ($CreatedAtUtc) {
        $Arguments += @("--created-at-utc", $CreatedAtUtc)
    }

    & $Python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Team Pairing prepare operation failed."
    }

    Write-Host "WRAPPER_OUTCOME=PASS"
    Write-Host "NEXT_ACTION=RUN_REVIEW_WRAPPER"
}
catch {
    Write-Host "WRAPPER_OUTCOME=BLOCKED"
    Write-Host "BLOCKING_REASON=$($_.Exception.Message)"
    throw
}
