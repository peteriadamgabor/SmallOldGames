@echo off
setlocal

set PROJECT_ROOT=%~dp0..
cd /d "%PROJECT_ROOT%"

call uv sync --extra build
if errorlevel 1 exit /b 1

call uv run pyinstaller --noconfirm SmallOldGames.spec
if errorlevel 1 exit /b 1

echo.
echo Build complete.
echo Executable: dist\SmallOldGames\SmallOldGames.exe
