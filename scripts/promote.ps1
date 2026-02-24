# Promote BOM Import Tool en/of Productiestructuur van dev naar stable op VMSERVERRUM
# Gebruik:
#   powershell -ExecutionPolicy Bypass -File scripts/promote.ps1
#   powershell -ExecutionPolicy Bypass -File scripts/promote.ps1 -Tool bom
#   powershell -ExecutionPolicy Bypass -File scripts/promote.ps1 -Tool prod
#   powershell -ExecutionPolicy Bypass -File scripts/promote.ps1 -Force
# -Tool bom:  alleen bom-import-tool promoten
# -Tool prod: alleen productiestructuur promoten
# Zonder -Tool: beide tools promoten
# -Force: bevestigingsprompt overslaan

param(
    [switch]$Force,
    [string]$Tool = ""
)

$ErrorActionPreference = "Stop"

# Valideer -Tool parameter
if ($Tool -ne "" -and $Tool -ne "bom" -and $Tool -ne "prod") {
    Write-Host ""
    Write-Host "FOUT: Ongeldige waarde voor -Tool: '$Tool'" -ForegroundColor Red
    Write-Host "  Geldige waarden: bom, prod, of weglaten voor beide tools" -ForegroundColor Red
    exit 1
}

# --- Configuratie ---
$server          = "10.0.1.5"
$importShare     = "\\$server\import"        # Z: drive -- C:\import op server (stable)
$importTestShare = "\\$server\import-test"   # Y: drive -- C:\import-test op server (dev)
$importDrive     = "Z:"
$importTestDrive = "Y:"
$bomExeName      = "bom-import-tool.exe"
$phantomExeName  = "productiestructuur.exe"

# Bepaal welke tools gepromoot worden
$promoteeBom     = ($Tool -eq "" -or $Tool -eq "bom")
$promoteProd     = ($Tool -eq "" -or $Tool -eq "prod")

Write-Host "=== Promote naar Stable ===" -ForegroundColor Cyan
Write-Host ""

# --- 1. Versies uitlezen ---
Write-Host "[1/7] Versies uitlezen..." -ForegroundColor Yellow

$ScriptDir = $PSScriptRoot

$BomVersion = $null
if ($promoteeBom) {
    $MainPy = Join-Path $ScriptDir "main.py"
    if (-not (Test-Path $MainPy)) {
        Write-Host ""
        Write-Host "FOUT: main.py niet gevonden: $MainPy" -ForegroundColor Red
        exit 1
    }
    $Content = Get-Content $MainPy -Raw
    if ($Content -match "__version__\s*=\s*'([^']+)'") {
        $BomVersion = $Matches[1]
        Write-Host "      BOM Import Tool: $BomVersion" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "FOUT: Kon __version__ niet vinden in main.py. Verwacht formaat: __version__ = 'X.Y.Z'" -ForegroundColor Red
        exit 1
    }
}

$PhantomVersion = $null
if ($promoteProd) {
    $PhantomPy = Join-Path $ScriptDir "phantom_tool.py"
    if (-not (Test-Path $PhantomPy)) {
        Write-Host ""
        Write-Host "FOUT: phantom_tool.py niet gevonden: $PhantomPy" -ForegroundColor Red
        exit 1
    }
    $PhantomContent = Get-Content $PhantomPy -Raw
    if ($PhantomContent -match "__version__\s*=\s*'([^']+)'") {
        $PhantomVersion = $Matches[1]
        Write-Host "      Productiestructuur: $PhantomVersion" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "FOUT: Kon __version__ niet vinden in phantom_tool.py." -ForegroundColor Red
        exit 1
    }
}

# Lees versie van niet-gepromote tool uit bestaande version.json (voor bewaren)
$ExistingBomVersion = "0.0.0"
$ExistingPhantomVersion = "0.0.0"

# --- 2. Bevestiging vragen ---
Write-Host ""
Write-Host "[2/7] Bevestiging" -ForegroundColor Yellow
Write-Host ""

