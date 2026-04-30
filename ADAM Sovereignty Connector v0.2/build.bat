@echo off
REM ========================================================================
REM  ADAM Sovereignty Connector — Windows build script
REM
REM  Produces `dist\adam_sovereignty_connector.exe` — a single-file frozen
REM  Python app that embeds the deploy/ tree and web UI as bundled data.
REM
REM  Run from a Windows PowerShell / cmd window with Python 3.11+ installed
REM  on PATH:
REM     build.bat
REM  or for a clean rebuild:
REM     build.bat --clean
REM ========================================================================

setlocal EnableDelayedExpansion
cd /d %~dp0

if "%1"=="--clean" (
    echo [clean] removing build/ dist/ __pycache__
    rmdir /s /q build_work 2>nul
    rmdir /s /q dist 2>nul
    for /d /r %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
)

where py >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python launcher 'py' not found. Install Python 3.11+ first: https://www.python.org/downloads/windows/
    exit /b 1
)

echo [venv] creating .venv
if not exist .venv (
    py -3 -m venv .venv || exit /b 1
)
call .venv\Scripts\activate.bat

echo [pip] upgrading tooling
python -m pip install --upgrade pip wheel setuptools >nul

echo [pip] installing runtime deps
pip install -r requirements.txt || exit /b 1

echo [pip] installing pyinstaller
pip install pyinstaller>=6.10 || exit /b 1

echo [build] freezing application
pyinstaller ^
    --noconfirm ^
    --clean ^
    --workpath build_work ^
    --distpath dist ^
    build\adam_sovereignty_connector.spec || exit /b 1

if not exist dist\adam_sovereignty_connector.exe (
    echo ERROR: build produced no .exe. See logs above.
    exit /b 1
)

echo.
echo ==================================================================
echo   Built: dist\adam_sovereignty_connector.exe
echo   Next:
echo     1. Copy dist\adam_sovereignty_connector.exe to your target host
echo     2. Populate ADAM_Offline_Media\ next to the .exe
echo        (see media\MANIFEST.md and scripts\build_offline_media.ps1)
echo     3. Run:  adam_sovereignty_connector.exe init
echo              adam_sovereignty_connector.exe check
echo              adam_sovereignty_connector.exe install --yes
echo              adam_sovereignty_connector.exe bootstrap --yes
echo              adam_sovereignty_connector.exe deploy --yes
echo              adam_sovereignty_connector.exe serve --all
echo ==================================================================
endlocal
