<#
Clean local, generated Python/project artifacts that should not be committed.
This script does not remove dataset files, model files, Git history, or .env.
Run from the FleetVision project root.
#>

$ErrorActionPreference = "Stop"

Write-Host "Cleaning FleetVision local artifacts..."

$pathsToRemove = @(
    ".pytest_cache",
    "src/fleetvision.egg-info"
)

foreach ($path in $pathsToRemove) {
    if (Test-Path $path) {
        Remove-Item -Recurse -Force $path
        Write-Host "Removed $path"
    }
}

Get-ChildItem -Recurse -Directory -Filter "__pycache__" | ForEach-Object {
    Remove-Item -Recurse -Force $_.FullName
    Write-Host "Removed $($_.FullName)"
}

Get-ChildItem -Recurse -Directory -Filter ".ipynb_checkpoints" | ForEach-Object {
    Remove-Item -Recurse -Force $_.FullName
    Write-Host "Removed $($_.FullName)"
}

Write-Host "Cleanup complete. Next recommended checks:"
Write-Host "  git status --short"
Write-Host "  python scripts/phase00_init_project.py --validate"
Write-Host "  pytest"
