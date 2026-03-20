@echo off
chcp 65001 >nul
title MarketCoreSoft - Detener

:: ============================================
:: Stops MarketCoreSoft server
:: ============================================

echo Deteniendo MarketCoreSoft...

:: Kill any Python process serving our app
taskkill /F /FI "WINDOWTITLE eq MarketCoreSoft - Servidor" >nul 2>&1
taskkill /F /IM python.exe /FI "WINDOWTITLE eq MarketCoreSoft*" >nul 2>&1

echo ✅ Servidor detenido.
timeout /t 2 >nul
