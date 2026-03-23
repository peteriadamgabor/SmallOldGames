$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

uv sync --extra build
uv run pyinstaller --noconfirm SmallOldGames.spec

$archivePath = "dist/SmallOldGames-windows-x64.zip"
if (Test-Path $archivePath) {
    Remove-Item $archivePath -Force
}
Compress-Archive -Path "dist/SmallOldGames.exe" -DestinationPath $archivePath

Write-Host ""
Write-Host "Build complete."
Write-Host "Executable: dist/SmallOldGames.exe"
Write-Host "Archive: $archivePath"
