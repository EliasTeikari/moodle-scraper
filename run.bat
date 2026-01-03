@echo off
cd /d "%~dp0"

if not exist "venv" (
    echo Setting up...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install beautifulsoup4 --quiet
) else (
    call venv\Scripts\activate.bat
)

python extract_answers.py

