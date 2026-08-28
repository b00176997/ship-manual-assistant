@echo off
setlocal
cd /d "%~dp0"
title FreeToken - how to install on Windows

echo ===============================================================
echo  OPTIONAL: big offline AI model (FreeToken)
echo ===============================================================
echo.
echo  IMPORTANT - please read, this saves you a wasted download.
echo.
echo  FreeToken's command-line version officially supports LINUX only.
echo  Its own install docs list "Linux x86_64" as the requirement, and
echo  on Windows the install always fails: it depends on a component
echo  ("triton") that has no Windows build at all.
echo.
echo  So this script does NOT try to pip-install it - that would only
echo  waste your time and end in an error.
echo ===============================================================
echo.
echo  THE WINDOWS WAY: use the official desktop app
echo.
echo    1. Open  https://flashml.ai  and download the Windows app
echo    2. Install it and start a model inside that app
echo       (the first start downloads about 20 GB)
echo    3. Leave the app running
echo    4. Come back here and run  check_system.bat
echo.
echo  Our program looks for the model server automatically on the
echo  usual addresses, so if the app serves an OpenAI/Anthropic-style
echo  API you do not need to configure anything.
echo.
echo  If check_system.bat still says "not installed", the app is using
echo  a different address. Find it in the app (something like
echo  http://localhost:8000) and add this line to the .env file:
echo.
echo      FREETOKEN_URL=http://localhost:PORT
echo.
echo ===============================================================
echo  WORKS TODAY, NO EXTRA SOFTWARE:
echo.
echo  Your graphics card has enough memory for a bigger Ollama model,
echo  which is a solid quality upgrade with no new dependencies:
echo.
echo      upgrade_offline_model.bat
echo.
echo ===============================================================
echo.

where nvidia-smi >nul 2>&1
if errorlevel 1 (
  echo  NOTE: no NVIDIA graphics card detected - a big local model
  echo  would be very slow on this machine.
  echo.
)

pause
