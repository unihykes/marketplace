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
set "R2U_DIR=%SOURCE_DIR%\..\r2u"
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

call :copy_dir_optional ".cursor-plugin"
if errorlevel 1 exit /b 1

call :copy_dir_optional "rules"
if errorlevel 1 exit /b 1

call :copy_dir_optional "skills"
if errorlevel 1 exit /b 1

call :copy_dir_optional "%R2U_DIR%\skills" "skills"
if errorlevel 1 exit /b 1

call :copy_dir_optional "agents"
if errorlevel 1 exit /b 1

call :copy_dir_optional "commands"
if errorlevel 1 exit /b 1

call :copy_dir_optional "hooks\windows" "hooks"
if errorlevel 1 exit /b 1

echo Plugin installed successfully. Please restart Cursor
timeout /t 10 /nobreak >nul
exit /b 0

:copy_dir_optional
set "COPY_TARGET_NAME=%~2"
if "%COPY_TARGET_NAME%"=="" set "COPY_TARGET_NAME=%~1"
set "COPY_SOURCE=%~1"
if not exist "%COPY_SOURCE%\" set "COPY_SOURCE=%SOURCE_DIR%\%~1"
if not exist "%COPY_SOURCE%\" exit /b 0
robocopy "%COPY_SOURCE%" "%TARGET_DIR%\%COPY_TARGET_NAME%" /e >nul
set "ROBOCOPY_EXIT=%errorlevel%"
if %ROBOCOPY_EXIT% GEQ 8 (
  call :fail "Failed to copy %COPY_SOURCE% to %COPY_TARGET_NAME%. (robocopy exit code: %ROBOCOPY_EXIT%)"
)
exit /b 0

:fail
if not "%~1"=="" echo [ERROR] %~1
timeout /t 10 /nobreak >nul
exit /b 1
