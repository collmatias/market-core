@echo off
title VetCoreSoft — Building Executable
color 0A

echo.
echo ============================================
echo   VetCoreSoft Desktop — Build System
echo ============================================
echo.

REM --- Check Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Download Python 3.11+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM --- Create build venv ---
if not exist "build_env\" (
    echo [1/5] Creating build environment...
    python -m venv build_env
)
call build_env\Scripts\activate.bat

REM --- Install build tools ---
echo [2/5] Installing build dependencies...
pip install --quiet -r requirements_build.txt

REM --- Generate icon ---
echo [3/5] Generating application icon...
python create_icon.py

REM --- Build with PyInstaller ---
echo [4/5] Building executable (this takes a few minutes)...
pyinstaller vetcoresoft.spec --clean --noconfirm

REM --- Assemble distribution ---
echo [5/5] Assembling distribution package...

set DIST=dist\VetCoreSoft

REM Copy Django project (excluding dev/docker files)
xcopy /E /I /Y /Q "..\backend" "%DIST%\backend\" /EXCLUDE:exclude_list.txt

REM Copy configuration
copy /Y "..\windows_pilot\vetcoresoft.ini" "%DIST%\vetcoresoft.ini" >nul

REM Copy icon to dist
if exist "vetcoresoft.ico" copy /Y "vetcoresoft.ico" "%DIST%\vetcoresoft.ico" >nul

REM Remove files not needed in distribution
del /Q "%DIST%\backend\Dockerfile" 2>nul
del /Q "%DIST%\backend\db.sqlite3" 2>nul
for /d /r "%DIST%\backend" %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

REM --- Create ZIP ---
echo.
echo Creating ZIP package...
cd dist
powershell -NoProfile -Command "Compress-Archive -Path 'VetCoreSoft' -DestinationPath 'VetCoreSoft-Setup.zip' -Force"
cd ..

echo.
echo ============================================
echo   BUILD COMPLETE!
echo   Output: desktop\dist\VetCoreSoft-Setup.zip
echo ============================================
echo.
echo The ZIP contains everything needed:
echo   - vetcoresoft.exe (self-contained, includes Python)
echo   - backend\ (Django project)
echo   - vetcoresoft.ini (cloud API configuration)
echo   - vetcoresoft.ico (application icon)
echo.
echo The user just extracts the ZIP and runs vetcoresoft.exe.
echo No Python installation required.
echo.
pause
