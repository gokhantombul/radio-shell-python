@echo off
setlocal enabledelayedexpansion

:: Radio Shell - Terminal FM Radio Player (Windows)
:: Kullanim: radio.bat [--install | --uninstall]

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

:: ── Install / Uninstall ──────────────────────────────────────────────────────
if /i "%~1"=="--install"   goto :install
if /i "%~1"=="--uninstall" goto :uninstall

:: ── Runtime checks ───────────────────────────────────────────────────────────
where ffplay >nul 2>&1
if errorlevel 1 (
    echo [UYARI] ffplay bulunamadi. Lutfen ffmpeg yukleyin.
    echo   winget  : winget install Gyan.FFmpeg
    echo   Manuel  : https://ffmpeg.org/download.html
    exit /b 1
)

where python >nul 2>&1
if errorlevel 1 (
    echo [UYARI] Python bulunamadi. Lutfen Python yukleyin: https://python.org
    exit /b 1
)

cd /d "%SCRIPT_DIR%"

if not exist "venv\" (
    echo [BILGI] Python sanal ortami olusturuluyor...
    python -m venv venv
    venv\Scripts\pip install --upgrade pip -q
    venv\Scripts\pip install -e . -q
    if exist "requirements.txt" (
        venv\Scripts\pip install -r requirements.txt -q
    )
)

set "PYTHONPATH=%SCRIPT_DIR%"
venv\Scripts\python -m src.radio.main %*
goto :eof

:: ── Install ──────────────────────────────────────────────────────────────────
:install
set "INSTALL_DIR=%USERPROFILE%\.local\bin"
if not exist "%INSTALL_DIR%\" mkdir "%INSTALL_DIR%"

(
    echo @echo off
    echo cd /d "%SCRIPT_DIR%"
    echo call "%SCRIPT_DIR%\radio.bat" %%*
) > "%INSTALL_DIR%\radio.bat"

echo [OK] 'radio' komutu kuruldu: %INSTALL_DIR%\radio.bat
echo.
echo Komutu her yerden calistirmak icin bu klasoru PATH'e ekleyin:
echo   [Kalici] setx PATH "%%PATH%%;%INSTALL_DIR%"
echo   [Gecici] set  PATH=%%PATH%%;%INSTALL_DIR%
goto :eof

:: ── Uninstall ─────────────────────────────────────────────────────────────────
:uninstall
set "INSTALL_FILE=%USERPROFILE%\.local\bin\radio.bat"
if exist "%INSTALL_FILE%" (
    del "%INSTALL_FILE%"
    echo [OK] Kaldirildi: %INSTALL_FILE%
) else (
    echo [BILGI] Kurulu 'radio' komutu bulunamadi.
)
goto :eof
