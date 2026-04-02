@echo off
setlocal
set "URL=https://raw.githubusercontent.com/ritco/spinnekop-tools/main/installers/install-artikelnamen-test.ps1"
set "TMPFILE=%TEMP%\install-artikelnamen-test.ps1"

echo Artikelnamen Tool - Installatie (TEST)
echo =============================================
echo.
echo Stap 1/2: Installer downloaden van GitHub...
PowerShell -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri '%URL%' -OutFile '%TMPFILE%' -UseBasicParsing"

if not exist "%TMPFILE%" (
    echo FOUT: Download mislukt. Controleer internetverbinding.
    pause
    exit /b 1
)

echo Stap 2/2: Installer starten...
echo.
PowerShell -ExecutionPolicy Bypass -File "%TMPFILE%"

if exist "%TMPFILE%" del /f /q "%TMPFILE%"
pause
