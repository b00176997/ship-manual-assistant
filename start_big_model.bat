@echo off
cd /d "%~dp0"
title Big offline model - keep this window open

REM Which model to serve. Change it here if you want a different one.
set FT_MODEL=Qwen3.6-35B-A3B

echo ===============================================================
echo  BIG OFFLINE MODEL
echo ===============================================================
echo.
echo  Keep THIS WINDOW OPEN while you use the "Offline AI - big model"
echo  mode. Closing this window stops the big model (everything else
echo  in the program keeps working).
echo.

if not exist venv (
  echo Please run setup.bat first.
  pause
  exit /b 1
)
call venv\Scripts\activate

REM Prefer the 'ft' command; fall back to the Python module if it is not on PATH.
where ft >nul 2>&1
if not errorlevel 1 (
  set FT_CMD=ft
) else (
  python -c "import freetoken" >nul 2>&1
  if errorlevel 1 (
    echo FreeToken is not installed.
    echo Run install_freetoken.bat first, then start this again.
    echo.
    pause
    exit /b 1
  )
  set FT_CMD=python -m freetoken
)

echo  Starting model: %FT_MODEL%
echo  The FIRST start downloads the model ^(about 20 GB^) - this takes a
echo  while. Later starts are fast.
echo.
echo  When you see a line with an address like http://localhost:8000
echo  the model is ready. Then open the program and choose
echo  "Offline AI - big model".
echo ===============================================================
echo.

%FT_CMD% serve %FT_MODEL%

echo.
echo ===============================================================
echo  The big model has stopped.
echo  If it stopped because of an error, take a screenshot of this
echo  window - the message above explains what went wrong.
echo ===============================================================
pause
