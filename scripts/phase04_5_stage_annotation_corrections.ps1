#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ProjectRoot,
    [Parameter(Mandatory = $true)][string]$Config,
    [Parameter(Mandatory = $true)][string]$CompletedReviewWorkspace,
    [Parameter(Mandatory = $true)][string]$Timestamp
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $ProjectRoot -PathType Container)) {
    throw "Project root does not exist: $ProjectRoot"
}

# Every FleetVision PowerShell entrypoint sets its own execution location.
Set-Location -LiteralPath $ProjectRoot

$ProjectPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Python = $ProjectPython

# Test-only/environment recovery override. Production uses the project .venv.
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    $Override = [Environment]::GetEnvironmentVariable("FLEETVISION_PYTHON")
    if (-not [string]::IsNullOrWhiteSpace($Override)) {
        $Python = $Override
    }
}

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "FleetVision Python not found: $ProjectPython"
}

$ScriptPath = Join-Path $ProjectRoot "scripts\phase04_5_stage_annotation_corrections.py"
if (-not (Test-Path -LiteralPath $ScriptPath -PathType Leaf)) {
    throw "Phase 04.5N Python entrypoint not found: $ScriptPath"
}

& $Python `
    $ScriptPath `
    --project-root $ProjectRoot `
    --config $Config `
    --completed-review-workspace $CompletedReviewWorkspace `
    --timestamp $Timestamp

$PythonExitCode = $LASTEXITCODE
if ($PythonExitCode -ne 0) {
    exit $PythonExitCode
}
