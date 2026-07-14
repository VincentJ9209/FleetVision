#requires -Version 5.1

[CmdletBinding()]
param(
    [string]$ProjectRoot = "G:\Project\FleetVision",
    [string]$Config = "configs/data/severity_scope_review_app_config.yaml",
    [string]$F1WorkspaceRoot = "",
    [switch]$Headless,
    [int]$Port = 8502,
    [string]$Address = "127.0.0.1"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Launcher = Join-Path $ProjectRoot "scripts\phase04_5_run_severity_scope_review_app.py"

if (-not (Test-Path -LiteralPath $ProjectRoot -PathType Container)) {
    throw "Project root not found: $ProjectRoot"
}
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Python executable not found: $Python"
}
if (-not (Test-Path -LiteralPath $Launcher -PathType Leaf)) {
    throw "Scope review app launcher not found: $Launcher"
}
if ($Port -lt 1 -or $Port -gt 65535) {
    throw "Port must be between 1 and 65535."
}

$Arguments = @(
    $Launcher,
    "--config", $Config,
    "--project-root", $ProjectRoot,
    "--port", $Port,
    "--address", $Address
)
if ($F1WorkspaceRoot) {
    $Arguments += @("--f1-workspace-root", $F1WorkspaceRoot)
}
if ($Headless) {
    $Arguments += "--headless"
}

Write-Host "============================================================"
Write-Host " FleetVision Severity Scope Review App"
Write-Host "============================================================"
Write-Host "介面語言: 繁體中文"
Write-Host "本機網址: http://${Address}:$Port"
Write-Host "Live review state: SQLite"
Write-Host "Excel role: completed export only"
Write-Host "F2 executed: NO"
Write-Host ""

Push-Location -LiteralPath $ProjectRoot
try {
    & $Python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Scope review app exited with code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}
