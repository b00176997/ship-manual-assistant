@echo off
cd /d "%~dp0"
echo === Ship Mechanic Assistant - Setup ===
echo.

REM This project requires Python 3.12 specifically.
REM (torch / numpy wheels are not available for 3.13 / 3.14 yet, and a mismatched
REM  default "python" is what breaks the install — so we force the 3.12 launcher.)
py -3.12 --version >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python 3.12 was not found.
  echo Install it from https://www.python.org/downloads/release/python-31210/
  echo During install, tick "Add Python to PATH". Then run setup again.
  pause
  exit /b 1
)
echo Using Python 3.12:
py -3.12 --version
echo.

echo [1/5] Creating a clean virtual environment...
if exist venv rmdir /s /q venv
py -3.12 -m venv venv

echo [2/5] Installing libraries (this takes a few minutes)...
call venv\Scripts\activate
python -m pip install --upgrade pip
REM CUDA 12.8 is required for RTX 50-series (Blackwell, sm_120) and also covers
REM older cards (RTX 30/40 series) - do not downgrade this to cu124.
where nvidia-smi >nul 2>&1
if not errorlevel 1 (
  echo   NVIDIA GPU detected - installing GPU-accelerated torch ^(~3 GB, one-time^)...
  pip install torch --index-url https://download.pytorch.org/whl/cu128
) else (
  echo   No NVIDIA GPU detected - using the CPU build ^(indexing will be slower^).
)
pip install -r requirements.txt

echo [3/5] Preparing the settings file...
if not exist .env (
  copy .env.example .env >nul
  echo Created .env - put your ANTHROPIC_API_KEY in it.
)

echo [4/5] Checking optional OCR engine (only needed for SCANNED manuals)...
where tesseract >nul 2>&1
if errorlevel 1 (
  echo   NOTE: Tesseract OCR is NOT installed. Text PDFs work fine without it.
  echo   For scanned manuals install:
  echo     1^) Tesseract:   https://github.com/UB-Mannheim/tesseract/wiki
  echo     2^) Ghostscript: https://www.ghostscript.com/releases/gsdnld.html
) else (
  echo   Tesseract OCR found - scanned manuals are supported.
)

echo [5/5] Checking local AI engine (Ollama) for the "Offline AI" mode...
where ollama >nul 2>&1
if errorlevel 1 (
  echo   NOTE: Ollama is NOT installed. The online modes work without it.
  echo   To enable the free Offline AI mode:
  echo     1^) Install Ollama: https://ollama.com/download
  echo     2^) Run setup again ^(it will download the model^).
) else (
  echo   Ollama found - downloading the local model qwen2.5:7b ^(~5 GB, one-time^)...
  ollama pull qwen2.5:7b
)

echo.
echo Setup complete! Start the program with start.bat
pause
