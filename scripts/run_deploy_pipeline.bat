@echo off
setlocal
cd /d "%~dp0\.."
echo ====================================================
echo Running Deploy Pipeline locally
echo ====================================================
python scripts\run_deploy_pipeline.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Pipeline execution failed!
    exit /b %ERRORLEVEL%
)
endlocal

