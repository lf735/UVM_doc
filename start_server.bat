@echo off
setlocal
cd /d "%~dp0"

set PORT=8000
echo Starting UVM 1.2 Documentation Server on http://localhost:%PORT%
echo Press Ctrl+C to stop the server.
echo.

python -m http.server %PORT%

