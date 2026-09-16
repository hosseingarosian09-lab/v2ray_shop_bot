@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title V2Ray Shop Bot - Setup

cls
echo ========================================
echo        V2Ray Shop Bot - Setup
echo ========================================
echo.

echo Checking Python...
call :find_python
if defined PYTHON_EXE goto :python_ready

echo Python 3.10-3.14 was not found.
echo Python 3.14.7 will now be downloaded from python.org.
echo It will be installed only for the current Windows user.
echo.
call :install_python
if errorlevel 1 goto :failed

call :find_python
if not defined PYTHON_EXE (
    echo [ERROR] Python was installed but could not be found.
    echo Restart Windows, then run setup.bat again.
    goto :failed
)

:python_ready
echo [OK] Python found:
"%PYTHON_EXE%" %PYTHON_ARGS% --version

echo.
if not exist ".venv\Scripts\python.exe" (
    echo [1/4] Creating project environment...
    "%PYTHON_EXE%" %PYTHON_ARGS% -m venv .venv
    if errorlevel 1 goto :failed
) else (
    echo [1/4] Project environment already exists.
)

set "VENV_PY=%CD%\.venv\Scripts\python.exe"

echo [2/4] Installing required packages...
"%VENV_PY%" -m pip install --disable-pip-version-check --upgrade pip
if errorlevel 1 goto :failed
"%VENV_PY%" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto :failed

:ask_token
echo.
echo [3/4] Telegram Bot Token
set "BOT_TOKEN="
set /p "BOT_TOKEN=Paste the token from BotFather and press Enter: "
if not defined BOT_TOKEN (
    echo [ERROR] Token cannot be empty.
    goto :ask_token
)

set "BOT_TOKEN_TO_TEST=%BOT_TOKEN%"
"%VENV_PY%" scripts\validate_token.py
set "TOKEN_RESULT=%ERRORLEVEL%"
set "BOT_TOKEN_TO_TEST="

if "%TOKEN_RESULT%"=="2" (
    echo [ERROR] Telegram rejected this token. Please try again.
    goto :ask_token
)
if "%TOKEN_RESULT%"=="3" (
    echo [WARNING] The token could not be checked because Telegram or the internet was unreachable.
    echo Setup will continue. run.bat will show an error if the token is wrong.
)

for /f %%G in ('powershell -NoProfile -Command "Get-Random -Minimum 100000 -Maximum 999999"') do set "ADMIN_CODE=%%G"
if not defined ADMIN_CODE set "ADMIN_CODE=123456"

> .env echo BOT_TOKEN=%BOT_TOKEN%
>> .env echo ADMIN_SETUP_CODE=%ADMIN_CODE%
>> .env echo DATABASE_PATH=data/bot.db

if not exist "data" mkdir "data"

echo.
echo [4/4] Checking project files...
"%VENV_PY%" -m compileall -q app run.py scripts
if errorlevel 1 goto :failed

echo.
echo ========================================
echo             SETUP COMPLETE
echo ========================================
echo.
echo Next steps:
echo   1. Double-click run.bat
echo   2. Open the bot in Telegram and send /start
echo   3. To claim admin access, send:
echo.
echo      /claimadmin %ADMIN_CODE%
echo.
echo Keep this code private until admin access is claimed.
echo.
pause
exit /b 0

:find_python
set "PYTHON_EXE="
set "PYTHON_ARGS="

rem Try normal Python executables first.
for %%P in (python.exe python3.exe) do (
    for /f "delims=" %%I in ('where %%P 2^>nul') do (
        if not defined PYTHON_EXE (
            "%%I" -c "import sys; raise SystemExit(0 if sys.version_info.major == 3 and sys.version_info.minor in range(10,15) else 1)" >nul 2>&1
            if not errorlevel 1 set "PYTHON_EXE=%%I"
        )
    )
)
if defined PYTHON_EXE exit /b 0

rem Try the Windows Python launcher, but only if it can actually launch Python 3.
for /f "delims=" %%I in ('where py.exe 2^>nul') do (
    if not defined PYTHON_EXE (
        "%%I" -3 -c "import sys; raise SystemExit(0 if sys.version_info.major == 3 and sys.version_info.minor in range(10,15) else 1)" >nul 2>&1
        if not errorlevel 1 (
            set "PYTHON_EXE=%%I"
            set "PYTHON_ARGS=-3"
        )
    )
)
if defined PYTHON_EXE exit /b 0

rem Final check for standard per-user Python installations.
for /f "delims=" %%I in ('dir /b /s "%LOCALAPPDATA%\Programs\Python\Python31*\python.exe" 2^>nul') do (
    if not defined PYTHON_EXE (
        "%%I" -c "import sys; raise SystemExit(0 if sys.version_info.major == 3 and sys.version_info.minor in range(10,15) else 1)" >nul 2>&1
        if not errorlevel 1 set "PYTHON_EXE=%%I"
    )
)
exit /b 0

:install_python
set "PYTHON_VERSION=3.14.7"
set "INSTALLER=%TEMP%\python-%PYTHON_VERSION%-installer.exe"
set "PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-amd64.exe"
set "PYTHON_SHA256=9d9eb2709ef81bf5cd30db3c2096bdbc4ea10087c22e62f27d356b36f6ae9649"

if /I "%PROCESSOR_ARCHITECTURE%"=="ARM64" (
    set "PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-arm64.exe"
    set "PYTHON_SHA256=9a3fe120cc81bc2cb099550f794d8356811f96a86c7f438519243c3485db928d"
)
if /I "%PROCESSOR_ARCHITECTURE%"=="x86" (
    set "PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%.exe"
    set "PYTHON_SHA256=097fc03d4ac2de66ee1d73a0c5d2d323b5c0f14923f7207686ce93149a80f0a6"
)

echo Downloading Python %PYTHON_VERSION%...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%INSTALLER%'"
if errorlevel 1 (
    echo [ERROR] Python download failed. Check the internet connection.
    exit /b 1
)

for /f "tokens=*" %%H in ('powershell -NoProfile -Command "(Get-FileHash -Algorithm SHA256 '%INSTALLER%').Hash.ToLower()"') do set "DOWNLOADED_HASH=%%H"
if /I not "%DOWNLOADED_HASH%"=="%PYTHON_SHA256%" (
    echo [ERROR] The downloaded Python installer failed its checksum check.
    del /q "%INSTALLER%" >nul 2>&1
    exit /b 1
)

echo Installing Python...
"%INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_launcher=1 InstallLauncherAllUsers=0 Include_test=0
if errorlevel 1 (
    echo [ERROR] Python installation failed.
    del /q "%INSTALLER%" >nul 2>&1
    exit /b 1
)

del /q "%INSTALLER%" >nul 2>&1
set "PATH=%LOCALAPPDATA%\Programs\Python\Python314;%LOCALAPPDATA%\Programs\Python\Python314\Scripts;%PATH%"
exit /b 0

:failed
echo.
echo ========================================
echo              SETUP FAILED
echo ========================================
echo Read the error above, fix it, and run setup.bat again.
echo.
pause
exit /b 1
