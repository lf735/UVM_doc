@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set PORT=8000

echo ============================================================
echo   UVM 1.2 Documentation Server
echo ============================================================
echo   Local URL      : http://localhost:%PORT%
echo   Mobile Preview : http://localhost:%PORT%/mobile_preview.html
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set "IP=%%a"
    set "IP=!IP: =!"
    echo   LAN / Mobile   : http://!IP!:%PORT%
)
echo ============================================================
echo Press Ctrl+C to stop the server.
echo.

python scripts\serve.py %PORT%
