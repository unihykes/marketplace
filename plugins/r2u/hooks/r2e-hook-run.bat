@echo off
setlocal enabledelayedexpansion

set "EVENT_NAME=%1"
>>"D:\unihykes\marketplace\log\r2u.log" echo [!DATE! !TIME!] hook=%EVENT_NAME%

set "PYTHON_CMD="
where python >nul 2>&1
if not errorlevel 1 set "PYTHON_CMD=python"
if "%PYTHON_CMD%"=="" (
    where python3 >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=python3"
)

if "%PYTHON_CMD%"=="" (
    >>"D:\unihykes\marketplace\log\r2u.log" echo [!DATE! !TIME!] [ERROR] python not found, hooks disabled
    exit /b 0
)

set "SCRIPT_DIR=%~dp0"
set "PY_SCRIPT=%SCRIPT_DIR%r2e_hook_on_%EVENT_NAME%.py"

%PYTHON_CMD% "%PY_SCRIPT%"
if errorlevel 1 exit /b 2
exit /b 0
