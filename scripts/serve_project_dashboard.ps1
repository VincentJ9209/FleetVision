[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [ValidateRange(1024, 65535)]
    [int]$Port = 8765,

    [Parameter(Mandatory = $false)]
    [string]$ProjectRoot,

    [Parameter(Mandatory = $false)]
    [switch]$NoBrowser
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
} else {
    $ProjectRoot = (Resolve-Path $ProjectRoot).Path
}

$dashboardRoot = Join-Path $ProjectRoot "docs\00_project_management\project_dashboard"
$requiredFiles = @(
    "index.html",
    "assets\dashboard.css",
    "assets\dashboard.js",
    "data\project_status.json",
    "data\project_history.json"
)

$missingFiles = @()
foreach ($relativePath in $requiredFiles) {
    $candidate = Join-Path $dashboardRoot $relativePath
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
        $missingFiles += $candidate
    }
}
if ($missingFiles.Count -gt 0) {
    throw "Dashboard required file(s) missing: $($missingFiles -join '; ')"
}

$pythonCommand = Get-Command "python" -ErrorAction SilentlyContinue
$pythonExecutable = $null
$pythonPrefixArguments = @()
if ($null -ne $pythonCommand) {
    $pythonExecutable = $pythonCommand.Source
} else {
    $pyCommand = Get-Command "py" -ErrorAction SilentlyContinue
    if ($null -eq $pyCommand) {
        throw "Python was not found. Install Python 3 or add python.exe / py.exe to PATH."
    }
    $pythonExecutable = $pyCommand.Source
    $pythonPrefixArguments = @("-3")
}

$listener = New-Object System.Net.Sockets.TcpListener -ArgumentList ([System.Net.IPAddress]::Loopback, $Port)
try {
    $listener.Start()
} catch {
    throw "Port $Port is unavailable on 127.0.0.1. Choose another port. Details: $($_.Exception.Message)"
} finally {
    try { $listener.Stop() } catch { }
}

$url = "http://127.0.0.1:$Port/"

Write-Host "============================================================"
Write-Host " FleetVision Local Project Dashboard"
Write-Host "============================================================"
Write-Host ("Project root:      {0}" -f $ProjectRoot)
Write-Host ("Dashboard root:    {0}" -f $dashboardRoot)
Write-Host ("Loopback URL:      {0}" -f $url)
Write-Host ("Browser auto-open: {0}" -f (-not $NoBrowser.IsPresent))
Write-Host "Repository writes: NO"
Write-Host "N1 / N2 execution: NO"
Write-Host "Stop server:       Press Ctrl+C"
Write-Host "============================================================"

if (-not $NoBrowser.IsPresent) {
    Start-Process $url
}

$arguments = @()
$arguments += $pythonPrefixArguments
$arguments += @(
    "-m",
    "http.server",
    [string]$Port,
    "--bind",
    "127.0.0.1",
    "--directory",
    $dashboardRoot
)

& $pythonExecutable @arguments
exit $LASTEXITCODE
