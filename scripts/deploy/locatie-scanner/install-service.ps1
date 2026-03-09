# install-service.ps1 - Installeer Locatie Scanner als Windows Service via NSSM
# Draai als Administrator op VMSERVERRUM via RDP
#
# Verwacht dat locatie_scanner.py en requirements.txt naast dit script staan.

#Requires -RunAsAdministrator

# --- Configuratie ---
$ServiceName = "LocatieScanner"
$InstallDir  = "C:\LocatieScanner"
$PythonExe   = "C:\Users\ridderadmin\AppData\Local\Programs\Python\Python312\python.exe"
$NssmExe     = "$InstallDir\nssm.exe"
$Port        = 5050

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# --- 1. Check Python ---
if (-not (Test-Path $PythonExe)) {
    Write-Host "FOUT: Python niet gevonden op $PythonExe" -ForegroundColor Red
    Write-Host "Pas `$PythonExe bovenaan dit script aan naar het juiste pad." -ForegroundColor Yellow
    exit 1
}
Write-Host "[OK] Python gevonden: $PythonExe" -ForegroundColor Green

# --- 2. Check/download NSSM ---
if (-not (Test-Path $NssmExe)) {
    Write-Host "NSSM niet gevonden in $InstallDir, probeer te downloaden..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force $InstallDir | Out-Null

    $nssmZip = "$env:TEMP\nssm-2.24.zip"
    $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"

    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip -UseBasicParsing -ErrorAction Stop
        Write-Host "NSSM gedownload, uitpakken..." -ForegroundColor Cyan

        $extractDir = "$env:TEMP\nssm-extract"
        if (Test-Path $extractDir) { Remove-Item -Recurse -Force $extractDir }
        Expand-Archive -Path $nssmZip -DestinationPath $extractDir -Force
        Copy-Item "$extractDir\nssm-2.24\win64\nssm.exe" $NssmExe -Force
        Remove-Item -Recurse -Force $extractDir
        Remove-Item -Force $nssmZip
        Write-Host "[OK] NSSM geinstalleerd: $NssmExe" -ForegroundColor Green
    } catch {
        Write-Host "FOUT: Kan NSSM niet downloaden (geen internet?)." -ForegroundColor Red
        Write-Host "Download handmatig: $nssmUrl" -ForegroundColor Yellow
        Write-Host "Kopieer nssm.exe (win64) naar: $NssmExe" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "[OK] NSSM aanwezig: $NssmExe" -ForegroundColor Green
}

# --- 3. Stop bestaande service ---
Write-Host "Stoppen bestaande service (als die draait)..." -ForegroundColor Cyan
& $NssmExe stop $ServiceName 2>$null
& $NssmExe remove $ServiceName confirm 2>$null
Start-Sleep -Seconds 2

# --- 4. Kopieer bestanden ---
Write-Host "Bestanden kopieren naar $InstallDir..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force $InstallDir | Out-Null

$sourceApp = Join-Path $ScriptDir "locatie_scanner.py"
$sourceReq = Join-Path $ScriptDir "requirements.txt"

if (-not (Test-Path $sourceApp)) {
    Write-Host "FOUT: locatie_scanner.py niet gevonden naast dit script ($ScriptDir)" -ForegroundColor Red
    Write-Host "Kopieer locatie_scanner.py naar dezelfde map als install-service.ps1" -ForegroundColor Yellow
    exit 1
}
if (-not (Test-Path $sourceReq)) {
    Write-Host "FOUT: requirements.txt niet gevonden naast dit script ($ScriptDir)" -ForegroundColor Red
    exit 1
}

Copy-Item $sourceApp "$InstallDir\locatie_scanner.py" -Force
Copy-Item $sourceReq "$InstallDir\requirements.txt" -Force
Write-Host "[OK] Bestanden gekopieerd" -ForegroundColor Green

# --- 5. Virtuele omgeving en dependencies ---
Write-Host "Virtuele omgeving aanmaken en dependencies installeren..." -ForegroundColor Cyan
& $PythonExe -m venv "$InstallDir\venv"
& "$InstallDir\venv\Scripts\pip.exe" install --upgrade pip -q
& "$InstallDir\venv\Scripts\pip.exe" install -r "$InstallDir\requirements.txt" -q

if ($LASTEXITCODE -ne 0) {
    Write-Host "FOUT: pip install mislukt" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Dependencies geinstalleerd" -ForegroundColor Green

# --- 6. Installeer NSSM service ---
Write-Host "Service installeren via NSSM..." -ForegroundColor Cyan
& $NssmExe install $ServiceName "$InstallDir\venv\Scripts\python.exe" "$InstallDir\locatie_scanner.py"
& $NssmExe set $ServiceName AppDirectory "$InstallDir"
& $NssmExe set $ServiceName DisplayName "Locatie Scanner - Spinnekop"
& $NssmExe set $ServiceName Description "Flask webapp voor barcode locatie scanning (poort $Port)"
& $NssmExe set $ServiceName Start SERVICE_AUTO_START
& $NssmExe set $ServiceName AppStdout "$InstallDir\logs\service.log"
& $NssmExe set $ServiceName AppStderr "$InstallDir\logs\service.log"
& $NssmExe set $ServiceName AppStdoutCreationDisposition 4
& $NssmExe set $ServiceName AppStderrCreationDisposition 4
& $NssmExe set $ServiceName AppRotateFiles 1
& $NssmExe set $ServiceName AppRotateBytes 1048576
& $NssmExe set $ServiceName AppRestartDelay 5000
Write-Host "[OK] Service geconfigureerd" -ForegroundColor Green

# --- 7. Logs directory ---
New-Item -ItemType Directory -Force "$InstallDir\logs" | Out-Null
Write-Host "[OK] Logs directory aangemaakt" -ForegroundColor Green

# --- 8. Start service ---
Write-Host "Service starten..." -ForegroundColor Cyan
& $NssmExe start $ServiceName

# --- 9. Verificatie ---
Write-Host "Wachten op startup (3 sec)..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

try {
    $response = Invoke-WebRequest -Uri "http://localhost:$Port/api/ping" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "[OK] Locatie Scanner draait op poort $Port!" -ForegroundColor Green
    } else {
        Write-Host "WAARSCHUWING: Onverwachte status $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "WAARSCHUWING: Locatie Scanner reageert nog niet" -ForegroundColor Yellow
    Write-Host "Service status:" -ForegroundColor Yellow
    & $NssmExe status $ServiceName
    Write-Host "Check logs: $InstallDir\logs\service.log" -ForegroundColor Yellow
}

# --- 10. Firewall rule (idempotent) ---
# Firewall rule bestaat waarschijnlijk al, dit is een safety check.
$rule = Get-NetFirewallRule -DisplayName "Locatie Scanner" -ErrorAction SilentlyContinue
if (-not $rule) {
    New-NetFirewallRule -DisplayName "Locatie Scanner" -Direction Inbound -Protocol TCP -LocalPort $Port -Action Allow | Out-Null
    Write-Host "[OK] Firewall regel aangemaakt voor poort $Port" -ForegroundColor Green
} else {
    Write-Host "[OK] Firewall regel bestond al" -ForegroundColor Green
}

# --- Klaar ---
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Locatie Scanner is geinstalleerd!" -ForegroundColor Green
Write-Host "  URL: http://localhost:$Port" -ForegroundColor Cyan
Write-Host "  Extern: http://10.0.1.5:$Port" -ForegroundColor Cyan
Write-Host "  Logs: $InstallDir\logs\service.log" -ForegroundColor Cyan
Write-Host "  Status: nssm status $ServiceName" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
