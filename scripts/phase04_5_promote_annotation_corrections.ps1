#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ProjectRoot,
    [Parameter(Mandatory = $true)][string]$Config,
    [Parameter(Mandatory = $true)][string]$N1Workspace,
    [Parameter(Mandatory = $true)][string]$ExpectedRepositoryHead,
    [Parameter(Mandatory = $true)][string]$ExpectedCanonicalSha256,
    [Parameter(Mandatory = $true)][string]$ExpectedStagedSha256,
    [string]$AuthorizationPhrase = "",
    [Parameter(Mandatory = $true)][string]$Timestamp,
    [switch]$DryRun,
    [switch]$Execute
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $ProjectRoot -PathType Container)) {
    throw "Project root does not exist: $ProjectRoot"
}

# Every FleetVision PowerShell entrypoint sets its own execution location.
Set-Location -LiteralPath $ProjectRoot

if ($DryRun -and $Execute) {
    throw "DryRun and Execute are mutually exclusive"
}

$ProjectPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Python = $ProjectPython
$Override = [Environment]::GetEnvironmentVariable("FLEETVISION_PYTHON")
if (-not [string]::IsNullOrWhiteSpace($Override)) {
    $Python = $Override
}
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "FleetVision Python not found: $ProjectPython"
}

$ScriptPath = Join-Path $ProjectRoot "scripts\phase04_5_promote_annotation_corrections.py"
if (-not (Test-Path -LiteralPath $ScriptPath -PathType Leaf)) {
    throw "Phase 04.5N promotion Python entrypoint not found: $ScriptPath"
}

$Arguments = @(
    $ScriptPath,
    "--project-root", $ProjectRoot,
    "--config", $Config,
    "--n1-workspace", $N1Workspace,
    "--expected-repository-head", $ExpectedRepositoryHead,
    "--expected-canonical-sha256", $ExpectedCanonicalSha256,
    "--expected-staged-sha256", $ExpectedStagedSha256
)

# Windows PowerShell 5.1 can drop empty native arguments. Omit this option
# when empty so argparse uses the Python default of an empty string.
if (-not [string]::IsNullOrEmpty($AuthorizationPhrase)) {
    $Arguments += @("--authorization-phrase", $AuthorizationPhrase)
}

$Arguments += @("--timestamp", $Timestamp)

if ($Execute) {
    $Arguments += "--execute"
}
else {
    # Neither switch defaults safely to the read-only mode.
    $Arguments += "--dry-run"
}

$StderrPath = Join-Path $env:TEMP (
    "FleetVision_Phase04_5N_N2_Stderr_" + [Guid]::NewGuid().ToString("N") + ".log"
)

$PreviousErrorActionPreference = $ErrorActionPreference
try {
    # Windows PowerShell 5.1 can promote native stderr to ErrorRecord when
    # ErrorActionPreference=Stop. Redirect stderr and trust the native exit code.
    $ErrorActionPreference = "Continue"
    & $Python @Arguments 2> $StderrPath
    $PythonExitCode = $LASTEXITCODE
}
finally {
    $ErrorActionPreference = $PreviousErrorActionPreference
}

if (Test-Path -LiteralPath $StderrPath -PathType Leaf) {
    $StderrText = [System.IO.File]::ReadAllText($StderrPath)
    if (-not [string]::IsNullOrEmpty($StderrText)) {
        [Console]::Error.Write($StderrText)
    }
    Remove-Item -LiteralPath $StderrPath -Force
}

exit $PythonExitCode
