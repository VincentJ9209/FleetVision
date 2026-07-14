#requires -Version 5.1
[CmdletBinding()]
param(
    [string]$ProjectRoot = "G:\Project\FleetVision",
    [string]$Config = "configs\data\phase04_5m_annotation_correction_review_config.yaml",
    [Parameter(Mandatory = $true)][string]$WorkspaceRoot
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Script = Join-Path $ProjectRoot "scripts\phase04_5_export_annotation_correction_review.py"
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) { throw "Python not found: $Python" }
if (-not (Test-Path -LiteralPath $Script -PathType Leaf)) { throw "Script not found: $Script" }
if (-not (Test-Path -LiteralPath $WorkspaceRoot -PathType Container)) { throw "Workspace not found: $WorkspaceRoot" }
& $Python $Script --project-root $ProjectRoot --config $Config --workspace-root $WorkspaceRoot
if ($LASTEXITCODE -ne 0) { throw "Phase 04.5M completed export failed" }
