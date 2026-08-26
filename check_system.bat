@echo off
cd /d "%~dp0"

if not exist venv (
  echo Please run setup.bat first to install.
  pause
  exit /b 1
)

call venv\Scripts\activate
python check_system.py
pause