if ($promoteeBom -and $promoteProd) {
    Write-Host "Promote beide tools naar stable?" -ForegroundColor Cyan
    Write-Host "  BOM Import Tool v${BomVersion}:   Y:\${bomExeName} -> Z:\${bomExeName}" -ForegroundColor Gray
    Write-Host "  Productiestructuur v${PhantomVersion}: Y:\${phantomExeName} -> Z:\${phantomExeName}" -ForegroundColor Gray
} elseif ($promoteeBom) {
    Write-Host "Promote bom-import-tool v$BomVersion naar stable?" -ForegroundColor Cyan
    Write-Host "  Dev:     Y:\${bomExeName} -> Z:\${bomExeName}" -ForegroundColor Gray
    Write-Host "  Archief: Z:\${bomExeName} -> Z:\archive\${BomVersion}\" -ForegroundColor Gray
} else {
    Write-Host "Promote productiestructuur v$PhantomVersion naar stable?" -ForegroundColor Cyan
    Write-Host "  Dev:     Y:\${phantomExeName} -> Z:\${phantomExeName}" -ForegroundColor Gray
    Write-Host "  Archief: Z:\${phantomExeName} -> Z:\archive\${PhantomVersion}\" -ForegroundColor Gray
}
Write-Host ""

if ($Force) {
    Write-Host "      -Force: bevestiging overgeslagen" -ForegroundColor Gray
} else {
    $confirm = Read-Host "Doorgaan? (j/n)"
    if ($confirm -ine 'j') {
        Write-Host "Afgebroken." -ForegroundColor Yellow
        exit 0
    }
}

Write-Host ""

# --- 3. VPN verbinding controleren ---
Write-Host "[3/7] VPN verbinding controleren..." -ForegroundColor Yellow

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
Write-Host "[4/7] Drives verbinden..." -ForegroundColor Yellow

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
Write-Host "[5/7] Archiveren en promoten..." -ForegroundColor Yellow

# Lees bestaande version.json voor versies van niet-gepromote tool
$versionJsonPath = "$importDrive\version.json"
if (Test-Path $versionJsonPath) {
    try {
        $existingJson = Get-Content $versionJsonPath -Raw | ConvertFrom-Json
        if ($existingJson.'bom-import-tool') { $ExistingBomVersion = $existingJson.'bom-import-tool' }
        if ($existingJson.'productiestructuur') { $ExistingPhantomVersion = $existingJson.'productiestructuur' }
    } catch {
        Write-Host "      Bestaande version.json kon niet gelezen worden -- gebruik 0.0.0 als fallback" -ForegroundColor Gray
    }
}

# Helper-functie om een tool te promoten
function Invoke-ToolPromote {
    param(
        [string]$ToolExeName,
        [string]$ToolVersion,
        [string]$DevDrive,
        [string]$StableDrive,
        [string]$ArchiveDir
    )

    $devExe    = "$DevDrive\$ToolExeName"
    $stableExe = "$StableDrive\$ToolExeName"

    # Controleer of dev build aanwezig is
    if (-not (Test-Path $devExe)) {
        Write-Host "      WAARSCHUWING: $ToolExeName niet gevonden op Y:\ -- overgeslagen" -ForegroundColor Yellow
        return $false
    }

    # Archiveer version.json als die bestaat (alleen eenmalig, door de aanroeper gedaan)
    # Archiveer huidige stable exe (als die bestaat)
    if (Test-Path $stableExe) {
        New-Item -ItemType Directory -Path $ArchiveDir -Force | Out-Null
        Copy-Item $stableExe "$ArchiveDir\$ToolExeName" -Force
        Write-Host "      $ToolExeName gearchiveerd naar $ArchiveDir\" -ForegroundColor Green
    } else {
        Write-Host "      Geen bestaande stable $ToolExeName -- eerste promote" -ForegroundColor Gray
    }

    # Kopieer dev naar stable
    Copy-Item $devExe $stableExe -Force
    Write-Host "      $ToolExeName gekopieerd naar $StableDrive\" -ForegroundColor Green

    # Bestandsgrootte verificatie
    $devSize    = (Get-Item $devExe).Length
    $stableSize = (Get-Item $stableExe).Length
    if ($devSize -ne $stableSize) {
        Write-Host "      WAARSCHUWING: Bestandsgrootte $ToolExeName komt niet overeen (dev: $devSize, stable: $stableSize)" -ForegroundColor Yellow
    }

    return $true
}

