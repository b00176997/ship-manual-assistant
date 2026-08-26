@echo off
cd /d "%~dp0"

if not exist venv (
  echo Please run setup.bat first to install.
  pause
  exit /b 1
)

call venv\Scripts\activate
echo Indexing all PDFs in the "manuals" folder...
echo (already-indexed files are skipped)
echo.
python ingest_folder.py
echo.
pause
