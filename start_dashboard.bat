@echo off
TITLE Stock Market Dashboard
echo Starting Stock Market Dashboard...
cd /d "%~dp0"

:: Check if python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    pause
    exit /b
)

:: Run the application
echo Launching Flask Server on Port 5004...
python run.py

if %errorlevel% neq 0 (
    echo Application crashed!
    pause
)
