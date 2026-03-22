@echo off
setlocal

set PROJECT_ROOT=%~dp0..
cd /d "%PROJECT_ROOT%"

call uv sync --extra build
if errorlevel 1 exit /b 1

call uv run pyinstaller --noconfirm SmallOldGames.spec
if errorlevel 1 exit /b 1

if exist "dist\SmallOldGames-windows-x64.zip" del /f /q "dist\SmallOldGames-windows-x64.zip"
powershell -NoProfile -Command "Compress-Archive -Path 'dist/SmallOldGames/*' -DestinationPath 'dist/SmallOldGames-windows-x64.zip'"
if errorlevel 1 exit /b 1

echo.
echo Build complete.
echo Executable: dist\SmallOldGames\SmallOldGames.exe
echo Archive: dist\SmallOldGames-windows-x64.zip
