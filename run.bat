@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title V2Ray Shop Bot

cls
echo ========================================
echo          V2Ray Shop Bot
echo ========================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Project is not set up yet.
    echo Run setup.bat first.
    echo.
    pause
    exit /b 1
)

if not exist ".env" (
    echo [ERROR] .env is missing.
    echo Run setup.bat first.
    echo.
    pause
    exit /b 1
)

echo Starting bot...
echo Press Ctrl+C to stop it.
echo.
".venv\Scripts\python.exe" run.py
set "BOT_EXIT=%ERRORLEVEL%"

echo.
if not "%BOT_EXIT%"=="0" (
    echo [ERROR] Bot stopped with exit code %BOT_EXIT%.
    echo Read the error above.
) else (
    echo Bot stopped.
)
echo.
pause
exit /b %BOT_EXIT%
