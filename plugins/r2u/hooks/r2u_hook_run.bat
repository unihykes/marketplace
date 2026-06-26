@echo off
set "LOG_FILE=%cd%\.codex\logs\hooks.log"
set "EXECUTOR=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
set "EVENT_NAME=%~1"
set "EVENT_SCRIPT=%~dp0r2u_hook_on_%EVENT_NAME%.py"

:: call :write_log "PLUGIN_ROOT=%PLUGIN_ROOT%"
:: call :write_log "PLUGIN_DATA=%PLUGIN_DATA%"
:: call :write_log "EXECUTOR=%EXECUTOR%"

if not exist "%LOG_FILE%" (
    for %%F in ("%LOG_FILE%") do mkdir "%%~dpF" 2>nul
)

call :write_log "execute %EVENT_SCRIPT%"
"%EXECUTOR%" "%EVENT_SCRIPT%" 2>> "%LOG_FILE%"
set "HOOK_EXIT_CODE=%ERRORLEVEL%"

if %HOOK_EXIT_CODE% neq 0 (
    call :write_log "hook failed with exit code %HOOK_EXIT_CODE%"
)

exit /b %HOOK_EXIT_CODE%

:write_log
set "LOG_DATE=%date%"
for /f "tokens=1,*" %%a in ("%LOG_DATE%") do if not "%%b"=="" set "LOG_DATE=%%b"
set "LOG_TIME=%time: =0%"
echo [%LOG_DATE% %LOG_TIME%] %~1>> "%LOG_FILE%"
exit /b 0
