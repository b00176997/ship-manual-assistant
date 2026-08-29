@echo off
cd /d "%~dp0"
echo === Ship Mechanic Assistant - Update ===
echo.

REM Receives the latest version from the git repository, then refreshes
REM libraries, GPU support and the local AI model. Your manuals, API key
REM (.env) and settings are kept - they are git-ignored and never touched.

where git >nul 2>&1
if errorlevel 1 (
  echo Git is not installed - it is needed to receive updates.
  echo Install it from https://git-scm.com/download/win then run update again.
  pause
  exit /b 1
)
if not exist ".git" (
  echo This folder is not connected to the update server, so it cannot update
  echo itself. Ask for a fresh copy of the program - your manuals, settings and
  echo API key are kept if you unpack it over this folder.
  pause
  exit /b 1
)
if not exist venv (
  echo No environment found - run setup.bat instead.
  pause
  exit /b 1
)

echo [1/4] Downloading the latest version...
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

echo [2/4] Updating libraries...
call venv\Scripts\activate
python -m pip install -r requirements.txt

echo [3/4] Checking GPU support...
where nvidia-smi >nul 2>&1
if errorlevel 1 goto :gpu_done
REM A plain "pip install torch" will NOT fix an old CUDA build, because pip sees
REM torch as already satisfied. Detect the old build and force the upgrade.
python -c "import torch,sys; sys.exit(0 if 'cu128' in torch.__version__ else 1)" 2>nul
if not errorlevel 1 goto :gpu_ok
echo   Installing GPU support for newer NVIDIA cards ^(~3 GB, one-time^)...
pip install --upgrade torch --index-url https://download.pytorch.org/whl/cu128
goto :gpu_done
:gpu_ok
echo   GPU support is already up to date.
:gpu_done

echo [4/4] Updating the local AI model (if Ollama is installed)...
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
echo Tip: run check_system.bat to confirm everything works.
echo.
pause