# Archiveer bestaande version.json mee (voor de promote start)
$archiveBase = "$importDrive\archive"
$versionJsonArchived = $false

$successBom    = $false
$successProd   = $false

# Promote bom-import-tool
if ($promoteeBom) {
    $archiveDir = "$archiveBase\$BomVersion"
    # Archiveer version.json naar archive samen met de exe
    if (Test-Path $versionJsonPath) {
        New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null
        Copy-Item $versionJsonPath "$archiveDir\version.json" -Force
        $versionJsonArchived = $true
    }
    $successBom = Invoke-ToolPromote -ToolExeName $bomExeName -ToolVersion $BomVersion `
        -DevDrive $importTestDrive -StableDrive $importDrive -ArchiveDir $archiveDir
}

# Promote productiestructuur
if ($promoteProd) {
    $archiveDir = "$archiveBase\$PhantomVersion"
    # Archiveer version.json als nog niet gedaan
    if (-not $versionJsonArchived -and (Test-Path $versionJsonPath)) {
        New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null
        Copy-Item $versionJsonPath "$archiveDir\version.json" -Force
        $versionJsonArchived = $true
    }
    $successProd = Invoke-ToolPromote -ToolExeName $phantomExeName -ToolVersion $PhantomVersion `
        -DevDrive $importTestDrive -StableDrive $importDrive -ArchiveDir $archiveDir
}

# --- 6. version.json atomair bijwerken ---
Write-Host "[6/7] version.json bijwerken..." -ForegroundColor Yellow

# Alleen bijwerken als minstens een tool succesvol gepromoot is
if (-not $successBom -and -not $promoteProd) {
    Write-Host "      Geen tools gepromoot -- version.json niet aangepast" -ForegroundColor Yellow
} elseif (-not $successBom -and $promoteeBom -and -not $promoteProd) {
    Write-Host "      BOM promote mislukt -- version.json niet aangepast" -ForegroundColor Yellow
} else {
    # Stel versies samen: gebruik gepromote versie, of bestaande voor niet-gepromote
    $finalBomVersion     = if ($successBom)  { $BomVersion }     else { $ExistingBomVersion }
    $finalPhantomVersion = if ($successProd) { $PhantomVersion } else { $ExistingPhantomVersion }

    $versionData = [ordered]@{
        "bom-import-tool"  = $finalBomVersion
        "productiestructuur" = $finalPhantomVersion
    }
    $versionJson = $versionData | ConvertTo-Json
    $versionJson | Set-Content -Path $versionJsonPath -Encoding UTF8
    Write-Host "      version.json bijgewerkt op Z:\" -ForegroundColor Green
    Write-Host "      bom-import-tool: $finalBomVersion" -ForegroundColor Gray
    Write-Host "      productiestructuur: $finalPhantomVersion" -ForegroundColor Gray
}

# --- 7. Samenvatting ---
Write-Host ""
Write-Host "[7/7] Samenvatting" -ForegroundColor Yellow
Write-Host ""

if ($successBom) {
    Write-Host "  bom-import-tool v$BomVersion  -> Z:\$bomExeName" -ForegroundColor Green
}
if ($successProd) {
    Write-Host "  productiestructuur v$PhantomVersion -> Z:\$phantomExeName" -ForegroundColor Green
}
if (-not $successBom -and $promoteeBom) {
    Write-Host "  bom-import-tool: OVERGESLAGEN (niet gevonden op Y:)" -ForegroundColor Yellow
}
if (-not $successProd -and $promoteProd) {
    Write-Host "  productiestructuur: OVERGESLAGEN (niet gevonden op Y:)" -ForegroundColor Yellow
}

if (Test-Path $versionJsonPath) {
    Write-Host ""
    Write-Host "  version.json op Z:\" -ForegroundColor Cyan
    Get-Content $versionJsonPath | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
}

if ($versionJsonArchived) {
    Write-Host ""
    Write-Host "  Archief: Z:\archive\ (exe + version.json)" -ForegroundColor Green
}

Write-Host ""
if ($successBom -or $successProd) {
    Write-Host "Promote geslaagd!" -ForegroundColor Green
} else {
    Write-Host "Geen tools gepromoot." -ForegroundColor Yellow
    exit 1
}
