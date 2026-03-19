@echo off
title VetCoreSoft - Starting...
color 0A

echo ============================================
echo   VetCoreSoft Desktop - First Time Setup
echo ============================================
echo.

REM --- Check Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Download Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM --- Create virtual environment (first run only) ---
if not exist "venv\" (
    echo [1/4] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

REM --- Activate venv ---
call venv\Scripts\activate.bat

REM --- Install dependencies (first run only, or if requirements changed) ---
echo [2/4] Checking dependencies...
pip install -r backend\requirements.txt --quiet

REM --- Copy config file if not present ---
if not exist "backend\vetcoresoft.ini" (
    echo [3/4] Creating configuration file...
    copy vetcoresoft.ini backend\vetcoresoft.ini >nul
)

REM --- Run migrations ---
echo [3/4] Updating database...
cd backend
python manage.py migrate --run-syncdb >nul 2>&1

REM --- Start server ---
echo [4/4] Starting VetCoreSoft...
echo.
echo ============================================
echo   VetCoreSoft is running!
echo   Open your browser: http://localhost:8000
echo   Press Ctrl+C to stop.
echo ============================================
echo.
python manage.py runserver 0.0.0.0:8000
