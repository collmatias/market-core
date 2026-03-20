@echo off
chcp 65001 >nul
title MarketCoreSoft - Servidor

:: ============================================
:: MarketCoreSoft - Desktop Server Launcher
:: Double-click this file to start the app.
:: ============================================

set "ROOT=%~dp0"
set "PYTHON=%ROOT%python\python.exe"
set "APP=%ROOT%app"
set "PORT=443"

:: Check Python exists
if not exist "%PYTHON%" (
    echo ❌ ERROR: Python no encontrado en %PYTHON%
    echo    Reinstale MarketCoreSoft.
    pause
    exit /b 1
)

:: Set environment
set "DJANGO_SETTINGS_MODULE=marketcore.settings"
set "DEPLOYMENT_MODE=DESKTOP"
set "ALLOWED_HOSTS=*"

cd /d "%APP%"

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║       🏪 MarketCoreSoft v0.4.0          ║
echo  ║       Sistema de Gestión Comercial       ║
echo  ╚══════════════════════════════════════════╝
echo.
echo  Iniciando servidor...
echo  NO cierre esta ventana mientras usa el sistema.
echo.

"%PYTHON%" manage.py rundesktop --port %PORT%

if errorlevel 1 (
    echo.
    echo ❌ Error al iniciar el servidor.
    echo    Verifique que el puerto %PORT% no esté en uso.
    echo    Puede probar con otro puerto editando este archivo.
    pause
)
