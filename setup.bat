@echo off
REM Setup script for PCBAI (Windows)

echo === PCBAI Setup ===
echo.

REM Check Python
echo Checking Python...
where python >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Python found
) else (
    echo ❌ Python not found! Please install Python 3.10+
    exit /b 1
)

REM Check Java
echo.
echo Checking Java...
where java >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Java found
) else (
    echo ⚠ Java not found. Install Java for FreeRouting
    echo Download from: https://www.java.com/download/
)

REM Create virtual environment
echo.
echo Creating virtual environment...
python -m venv venv
echo ✓ Virtual environment created

REM Activate and install
echo.
echo Installing dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -e ".[dev]"

echo.
echo === Setup Complete! ===
echo.
echo Next steps:
echo   1. Activate venv: venv\Scripts\activate
echo   2. Check system: pcba check
echo   3. Download FreeRouting: pcba download-freerouting
echo   4. Try example: pcba inspect examples\simple_led.kicad_pcb
echo.
