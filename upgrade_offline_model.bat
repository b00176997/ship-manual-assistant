@echo off
cd /d "%~dp0"
title Upgrade the offline model

echo ===============================================================
echo  UPGRADE THE OFFLINE AI MODEL
echo ===============================================================
echo.
echo  This picks the best local model your graphics card can run
echo  and downloads it. Better offline answers, still free and
echo  still works without internet.
echo.

if not exist venv (
  echo Please run setup.bat first.
  pause
  exit /b 1
)
call venv\Scripts\activate
python upgrade_offline_model.py
echo.
pause
