#requires -Version 5.1

[CmdletBinding()]
param(
    [string]$ProjectRoot = "G:\Project\FleetVision",
    [string]$Config = "configs/data/severity_scope_review_app_config.yaml",
    [string]$F1WorkspaceRoot = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Exporter = Join-Path $ProjectRoot "scripts\phase04_5_export_severity_scope_review_app_workbook.py"

if (-not (Test-Path -LiteralPath $ProjectRoot -PathType Container)) {
    throw "Project root not found: $ProjectRoot"
}
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Python executable not found: $Python"
}
if (-not (Test-Path -LiteralPath $Exporter -PathType Leaf)) {
    throw "Scope review exporter not found: $Exporter"
}

$Arguments = @(
    $Exporter,
    "--config", $Config,
    "--project-root", $ProjectRoot
)
if ($F1WorkspaceRoot) {
    $Arguments += @("--f1-workspace-root", $F1WorkspaceRoot)
}

Push-Location -LiteralPath $ProjectRoot
try {
    & $Python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Scope review export failed with code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}
