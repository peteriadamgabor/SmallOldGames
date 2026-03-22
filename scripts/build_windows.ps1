$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

uv sync --extra build
uv run pyinstaller --noconfirm SmallOldGames.spec

Write-Host ""
Write-Host "Build complete."
Write-Host "Executable: dist/SmallOldGames/SmallOldGames.exe"
