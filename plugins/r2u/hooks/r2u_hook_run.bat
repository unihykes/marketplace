@echo off
set "LOG_FILE=%~dp0..\..\..\.codex\logs\hooks.log"
if not exist "%LOG_FILE%" (
    for %%F in ("%LOG_FILE%") do mkdir "%%~dpF" 2>nul
)
set "PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python"
set "EVENT_NAME=%~1"
set "PY_SCRIPT=%~dp0r2u_hook_on_%EVENT_NAME%.py"
set "TMP_SCRIPT=%~dp0r2u_hook_on_default.py"

echo [%date% %time%] >> "%LOG_FILE%"
echo [%date% %time%] PLUGIN_ROOT=%PLUGIN_ROOT% >> "%LOG_FILE%"
echo [%date% %time%] PLUGIN_DATA=%PLUGIN_DATA% >> "%LOG_FILE%"
echo [%date% %time%] PYTHON=%PYTHON% >> "%LOG_FILE%"
echo [%date% %time%] PY_SCRIPT=%PY_SCRIPT% >> "%LOG_FILE%"

"%PYTHON%" "%TMP_SCRIPT%" 2>> "%LOG_FILE%"
if %ERRORLEVEL% neq 0 (
    echo [%date% %time%] Hook failed with exit code %ERRORLEVEL% >> "%LOG_FILE%"
)
