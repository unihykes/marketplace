@echo off
set "LOG_FILE=%cd%\.codex\logs\hooks.log"
set "EXECUTOR=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
set "EVENT_NAME=%~1"
set "EVENT_SCRIPT=%~dp0r2u_hook_on_%EVENT_NAME%.py"

:: echo [%date% %time%] PLUGIN_ROOT=%PLUGIN_ROOT% >> "%LOG_FILE%"
:: echo [%date% %time%] PLUGIN_DATA=%PLUGIN_DATA% >> "%LOG_FILE%"
:: echo [%date% %time%] EXECUTOR=%EXECUTOR% >> "%LOG_FILE%"

if not exist "%LOG_FILE%" (
    for %%F in ("%LOG_FILE%") do mkdir "%%~dpF" 2>nul
)

echo [%date% %time%] execute %EVENT_SCRIPT% >> "%LOG_FILE%"
"%EXECUTOR%" "%EVENT_SCRIPT%" 2>> "%LOG_FILE%"

if %ERRORLEVEL% neq 0 (
    echo [%date% %time%] hook failed with exit code %ERRORLEVEL% >> "%LOG_FILE%"
)