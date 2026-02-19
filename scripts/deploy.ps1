# Deploy BOM Import Tool naar test-omgeving op VMSERVERRUM
# Gebruik: powershell -ExecutionPolicy Bypass -File scripts/deploy.ps1
# Vereist: VPN verbinding + import-test share op server

$ErrorActionPreference = "Stop"

# --- Configuratie ---
$server         = "10.0.1.5"
$importShare    = "\\$server\import"        # Z: drive -- C:\import op server
$importTestShare = "\\$server\import-test"  # Y: drive -- C:\import-test op server
$importDrive    = "Z:"
$importTestDrive = "Y:"
$exeName        = "bom-import-tool.exe"

Write-Host "=== Deploy BOM Import Tool -> VMSERVERRUM ===" -ForegroundColor Cyan
Write-Host ""

# --- 1. Zoek de te deployen exe ---
Write-Host "[1/4] Exe zoeken..." -ForegroundColor Yellow

$scriptDir = $PSScriptRoot
$exePath   = Join-Path $scriptDir "dist\$exeName"

if (-not (Test-Path $exePath)) {
    Write-Host ""
    Write-Host "FOUT: Geen exe gevonden in dist/. Draai eerst build.ps1" -ForegroundColor Red
    Write-Host "  Verwacht: $exePath" -ForegroundColor Red
    exit 1
}

$exeInfo = Get-Item $exePath
$exeSizeMB = [math]::Round($exeInfo.Length / 1MB, 1)
Write-Host "      Exe gevonden: $exePath ($exeSizeMB MB)" -ForegroundColor Green

# --- 2. Verbindingscheck (VPN) ---
Write-Host "[2/4] VPN verbinding controleren..." -ForegroundColor Yellow

$reachable = Test-Connection -ComputerName $server -Count 2 -Quiet
if (-not $reachable) {
    Write-Host ""
    Write-Host "FOUT: Server $server niet bereikbaar. Check VPN verbinding." -ForegroundColor Red
    Write-Host "  - Zorg dat OpenVPN Connect actief is" -ForegroundColor Red
    Write-Host "  - Controleer status: ping $server" -ForegroundColor Red
    exit 1
}
Write-Host "      Server bereikbaar via VPN" -ForegroundColor Green

# --- 3. Drives mappen (idempotent) ---
Write-Host "[3/4] Drives verbinden..." -ForegroundColor Yellow

# Z: drive (import share -- bestaand)
$zMapped = net use $importDrive 2>&1 | Select-String $importDrive
if (-not $zMapped) {
    try {
        net use $importDrive $importShare /persistent:no 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "net use Z: mislukt (exit code $LASTEXITCODE)" }
        Write-Host "      Z: verbonden met $importShare" -ForegroundColor Green
    } catch {
        Write-Host "WAARSCHUWING: Z: kon niet verbonden worden: $_" -ForegroundColor Yellow
        Write-Host "  (deploy gaat door -- Z: is niet vereist voor import-test)" -ForegroundColor Yellow
    }
} else {
    Write-Host "      Z: al verbonden" -ForegroundColor Gray
}

# Y: drive (import-test share -- nieuw)
$yMapped = net use $importTestDrive 2>&1 | Select-String $importTestDrive
if (-not $yMapped) {
    try {
        net use $importTestDrive $importTestShare /persistent:no 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "exit $LASTEXITCODE" }
        Write-Host "      Y: verbonden met $importTestShare" -ForegroundColor Green
    } catch {
        Write-Host ""
        Write-Host "FOUT: Share $importTestShare bestaat nog niet." -ForegroundColor Red
        Write-Host ""
        Write-Host "  Maak deze aan op de server via RDP:" -ForegroundColor Yellow
        Write-Host "    1. Open Computer Management (compmgmt.msc)" -ForegroundColor Yellow
        Write-Host "       > Shared Folders > Shares" -ForegroundColor Yellow
        Write-Host "    2. Right-click > New Share..." -ForegroundColor Yellow
        Write-Host "    3. Folder path: C:\import-test" -ForegroundColor Yellow
        Write-Host "    4. Share name:  import-test" -ForegroundColor Yellow
        Write-Host "    5. Permissions: Everyone = Full Control (intern netwerk)" -ForegroundColor Yellow
        Write-Host "    6. Klik Finish" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Daarna opnieuw proberen: powershell -ExecutionPolicy Bypass -File scripts/deploy.ps1" -ForegroundColor Cyan
        exit 1
    }
} else {
    Write-Host "      Y: al verbonden" -ForegroundColor Gray
}

# --- 4. Kopieer exe naar import-test ---
Write-Host "[4/4] Exe deployen naar $importTestShare..." -ForegroundColor Yellow

$destination = "$importTestDrive\$exeName"

Copy-Item -Path $exePath -Destination $destination -Force

# Verificatie
if (Test-Path $destination) {
    $deployedInfo = Get-Item $destination
    $deployedSizeMB = [math]::Round($deployedInfo.Length / 1MB, 1)
    Write-Host "      Deployed: $exeName -> C:\import-test\ op VMSERVERRUM ($deployedSizeMB MB)" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "FOUT: Verificatie mislukt -- bestand niet gevonden na kopieren: $destination" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Deploy geslaagd!" -ForegroundColor Green
Write-Host "  Exe staat klaar in C:\import-test\ op VMSERVERRUM" -ForegroundColor Green
