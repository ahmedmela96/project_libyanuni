@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ==========================================
echo   Ehsan Project - Local Run (Windows)
echo ==========================================

echo [1/5] Checking Python ...
where py >nul 2>nul
if %errorlevel%==0 (
  set "PY_CMD=py -3"
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    set "PY_CMD=python"
  ) else (
    echo [ERROR] Python is not installed or not in PATH.
    echo Install Python 3.10+ then re-run this file.
    pause
    exit /b 1
  )
)

if exist "ehsan.db" (
  echo [2/5] Existing database found (ehsan.db) - keeping your data.
  set "FIRST_RUN=0"
) else (
  echo [2/5] No database found. Initializing new database ...
  %PY_CMD% init_db.py
  if errorlevel 1 goto :failed
  set "FIRST_RUN=1"
)

echo [3/5] Applying DB migration ...
%PY_CMD% migrate_db.py
if errorlevel 1 goto :failed

if "%FIRST_RUN%"=="1" (
  echo [4/5] Migrating passwords for first-time login flow ...
  %PY_CMD% migrate_passwords.py
  if errorlevel 1 goto :failed
) else (
  echo [4/5] Skipping password migration to preserve existing accounts.
)

echo [5/5] Starting server on http://localhost:8000 ...
echo Login: admin / admin123
echo Opening the platform in your default browser...
start "" http://localhost:8000
%PY_CMD% server.py
if errorlevel 1 goto :failed

goto :eof

:failed
echo.
echo [FAILED] A step failed. Check the error above.
pause
exit /b 1
