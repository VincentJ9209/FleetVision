#requires -Version 5.1

[CmdletBinding()]
param(
    [string]$ProjectRoot = "G:\Project\FleetVision",
    [string]$Config = "configs/data/phase04_5l_completed_review_findings_config.yaml",
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-fA-F]{40}$')]
    [string]$ExpectedHead,
    [Parameter(Mandatory = $true)]
    [string]$WorkspaceRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Script = Join-Path $ProjectRoot "scripts\phase04_5_run_completed_review_findings_f2.py"
if (-not (Test-Path -LiteralPath $ProjectRoot -PathType Container)) { throw "Project root not found: $ProjectRoot" }
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) { throw "Python not found: $Python" }
if (-not (Test-Path -LiteralPath $Script -PathType Leaf)) { throw "F2 script not found: $Script" }
if (-not (Test-Path -LiteralPath $WorkspaceRoot -PathType Container)) { throw "Workspace root not found: $WorkspaceRoot" }

$Arguments = @(
    $Script,
    "--project-root", $ProjectRoot,
    "--config", $Config,
    "--expected-head", $ExpectedHead,
    "--workspace-root", $WorkspaceRoot
)

Push-Location -LiteralPath $ProjectRoot
try {
    & $Python @Arguments
    if ($LASTEXITCODE -ne 0) { throw "F2 blocked with exit code $LASTEXITCODE" }
}
finally {
    Pop-Location
}
