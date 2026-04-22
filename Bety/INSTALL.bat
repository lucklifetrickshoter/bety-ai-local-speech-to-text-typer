@echo off
title Bety: The Privacy-First Universal Dictator -- Setup & Build
color 0D
echo.
echo  ============================================================
echo   Bety -- One-Click Setup ^& Build
echo  ============================================================
echo.

:: ------------------------------------------------------------------
:: 1. Find Python
:: ------------------------------------------------------------------
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python was not found on this computer.
    echo.
    echo  Please install Python 3.10 or newer from:
    echo  https://www.python.org/downloads/
    echo.
    echo  IMPORTANT: On the installer screen, tick the box that says
    echo  "Add Python to PATH" before clicking Install.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYVER=%%i
echo  Found: %PYVER%
echo.

:: ------------------------------------------------------------------
:: 2. Create virtual environment (if it doesn't already exist)
:: ------------------------------------------------------------------
if not exist venv\ (
    echo  [1/4] Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo  [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo  Done.
    echo.
) else (
    echo  [1/4] Virtual environment already exists -- skipping.
    echo.
)

:: ------------------------------------------------------------------
:: 3. Install dependencies
:: ------------------------------------------------------------------
echo  [2/4] Installing dependencies (this may take a few minutes)...
echo        faster-whisper will also download the Whisper AI model
echo        (~145 MB) on first run -- internet required just this once.
echo.
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] pip install failed. Check your internet connection
    echo  and try running this script again.
    pause
    exit /b 1
)
echo  Done.
echo.

:: ------------------------------------------------------------------
:: 4. Build the .exe with PyInstaller
:: ------------------------------------------------------------------
echo  [3/4] Building the .exe (this takes 1-3 minutes)...
python build.py
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Build failed. See the output above for details.
    pause
    exit /b 1
)
echo.

:: ------------------------------------------------------------------
:: 5. Done
:: ------------------------------------------------------------------
echo  [4/4] All done!
echo.
echo  ============================================================
echo   Your .exe is ready here:
echo   %~dp0dist\Bety\Bety.exe
echo.
echo   To share with someone who doesn't have Python:
echo   Zip up the ENTIRE "dist\Bety\" folder
echo   and send them that zip -- everything is self-contained.
echo  ============================================================
echo.
set /p LAUNCH="   Launch Bety now? (Y/N): "
if /i "%LAUNCH%"=="Y" (
    start "" "%~dp0dist\Bety\Bety.exe"
)
echo.
pause
