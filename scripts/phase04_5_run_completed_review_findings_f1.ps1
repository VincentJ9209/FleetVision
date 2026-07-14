#requires -Version 5.1

[CmdletBinding()]
param(
    [string]$ProjectRoot = "G:\Project\FleetVision",
    [string]$Config = "configs/data/phase04_5l_completed_review_findings_config.yaml",
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-fA-F]{40}$')]
    [string]$ExpectedHead,
    [string]$Timestamp = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Script = Join-Path $ProjectRoot "scripts\phase04_5_run_completed_review_findings_f1.py"
if (-not (Test-Path -LiteralPath $ProjectRoot -PathType Container)) { throw "Project root not found: $ProjectRoot" }
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) { throw "Python not found: $Python" }
if (-not (Test-Path -LiteralPath $Script -PathType Leaf)) { throw "F1 script not found: $Script" }

$Arguments = @(
    $Script,
    "--project-root", $ProjectRoot,
    "--config", $Config,
    "--expected-head", $ExpectedHead
)
if ($Timestamp) { $Arguments += @("--timestamp", $Timestamp) }

Push-Location -LiteralPath $ProjectRoot
try {
    & $Python @Arguments
    if ($LASTEXITCODE -ne 0) { throw "F1 blocked with exit code $LASTEXITCODE" }
}
finally {
    Pop-Location
}
