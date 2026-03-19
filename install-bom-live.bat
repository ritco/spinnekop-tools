@echo off
PowerShell -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/ritco/spinnekop-tools/main/install-bom-live.ps1' -OutFile '%TEMP%\install-bom-live.ps1' -UseBasicParsing"
PowerShell -ExecutionPolicy Bypass -File "%TEMP%\install-bom-live.ps1"
