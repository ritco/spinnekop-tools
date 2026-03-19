# ePlan Import Tool -- Installatie op live server share
# Gebruik: PowerShell -ExecutionPolicy Bypass -File install-live.ps1

$Server = "10.0.1.5"
$SharePath = "\\$Server\import"
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

# Kopieer naar share
Write-Host "Kopieren naar $SharePath..."
try {
    Copy-Item -Path $LocalExe -Destination $SharePath -Force
    Write-Host "OK: $ExeName geinstalleerd op $SharePath"
} catch {
    Write-Error "Kopieren mislukt: $_"
    exit 1
}
