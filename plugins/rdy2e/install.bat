@echo off
setlocal EnableDelayedExpansion

if not "%~2"=="" (
  echo [ERROR] Too many arguments.
  echo Usage: %~nx0 ["PROJECT_ROOT_PATH"]
  call :fail
)

if "%~1"=="" (
  set "PROJECT_ROOT=%USERPROFILE%"
) else (
  set "PROJECT_ROOT=%~1"
)

set "SOURCE_DIR=%~dp0."
set "TARGET_DIR=%PROJECT_ROOT%\.cursor\plugins\local\r2e"

echo Source: %SOURCE_DIR% ^| Target: %TARGET_DIR%

if not exist "%SOURCE_DIR%\.cursor-plugin\plugin.json" (
  call :fail "Plugin manifest not found: %SOURCE_DIR%\.cursor-plugin\plugin.json"
)

if exist "%TARGET_DIR%\" (
  echo Removing existing plugin: %TARGET_DIR%
  rmdir /s /q "%TARGET_DIR%"
  if errorlevel 1 (
    call :fail "Failed to remove existing plugin directory."
  )
)

mkdir "%TARGET_DIR%" >nul 2>&1

call :copy_dir ".cursor-plugin"
if errorlevel 1 exit /b 1

call :copy_dir "rules"
if errorlevel 1 exit /b 1

call :copy_dir "skills"
if errorlevel 1 exit /b 1

call :copy_dir "agents"
if errorlevel 1 exit /b 1

call :copy_dir "commands"
if errorlevel 1 exit /b 1

robocopy "%SOURCE_DIR%\hooks\windows" "%TARGET_DIR%\hooks" /e >nul
set "ROBOCOPY_EXIT=%errorlevel%"
if %ROBOCOPY_EXIT% GEQ 8 (
  call :fail "Failed to copy hooks from hooks\windows. (robocopy exit code: %ROBOCOPY_EXIT%)"
)

echo Plugin installed successfully. Please restart Cursor
timeout /t 10 /nobreak >nul
exit /b 0

:copy_dir
set "COPY_NAME=%~1"
robocopy "%SOURCE_DIR%\%COPY_NAME%" "%TARGET_DIR%\%COPY_NAME%" /e >nul
set "ROBOCOPY_EXIT=%errorlevel%"
if %ROBOCOPY_EXIT% GEQ 8 (
  call :fail "Failed to copy %COPY_NAME%. (robocopy exit code: %ROBOCOPY_EXIT%)"
)
exit /b 0

:fail
if not "%~1"=="" echo [ERROR] %~1
timeout /t 10 /nobreak >nul
exit /b 1
