@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: ============================================================
:: MarketCoreSoft - Build Script
:: Creates a distributable package with embedded Python.
:: Run this on a Windows machine with internet access.
::
:: Output: desktop\dist\MarketCoreSoft\  (ready to zip or feed to Inno Setup)
:: ============================================================

set "PYTHON_VERSION=3.11.9"
set "PYTHON_ZIP=python-%PYTHON_VERSION%-embed-amd64.zip"
set "PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/%PYTHON_ZIP%"
set "ROOT=%~dp0"
set "DIST=%ROOT%dist\MarketCoreSoft"
set "PY_DIR=%DIST%\python"
set "APP_DIR=%DIST%\app"

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║  MarketCoreSoft - Build Package          ║
echo  ╚══════════════════════════════════════════╝
echo.

:: Clean previous build
if exist "%DIST%" (
    echo 🗑️  Cleaning previous build...
    rmdir /s /q "%DIST%"
)
mkdir "%DIST%"

:: ── 1. Download embedded Python ──
echo 📥 Downloading Python %PYTHON_VERSION% (embedded)...
if not exist "%ROOT%cache" mkdir "%ROOT%cache"
if not exist "%ROOT%cache\%PYTHON_ZIP%" (
    powershell -Command "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%ROOT%cache\%PYTHON_ZIP%'"
    if errorlevel 1 (
        echo ❌ Failed to download Python. Check your internet connection.
        pause & exit /b 1
    )
)

echo 📦 Extracting Python...
mkdir "%PY_DIR%"
powershell -Command "Expand-Archive -Path '%ROOT%cache\%PYTHON_ZIP%' -DestinationPath '%PY_DIR%' -Force"

:: ── 2. Enable pip in embedded Python ──
echo 🔧 Configuring pip...
:: Uncomment the import site line in python311._pth
set "PTH_FILE=%PY_DIR%\python311._pth"
if exist "%PTH_FILE%" (
    powershell -Command "(Get-Content '%PTH_FILE%') -replace '#import site', 'import site' | Set-Content '%PTH_FILE%'"
)

:: Download get-pip.py
if not exist "%ROOT%cache\get-pip.py" (
    powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%ROOT%cache\get-pip.py'"
)
"%PY_DIR%\python.exe" "%ROOT%cache\get-pip.py" --no-warn-script-location >nul 2>&1

:: ── 3. Install dependencies ──
echo 📦 Installing dependencies...
"%PY_DIR%\python.exe" -m pip install --no-warn-script-location -q -r "%ROOT%..\backend\requirements.txt"

:: Also install cryptography for SSL cert generation (no openssl on most Windows)
"%PY_DIR%\python.exe" -m pip install --no-warn-script-location -q cryptography

:: ── 4. Copy application code ──
echo 📂 Copying application...
xcopy "%ROOT%..\backend" "%APP_DIR%\" /E /I /Q /Y >nul

:: Remove unnecessary files from the copy
if exist "%APP_DIR%\db.sqlite3" del "%APP_DIR%\db.sqlite3"
if exist "%APP_DIR%\certs" rmdir /s /q "%APP_DIR%\certs"
if exist "%APP_DIR%\__pycache__" rmdir /s /q "%APP_DIR%\__pycache__"
for /d /r "%APP_DIR%" %%d in (__pycache__) do (
    if exist "%%d" rmdir /s /q "%%d"
)

:: ── 5. Copy launcher scripts ──
echo 📝 Copying launchers...
copy "%ROOT%start.bat" "%DIST%\MarketCoreSoft.bat" >nul
copy "%ROOT%stop.bat" "%DIST%\Detener.bat" >nul

:: ── 6. Compile translations ──
echo 🌐 Compiling translations...
set "DJANGO_SETTINGS_MODULE=marketcore.settings"
set "DEPLOYMENT_MODE=DESKTOP"
cd /d "%APP_DIR%"
"%PY_DIR%\python.exe" manage.py compilemessages >nul 2>&1

:: ── 7. Summary ──
echo.
echo  ╔══════════════════════════════════════════╗
echo  ║  ✅ Build completed!                     ║
echo  ╚══════════════════════════════════════════╝
echo.
echo  Output: %DIST%
echo.
echo  Next steps:
echo    1. Test: double-click MarketCoreSoft.bat
echo    2. Build installer: compile desktop\installer.iss with Inno Setup
echo.

pause
