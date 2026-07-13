#requires -Version 5.1

[CmdletBinding()]
param(
    [string]$ProjectRoot = "G:\Project\FleetVision",
    [string]$Config = "configs/data/validation_error_review_app_config.yaml",
    [switch]$Headless,
    [int]$Port = 8501,
    [string]$Address = "127.0.0.1",
    [string]$WorkspaceRoot = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Launcher = Join-Path $ProjectRoot "scripts\phase04_5_run_validation_error_review_app.py"

if (-not (Test-Path -LiteralPath $ProjectRoot -PathType Container)) {
    throw "Project root not found: $ProjectRoot"
}
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Python executable not found: $Python"
}
if (-not (Test-Path -LiteralPath $Launcher -PathType Leaf)) {
    throw "Review app launcher not found: $Launcher"
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
if ($Headless) {
    $Arguments += "--headless"
}
if ($WorkspaceRoot) {
    $Arguments += @("--workspace-root", $WorkspaceRoot)
}

Push-Location -LiteralPath $ProjectRoot
try {
    & $Python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Review app exited with code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}
