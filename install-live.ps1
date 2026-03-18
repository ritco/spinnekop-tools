# =============================================================================
# BOM Import Tool — Installatie (LIVE / stabiele versies)
# =============================================================================
# Wat dit script doet:
#   1. Vraagt waar de tool geinstalleerd moet worden
#   2. Downloadt de laatste stabiele versie van GitHub
#   3. Maakt config.json aan (SQL-instellingen invullen na installatie)
#   4. Maakt een snelkoppeling op het bureaublad
#
# Gebruik: rechtsklik → "Uitvoeren met PowerShell"
# =============================================================================

$ErrorActionPreference = "Stop"
$TOOL_NAME    = "bom-import-tool"
$EXE_NAME     = "bom-import-tool.exe"
$GITHUB_REPO  = "ritco/spinnekop-tools"
$CHANNEL      = "stable"
$DISPLAY_NAME = "BOM Import Tool"

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  $DISPLAY_NAME — Installatie (LIVE)"        -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# --- Installatiemap kiezen ---
$default_dir = "C:\Tools\BOM-Import"
$install_dir = Read-Host "Installatiemap [$default_dir]"
if ([string]::IsNullOrWhiteSpace($install_dir)) {
    $install_dir = $default_dir
}

if (-not (Test-Path $install_dir)) {
    New-Item -ItemType Directory -Path $install_dir -Force | Out-Null
    Write-Host "Map aangemaakt: $install_dir" -ForegroundColor Green
}

# --- Download exe van GitHub ---
Write-Host ""
Write-Host "Laatste versie ophalen van GitHub..." -ForegroundColor Yellow

try {
    $release_url = "https://api.github.com/repos/$GITHUB_REPO/releases/latest"
    $headers = @{ "User-Agent" = "spinnekop-installer"; "Accept" = "application/vnd.github.v3+json" }
    $release  = Invoke-RestMethod -Uri $release_url -Headers $headers -TimeoutSec 15
    $asset    = $release.assets | Where-Object { $_.name -eq $EXE_NAME } | Select-Object -First 1

    if (-not $asset) {
        throw "Geen '$EXE_NAME' gevonden in release $($release.tag_name)"
    }

    $version     = $release.tag_name -replace '[^\d\.]', ''
    $exe_path    = Join-Path $install_dir $EXE_NAME

    Write-Host "Downloaden: $EXE_NAME v$version..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $exe_path -TimeoutSec 120
    Unblock-File -Path $exe_path
    Write-Host "Download klaar: $exe_path" -ForegroundColor Green
}
catch {
    Write-Host "FOUT bij downloaden: $_" -ForegroundColor Red
    Write-Host "Controleer je internetverbinding en probeer opnieuw."
    Read-Host "Druk op Enter om te sluiten"
    exit 1
}

# --- SQL wachtwoord vragen en encrypteren ---
Write-Host ""
Write-Host "SQL Server wachtwoord instellen..." -ForegroundColor Yellow
Write-Host "  Server : 10.0.1.5\RIDDERIQ" -ForegroundColor DarkGray
Write-Host "  Login  : ridderadmin" -ForegroundColor DarkGray
Write-Host ""
$sql_secure  = Read-Host "SQL wachtwoord" -AsSecureString
$sql_dpapi   = "dpapi:" + (ConvertFrom-SecureString $sql_secure)

# --- config.json aanmaken (als die nog niet bestaat) ---
$config_path = Join-Path $install_dir "config.json"
if (-not (Test-Path $config_path)) {
    $config = @{
        sql_server         = "10.0.1.5\RIDDERIQ"
        sql_auth           = "sql"
        sql_user           = "ridderadmin"
        sql_password       = $sql_dpapi
        databases          = @{
            speel = "Speeltuin 2"
            live  = "Spinnekop Live 2"
        }
        output_basis       = $install_dir
        update_github_repo = $GITHUB_REPO
        update_channel     = $CHANNEL
    }
    $config | ConvertTo-Json -Depth 3 | Set-Content -Path $config_path -Encoding UTF8
    Write-Host "config.json aangemaakt: $config_path" -ForegroundColor Green
} else {
    Write-Host "config.json bestaat al — niet overschreven." -ForegroundColor Cyan
}

# --- Snelkoppeling op bureaublad ---
try {
    $desktop    = [Environment]::GetFolderPath("Desktop")
    $shortcut   = Join-Path $desktop "$DISPLAY_NAME.lnk"
    $wsh        = New-Object -ComObject WScript.Shell
    $lnk        = $wsh.CreateShortcut($shortcut)
    $lnk.TargetPath       = Join-Path $install_dir $EXE_NAME
    $lnk.WorkingDirectory = $install_dir
    $lnk.Description      = "$DISPLAY_NAME (live)"
    $lnk.Save()
    Write-Host "Snelkoppeling aangemaakt: $shortcut" -ForegroundColor Green
}
catch {
    Write-Host "Snelkoppeling niet aangemaakt (niet kritiek): $_" -ForegroundColor DarkGray
}

# --- Klaar ---
Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  Installatie geslaagd!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Versie  : $version"
Write-Host "  Locatie : $install_dir"
Write-Host "  Kanaal  : LIVE (alleen stabiele updates)"
Write-Host ""
Write-Host "  De tool controleert automatisch op updates bij elke opstart."
Write-Host ""
Read-Host "Druk op Enter om te sluiten"
