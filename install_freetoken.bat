@echo off
cd /d "%~dp0"
echo ===============================================================
echo  OPTIONAL: big offline AI model (FreeToken)
echo ===============================================================
echo.
echo  This installs FreeToken, which runs a LARGE AI model on your own
echo  computer - free, offline, and much smarter than the small model.
echo.
echo  It needs an NVIDIA graphics card and downloads about 20 GB.
echo  Everything already works without it - this is an extra.
echo.
echo  Press Ctrl+C to cancel, or
pause

where nvidia-smi >nul 2>&1
if errorlevel 1 (
  echo.
  echo   No NVIDIA graphics card detected - FreeToken needs one. Stopping.
  pause
  exit /b 1
)

if not exist venv (
  echo Please run setup.bat first.
  pause
  exit /b 1
)
call venv\Scripts\activate

echo.
echo [1/3] Installing the uv package tool...
python -m pip install --upgrade uv
if errorlevel 1 goto :failed

echo.
echo [2/3] Installing FreeToken...
python -m uv pip install "freetoken[accel]"
if errorlevel 1 goto :failed

echo.
echo [3/3] Checking the installation...
ft --help >nul 2>&1
if errorlevel 1 (
  echo   FreeToken installed, but the 'ft' command was not found on PATH.
  echo   You can still start it with:  python -m freetoken serve ^<model^>
) else (
  echo   FreeToken is installed.
)

echo.
echo ===============================================================
echo  NEXT STEP:
echo.
echo    1. Double-click  start_big_model.bat
echo       ^(the first start downloads the model, about 20 GB^)
echo    2. Leave that window open
echo    3. In the program pick "Offline AI - big model"
echo.
echo  Run check_system.bat to confirm it is detected.
echo ===============================================================
pause
exit /b 0

:failed
echo.
echo   Installation failed. The program still works without FreeToken -
echo   just use one of the other modes.
pause
exit /b 1
