@echo off
echo Restarting Stock Market Dashboard...

:: 1. Kill invalid processes
echo Killing existing python processes...
taskkill /F /IM python.exe /T 2>nul

:: 2. Wait a moment
timeout /t 2 /nobreak >nul

:: 3. Start the dashboard in a new window
echo Starting application...
start "" "start_dashboard.bat"

echo Restart initiated. You can close this window.
timeout /t 3
