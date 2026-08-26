@echo off
cd /d "%~dp0"
echo === Ship Mechanic Assistant - Update ===
echo.

REM Receives the latest version from the git repository, then refreshes
REM libraries and the local AI model. Your manuals, API key (.env) and
REM settings are kept - they are git-ignored and never touched.

where git >nul 2>&1
if errorlevel 1 (
  echo Git is not installed - it is needed to receive updates.
  echo Install it from https://git-scm.com/download/win then run update again.
  pause
  exit /b 1
)
if not exist ".git" (
  echo This folder is not connected to the update server.
  echo Ask for a fresh copy that supports updating.
  pause
  exit /b 1
)

echo [1/3] Downloading the latest version...
git fetch origin
if errorlevel 1 (
  echo   Could not reach the update server. Check the internet connection.
  pause
  exit /b 1
)
git reset --hard origin/main
if errorlevel 1 (
  echo   Update failed. Please ask for help.
  pause
  exit /b 1
)

echo [2/3] Updating libraries...
if not exist venv (
  echo   No environment found - run setup.bat instead.
  pause
  exit /b 1
)
call venv\Scripts\activate
python -m pip install -r requirements.txt

echo [3/3] Updating the local AI model (if Ollama is installed)...
where ollama >nul 2>&1
if not errorlevel 1 (
  ollama pull qwen2.5:7b
) else (
  echo   Ollama not installed - skipping.
)

echo.
echo Update complete. Your manuals, API key and settings were kept.
echo Current version:
git log -1 --format="  %%cd  %%s" --date=short
echo.
pause
