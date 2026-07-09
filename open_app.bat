@echo off
TITLE Opening AI Stock Dashboard...

:: 1. Check if server is running (Looking for python process)
tasklist /FI "IMAGENAME eq python.exe" 2>NUL | find /I /N "python.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Server is already running.
) else (
    echo Server is NOT running. Starting it now...
    cscript //Nologo "c:\stock market\start_dashboard_hidden.vbs"
    echo Waiting for server to initialize...
    timeout /t 3 /nobreak >nul
)

:: 2. Open Browser
echo Opening Dashboard...
start http://127.0.0.1:5004

:: 3. Exit launcher
exit
