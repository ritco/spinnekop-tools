@echo off
set PS1_URL=https://raw.githubusercontent.com/ritco/spinnekop-tools/main/install-bom-test.ps1
set PS1_TMP=%TEMP%\install-bom-test.ps1
PowerShell -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri '%PS1_URL%' -OutFile '%PS1_TMP%' -UseBasicParsing; ^& '%PS1_TMP%'"
