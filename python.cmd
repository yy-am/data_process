@echo off
setlocal
set "SCRIPT_DIR=%~dp0"

if exist "%SCRIPT_DIR%\.venv\Scripts\python.exe" (
  "%SCRIPT_DIR%\.venv\Scripts\python.exe" %*
  exit /b %errorlevel%
)

where python >nul 2>nul
if %errorlevel%==0 (
  python %*
  exit /b %errorlevel%
)

where py >nul 2>nul
if %errorlevel%==0 (
  py %*
  exit /b %errorlevel%
)

echo No usable Python runtime found. Please create .venv or install Python and add it to PATH.
exit /b 1
