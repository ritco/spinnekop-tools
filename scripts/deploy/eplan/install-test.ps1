# ePlan Import Tool -- Installatie op test server share
# Gebruik: PowerShell -ExecutionPolicy Bypass -File install-test.ps1

$Server = "10.0.1.5"
$SharePath = "\\$Server\import-test"
$ExeName = "eplan-import-tool.exe"
$LocalExe = Join-Path $PSScriptRoot "..\..\dist\$ExeName"

# Ping check
Write-Host "Ping check op $Server..."
if (-not (Test-Connection -ComputerName $Server -Count 1 -Quiet -ErrorAction SilentlyContinue)) {
    Write-Error "Server $Server niet bereikbaar. Controleer VPN."
    exit 1
}

# Controleer lokale exe
if (-not (Test-Path $LocalExe)) {
    Write-Error "Exe niet gevonden: $LocalExe. Bouw eerst met PyInstaller."
    exit 1
}

# Kopieer naar test share
Write-Host "Kopieren naar test server share $SharePath..."
try {
    Copy-Item -Path $LocalExe -Destination $SharePath -Force
    Write-Host "OK: $ExeName geinstalleerd op test server share $SharePath"
} catch {
    Write-Error "Kopieren mislukt: $_"
    exit 1
}
