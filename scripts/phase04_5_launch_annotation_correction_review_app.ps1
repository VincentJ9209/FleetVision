#requires -Version 5.1
[CmdletBinding()]
param(
    [string]$ProjectRoot = "G:\Project\FleetVision",
    [string]$Config = "configs\data\phase04_5m_annotation_correction_review_config.yaml",
    [Parameter(Mandatory = $true)][string]$WorkspaceRoot,
    [int]$Port = 8503
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Script = Join-Path $ProjectRoot "scripts\phase04_5_run_annotation_correction_review_app.py"
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) { throw "Python not found: $Python" }
if (-not (Test-Path -LiteralPath $Script -PathType Leaf)) { throw "Script not found: $Script" }
if (-not (Test-Path -LiteralPath $WorkspaceRoot -PathType Container)) { throw "Workspace not found: $WorkspaceRoot" }
Write-Host "FleetVision 標註修正提案人工複核"
Write-Host "本機網址: http://127.0.0.1:$Port"
Write-Host "Live review state: SQLite"
Write-Host "TRAINING_STARTED: NO"
& $Python -m streamlit run $Script --server.address 127.0.0.1 --server.port $Port -- --project-root $ProjectRoot --config $Config --workspace-root $WorkspaceRoot
if ($LASTEXITCODE -ne 0) { throw "Phase 04.5M Streamlit app failed" }
