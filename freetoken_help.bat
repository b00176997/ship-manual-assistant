@echo off
setlocal
cd /d "%~dp0"
title FreeToken - diagnostic info

echo ===============================================================
echo  FREETOKEN DIAGNOSTIC
echo  Take a screenshot of this window (scroll up if needed).
echo ===============================================================
echo.

if not exist venv (
  echo  No environment found. Run setup.bat first.
  pause
  exit /b 1
)
call venv\Scripts\activate

echo --- Is it installed? -------------------------------------------
where ft 2>nul
if errorlevel 1 echo   'ft' command NOT on PATH
python -c "import freetoken, sys; print('   python module: OK'); print('   version:', getattr(freetoken,'__version__','unknown'))" 2>nul
if errorlevel 1 echo    python module: NOT installed
echo.

echo --- Is a server already running? -------------------------------
curl -s -m 3 http://localhost:8000/v1/models 2>nul
if errorlevel 1 echo    nothing answering on port 8000
echo.
echo.

echo --- ft --help --------------------------------------------------
ft --help 2>&1
echo.

echo --- ft serve --help --------------------------------------------
ft serve --help 2>&1
echo.

echo ===============================================================
echo  Done. Please send a screenshot of this window.
echo ===============================================================
pause
