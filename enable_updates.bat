@echo off
cd /d "%~dp0"
echo === Connecting this copy to updates (one-time) ===
echo.

REM Address of the update server. Filled in by the maintainer.
set REPO_URL=PUT-REPOSITORY-URL-HERE

echo %REPO_URL% | findstr /C:"PUT-REPOSITORY-URL-HERE" >nul
if not errorlevel 1 (
  echo This file is not configured yet - ask for an updated copy.
  pause
  exit /b 1
)

where git >nul 2>&1
if errorlevel 1 (
  echo Git is not installed - it is needed for updates.
  echo Install it from https://git-scm.com/download/win then run this again.
  pause
  exit /b 1
)

if exist ".git" (
  echo This copy is already connected to updates.
  echo Just use update.bat from now on.
  pause
  exit /b 0
)

echo Connecting and downloading the latest version...
git init -b main -q
git remote add origin %REPO_URL%
git fetch origin
if errorlevel 1 (
  echo   Could not reach the update server. Check the internet connection.
  pause
  exit /b 1
)
git reset --hard origin/main
if errorlevel 1 (
  echo   Could not apply the update. Please ask for help.
  pause
  exit /b 1
)
git branch --set-upstream-to=origin/main main >nul 2>&1

echo.
echo Done. This copy is now up to date and connected.
echo From now on, just double-click update.bat to get new versions.
echo Your manuals, API key and settings were kept.
echo.
pause
