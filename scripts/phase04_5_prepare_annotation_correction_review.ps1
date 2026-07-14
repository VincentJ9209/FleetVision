#requires -Version 5.1
[CmdletBinding()]
param(
    [string]$ProjectRoot = "G:\Project\FleetVision",
    [string]$Config = "configs\data\phase04_5m_annotation_correction_review_config.yaml",
    [Parameter(Mandatory = $true)][string]$F2WorkspaceRoot,
    [string]$Timestamp = ""
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Script = Join-Path $ProjectRoot "scripts\phase04_5_prepare_annotation_correction_review.py"
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) { throw "Python not found: $Python" }
if (-not (Test-Path -LiteralPath $Script -PathType Leaf)) { throw "Script not found: $Script" }
if (-not (Test-Path -LiteralPath $F2WorkspaceRoot -PathType Container)) { throw "F2 workspace not found: $F2WorkspaceRoot" }
$Args = @($Script, "--project-root", $ProjectRoot, "--config", $Config, "--f2-workspace-root", $F2WorkspaceRoot)
if ($Timestamp) { $Args += @("--timestamp", $Timestamp) }
& $Python @Args
if ($LASTEXITCODE -ne 0) { throw "Phase 04.5M package preparation failed" }
