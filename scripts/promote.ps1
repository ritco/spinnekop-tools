# Promote BOM Import Tool van dev naar stable op VMSERVERRUM
# Gebruik: powershell -ExecutionPolicy Bypass -File scripts/promote.ps1
# Archiveert huidige stable, kopieert dev build naar stable locatie

$ErrorActionPreference = "Stop"

# --- Configuratie ---
$server          = "10.0.1.5"
$importShare     = "\\$server\import"        # Z: drive -- C:\import op server (stable)
$importTestShare = "\\$server\import-test"   # Y: drive -- C:\import-test op server (dev)
$importDrive     = "Z:"
$importTestDrive = "Y:"
$exeName         = "bom-import-tool.exe"

Write-Host "=== Promote BOM Import Tool -> Stable ===" -ForegroundColor Cyan
Write-Host ""

# --- 1. Versie uitlezen uit main.py ---
Write-Host "[1/6] Versie uitlezen uit main.py..." -ForegroundColor Yellow

$ScriptDir = $PSScriptRoot
$MainPy = Join-Path $ScriptDir "main.py"

if (-not (Test-Path $MainPy)) {
    Write-Host ""
    Write-Host "FOUT: main.py niet gevonden: $MainPy" -ForegroundColor Red
    exit 1
}

$Content = Get-Content $MainPy -Raw
if ($Content -match "__version__\s*=\s*'([^']+)'") {
    $Version = $Matches[1]
} else {
    Write-Host ""
    Write-Host "FOUT: Kon __version__ niet vinden in main.py. Verwacht formaat: __version__ = 'X.Y.Z'" -ForegroundColor Red
    exit 1
}

Write-Host "      Versie: $Version" -ForegroundColor Green

# --- 2. Bevestiging vragen ---
Write-Host ""
Write-Host "[2/6] Bevestiging" -ForegroundColor Yellow
Write-Host ""
Write-Host "Promote versie $Version naar stable?" -ForegroundColor Cyan
Write-Host "  Dev:     Y:\bom-import-tool.exe -> Z:\bom-import-tool.exe" -ForegroundColor Gray
Write-Host "  Archief: Z:\bom-import-tool.exe -> Z:\archive\$Version\" -ForegroundColor Gray
Write-Host ""

$confirm = Read-Host "Doorgaan? (j/n)"
if ($confirm -ine 'j') {
    Write-Host "Afgebroken." -ForegroundColor Yellow
    exit 0
}

Write-Host ""

# --- 3. VPN verbinding controleren ---
Write-Host "[3/6] VPN verbinding controleren..." -ForegroundColor Yellow

$reachable = Test-Connection -ComputerName $server -Count 2 -Quiet
if (-not $reachable) {
    Write-Host ""
    Write-Host "FOUT: Server $server niet bereikbaar. Check VPN verbinding." -ForegroundColor Red
    Write-Host "  - Zorg dat OpenVPN Connect actief is" -ForegroundColor Red
    Write-Host "  - Controleer status: ping $server" -ForegroundColor Red
    exit 1
}
Write-Host "      Server bereikbaar via VPN" -ForegroundColor Green

# --- 4. Drives mappen (idempotent) ---
Write-Host "[4/6] Drives verbinden..." -ForegroundColor Yellow

# Z: drive (import share -- stable, VEREIST)
$zMapped = net use $importDrive 2>&1 | Select-String $importDrive
if (-not $zMapped) {
    try {
        net use $importDrive $importShare /persistent:no 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "net use Z: mislukt (exit code $LASTEXITCODE)" }
        Write-Host "      Z: verbonden met $importShare" -ForegroundColor Green
    } catch {
        Write-Host ""
        Write-Host "FOUT: Z: kon niet verbonden worden: $_" -ForegroundColor Red
        Write-Host "  Z: is vereist voor promote (stable locatie)" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "      Z: al verbonden" -ForegroundColor Gray
}

# Y: drive (import-test share -- dev, VEREIST)
$yMapped = net use $importTestDrive 2>&1 | Select-String $importTestDrive
if (-not $yMapped) {
    try {
        net use $importTestDrive $importTestShare /persistent:no 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "exit $LASTEXITCODE" }
        Write-Host "      Y: verbonden met $importTestShare" -ForegroundColor Green
    } catch {
        Write-Host ""
        Write-Host "FOUT: Y: kon niet verbonden worden: $_" -ForegroundColor Red
        Write-Host "  Y: is vereist voor promote (dev build locatie)" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "      Y: al verbonden" -ForegroundColor Gray
}

# --- 5. Archiveren + promoten ---
Write-Host "[5/6] Archiveren en promoten..." -ForegroundColor Yellow

$devExe    = "$importTestDrive\$exeName"
$stableExe = "$importDrive\$exeName"
$archiveDir = "$importDrive\archive\$Version"
$archiveCreated = $false

# Controleer of dev build aanwezig is
if (-not (Test-Path $devExe)) {
    Write-Host ""
    Write-Host "FOUT: Geen dev build gevonden op Y:\. Draai eerst build.ps1 en deploy.ps1" -ForegroundColor Red
    exit 1
}

# Archiveer huidige stable (als die bestaat)
if (Test-Path $stableExe) {
    New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null
    Copy-Item $stableExe "$archiveDir\$exeName" -Force
    Write-Host "      Huidige stable gearchiveerd naar Z:\archive\$Version\" -ForegroundColor Green
    $archiveCreated = $true
} else {
    Write-Host "      Geen bestaande stable gevonden -- eerste promote" -ForegroundColor Gray
}

# Kopieer dev naar stable
Copy-Item $devExe $stableExe -Force
Write-Host "      Dev build gekopieerd naar Z:\" -ForegroundColor Green

# --- 6. Verificatie ---
Write-Host "[6/6] Verificatie..." -ForegroundColor Yellow

if (-not (Test-Path $stableExe)) {
    Write-Host ""
    Write-Host "FOUT: Verificatie mislukt -- stable exe niet gevonden na kopieren: $stableExe" -ForegroundColor Red
    exit 1
}

$devSize    = (Get-Item $devExe).Length
$stableSize = (Get-Item $stableExe).Length

if ($devSize -ne $stableSize) {
    Write-Host ""
    Write-Host "WAARSCHUWING: Bestandsgrootte komt niet overeen -- controleer handmatig" -ForegroundColor Yellow
    Write-Host "  Dev:    $devSize bytes" -ForegroundColor Yellow
    Write-Host "  Stable: $stableSize bytes" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "Promote geslaagd! v$Version staat live." -ForegroundColor Green
}

Write-Host "  Stable: C:\import\bom-import-tool.exe (v$Version)" -ForegroundColor Green
if ($archiveCreated) {
    Write-Host "  Archief: C:\import\archive\$Version\" -ForegroundColor Green
}
Write-Host "  Evy's snelkoppeling werkt automatisch" -ForegroundColor Green
