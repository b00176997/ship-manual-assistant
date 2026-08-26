@echo off
cd /d "%~dp0"

if not exist venv (
  echo Please run setup.bat first to install.
  pause
  exit /b 1
)

call venv\Scripts\activate

REM Health check: make sure the environment is intact before launching.
python -c "import numpy, flask" >nul 2>&1
if errorlevel 1 (
  echo.
  echo The Python environment looks broken or incomplete.
  echo Please run setup.bat again to rebuild it.
  pause
  exit /b 1
)

echo Starting... the browser will open in a few seconds.
start "" /min cmd /c "timeout /t 3 >nul & start http://127.0.0.1:5000"
python app.py
pause
