@echo off
PowerShell -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/ritco/spinnekop-tools/main/install-eplan-live.ps1' -OutFile '%TEMP%\install-eplan-live.ps1' -UseBasicParsing"
PowerShell -ExecutionPolicy Bypass -File "%TEMP%\install-eplan-live.ps1"
