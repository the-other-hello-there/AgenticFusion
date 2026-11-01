@echo off
setlocal
where py >nul 2>nul
if errorlevel 1 (
    echo Template updates require Python 3.11 or newer and the Windows py launcher.
    exit /b 1
)
py -3 "%~dp0.agents\scripts\update_template.py" --project-dir "%~dp0." %*
set "UPDATE_RESULT=%ERRORLEVEL%"
if "%~1"=="" pause
exit /b %UPDATE_RESULT%
