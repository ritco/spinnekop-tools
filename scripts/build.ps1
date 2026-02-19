# Build BOM Import Tool
# Gebruik: powershell -ExecutionPolicy Bypass -File scripts/build.ps1
# Output: scripts/dist/bom-import-tool-{version}.exe

$ErrorActionPreference = "Stop"

# Bepaal de scripts-directory (relatief aan dit script)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$MainPy = Join-Path $ScriptDir "main.py"
$SpecFile = Join-Path $ScriptDir "bom-import-tool.spec"

# --- Stap 1: Versie uitlezen uit main.py ---
if (-not (Test-Path $MainPy)) {
    Write-Error "main.py niet gevonden: $MainPy"
    exit 1
}

$Content = Get-Content $MainPy -Raw
if ($Content -match "__version__\s*=\s*'([^']+)'") {
    $Version = $Matches[1]
} else {
    Write-Error "Kon __version__ niet vinden in main.py. Verwacht formaat: __version__ = 'X.Y.Z'"
    exit 1
}

# --- Stap 2: Pre-flight checks ---
if (-not (Test-Path $SpecFile)) {
    Write-Error "Spec-bestand niet gevonden: $SpecFile"
    exit 1
}

try {
    $null = Get-Command pyinstaller -ErrorAction Stop
} catch {
    Write-Error "pyinstaller is niet beschikbaar. Installeer met: pip install pyinstaller"
    exit 1
}

Write-Host "Building bom-import-tool v$Version..." -ForegroundColor Cyan

# --- Stap 3: PyInstaller uitvoeren ---
# Verander naar scripts-directory (spec gebruikt relatieve paden)
Push-Location $ScriptDir
try {
    pyinstaller --clean --noconfirm bom-import-tool.spec
    if ($LASTEXITCODE -ne 0) {
        Write-Error "PyInstaller is mislukt met exit code $LASTEXITCODE"
        exit 1
    }
} finally {
    Pop-Location
}

# --- Stap 4: Output versiebeheer ---
$DistDir = Join-Path $ScriptDir "dist"
$BaseExe = Join-Path $DistDir "bom-import-tool.exe"
$VersionedExe = Join-Path $DistDir "bom-import-tool-$Version.exe"

if (-not (Test-Path $BaseExe)) {
    Write-Error "Verwachte output niet gevonden: $BaseExe"
    exit 1
}

# Kopieer naar versioned bestandsnaam
Copy-Item -Path $BaseExe -Destination $VersionedExe -Force

Write-Host "Build complete: dist/bom-import-tool-$Version.exe" -ForegroundColor Green
Write-Host "Alias:          dist/bom-import-tool.exe" -ForegroundColor Gray
