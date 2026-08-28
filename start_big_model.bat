@echo off
setlocal
cd /d "%~dp0"
title Big offline model - keep this window open

REM Which model to serve. Change it here if you need a different one.
set FT_MODEL=Qwen3.6-35B-A3B

echo ===============================================================
echo  BIG OFFLINE MODEL
echo ===============================================================
echo.

if not exist venv (
  echo  ERROR: no environment found. Run setup.bat first.
  echo.
  pause
  exit /b 1
)
call venv\Scripts\activate

echo  Step 1: looking for FreeToken...
set FT_CMD=
where ft >nul 2>&1
if not errorlevel 1 goto :found_ft
python -c "import freetoken" >nul 2>&1
if not errorlevel 1 goto :found_module

echo.
echo  FreeToken is NOT installed.
echo  Run install_freetoken.bat first, then start this again.
echo.
pause
exit /b 1

:found_ft
set FT_CMD=ft
echo    found: 'ft' command
goto :ready

:found_module
set FT_CMD=python -m freetoken
echo    found: python module ^(the 'ft' command is not on PATH^)
goto :ready

:ready
echo.
echo  Step 2: starting the model server
echo    command: %FT_CMD% serve %FT_MODEL%
echo.
echo ===============================================================
echo  IMPORTANT - WHAT TO EXPECT
echo.
echo   * The FIRST start downloads the model (about 20 GB). During the
echo     download this window may show NOTHING for a long time - that
echo     is normal, it is working. Do not close it.
echo   * When ready you will see an address like http://localhost:8000
echo   * To check progress, open check_system.bat in a SECOND window -
echo     it says whether the big model is answering yet.
echo   * Keep THIS window open while you use the big model.
echo ===============================================================
echo.

%FT_CMD% serve %FT_MODEL%
set RC=%ERRORLEVEL%

echo.
echo ===============================================================
echo  The big model has stopped (exit code %RC%).
echo.
if not "%RC%"=="0" (
  echo  It stopped because of an error - the message above says why.
  echo  Take a screenshot of this whole window.
  echo.
  echo  If it says the model name is unknown, run freetoken_help.bat
  echo  and send that screenshot too - it lists the correct names.
)
echo ===============================================================
pause
