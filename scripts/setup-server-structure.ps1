<#
.SYNOPSIS
    Eenmalige server setup voor BOM Import Tool release structuur.
    Uitvoeren via RDP op VMSERVERRUM als ridderadmin.

.DESCRIPTION
    1. Maakt C:\import\archive\ aan
    2. Maakt C:\import-test\ aan met output submappen
    3. Migreert exe van oude naar nieuwe locatie
    4. Verwijdert lege oude map
    5. Maakt Public Desktop snelkoppeling aan

    Idempotent: veilig om meerdere keren uit te voeren.
#>

$ErrorActionPreference = "Stop"

Write-Host "=== BOM Import Tool --- Server Setup ===" -ForegroundColor Cyan
Write-Host ""

# --- 1. Archief map aanmaken ---
Write-Host "[1/5] Archive map aanmaken..." -ForegroundColor Yellow
$archivePath = "C:\import\archive"
if (-not (Test-Path $archivePath)) {
    New-Item -ItemType Directory -Path $archivePath | Out-Null
    Write-Host "      Aangemaakt: $archivePath" -ForegroundColor Green
} else {
    Write-Host "      Bestaat al: $archivePath" -ForegroundColor Gray
}

# --- 2. Import-test root aanmaken met output submappen ---
Write-Host "[2/5] Import-test structuur aanmaken..." -ForegroundColor Yellow
$testPaths = @(
    "C:\import-test",
    "C:\import-test\speel",
    "C:\import-test\live"
)
foreach ($path in $testPaths) {
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path | Out-Null
        Write-Host "      Aangemaakt: $path" -ForegroundColor Green
    } else {
        Write-Host "      Bestaat al: $path" -ForegroundColor Gray
    }
}

# --- 3. Exe migreren ---
Write-Host "[3/5] Exe migreren naar nieuwe locatie..." -ForegroundColor Yellow
$oldExe = "C:\import\bom-import-tool\bom-import-tool.exe"
$newExe = "C:\import\bom-import-tool.exe"

if (Test-Path $oldExe) {
    if (Test-Path $newExe) {
        Write-Host "      Nieuwe locatie bestaat al --- migratie overgeslagen" -ForegroundColor Gray
        Write-Host "      (verwijder $newExe handmatig als je opnieuw wilt migreren)" -ForegroundColor Gray
    } else {
        Copy-Item -Path $oldExe -Destination $newExe
        Write-Host "      Gekopieerd: $oldExe -> $newExe" -ForegroundColor Green
    }
} elseif (Test-Path $newExe) {
    Write-Host "      Exe al op nieuwe locatie, niets te migreren" -ForegroundColor Gray
} else {
    Write-Host "      WAARSCHUWING: Geen exe gevonden op oude of nieuwe locatie." -ForegroundColor Red
    Write-Host "      Kopieer handmatig de exe naar: $newExe" -ForegroundColor Red
}

# --- 4. Lege oude map verwijderen ---
Write-Host "[4/5] Oude map opruimen..." -ForegroundColor Yellow
$oldDir = "C:\import\bom-import-tool"
if (Test-Path $oldDir) {
    $contents = Get-ChildItem -Path $oldDir
    if ($contents.Count -eq 0) {
        Remove-Item -Path $oldDir
        Write-Host "      Verwijderd (was leeg): $oldDir" -ForegroundColor Green
    } else {
        Write-Host "      Map bevat nog bestanden --- niet verwijderd:" -ForegroundColor Yellow
        $contents | ForEach-Object { Write-Host "        $_" -ForegroundColor Yellow }
        Write-Host "      Controleer en verwijder handmatig als alles is gemigreerd." -ForegroundColor Yellow
    }
} else {
    Write-Host "      Bestaat niet meer: $oldDir" -ForegroundColor Gray
}

# --- 5. Public Desktop snelkoppeling aanmaken ---
Write-Host "[5/5] Public Desktop snelkoppeling aanmaken..." -ForegroundColor Yellow
$shortcutPath = "C:\Users\Public\Desktop\BOM Import Tool.lnk"
$targetExe = "C:\import\bom-import-tool.exe"

$WShell = New-Object -ComObject WScript.Shell
$shortcut = $WShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetExe
$shortcut.WorkingDirectory = "C:\import"
$shortcut.Description = "BOM Import Tool --- Spinnekop"
$shortcut.IconLocation = "$targetExe,0"
$shortcut.WindowStyle = 1
$shortcut.Save()

if (Test-Path $shortcutPath) {
    Write-Host "      Snelkoppeling aangemaakt: $shortcutPath" -ForegroundColor Green
    Write-Host "      -> Wijst naar: $targetExe" -ForegroundColor Green
} else {
    Write-Host "      FOUT: Snelkoppeling aanmaken mislukt!" -ForegroundColor Red
    exit 1
}

# --- Verificatie ---
Write-Host ""
Write-Host "=== Verificatie ===" -ForegroundColor Cyan
$checks = @(
    @{ Path = "C:\import\bom-import-tool.exe"; Label = "Stable exe" },
    @{ Path = "C:\import\archive"; Label = "Archive map" },
    @{ Path = "C:\import-test"; Label = "Import-test root" },
    @{ Path = "C:\import-test\speel"; Label = "Import-test speel" },
    @{ Path = "C:\import-test\live"; Label = "Import-test live" },
    @{ Path = "C:\Users\Public\Desktop\BOM Import Tool.lnk"; Label = "Snelkoppeling" }
)

$allOk = $true
foreach ($check in $checks) {
    if (Test-Path $check.Path) {
        Write-Host "  [OK] $($check.Label): $($check.Path)" -ForegroundColor Green
    } else {
        Write-Host "  [!!] $($check.Label) ONTBREEKT: $($check.Path)" -ForegroundColor Red
        $allOk = $false
    }
}

Write-Host ""
if ($allOk) {
    Write-Host "Server setup voltooid!" -ForegroundColor Green
} else {
    Write-Host "Setup niet volledig --- controleer de waarschuwingen hierboven." -ForegroundColor Red
    exit 1
}
