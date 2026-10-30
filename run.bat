@echo off
title TerraScout AI - Touch Grass
echo ========================================================
echo   TERRASCOUT AI - BACKCOUNTRY TRAIL & NATURALIST
echo   Powered by Google Gemma 2B Open-Weight Intelligence
echo ========================================================
echo.
echo Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH! Please install Python 3.10+.
    pause
    exit /b 1
)

echo.
echo [1/2] Starting local Field Server on http://localhost:8081...
start "" "http://localhost:8081"
python backend/app.py 8081
pause
