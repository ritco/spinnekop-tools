# =============================================================================
# BOM Import Tool — Installatie (TEST / pre-release versies)
# =============================================================================
# Wat dit script doet:
#   1. Vraagt waar de tool geinstalleerd moet worden
#   2. Downloadt de laatste testversie (pre-release) van GitHub
#   3. Maakt config.json aan (SQL-instellingen invullen na installatie)
#   4. Maakt een snelkoppeling op het bureaublad (met TEST-label)
#
# Gebruik: rechtsklik → "Uitvoeren met PowerShell"
# =============================================================================

$ErrorActionPreference = "Stop"
$TOOL_NAME    = "bom-import-tool"
$EXE_NAME     = "bom-import-tool.exe"
$GITHUB_REPO  = "ritco/spinnekop-tools"
$CHANNEL      = "prerelease"
$DISPLAY_NAME = "BOM Import Tool"

Write-Host ""
Write-Host "=============================================" -ForegroundColor Magenta
Write-Host "  $DISPLAY_NAME — Installatie (TEST)"        -ForegroundColor Magenta
Write-Host "=============================================" -ForegroundColor Magenta
Write-Host ""

# --- Installatiemap kiezen ---
$default_dir = "C:\Tools\BOM-Import-Test"
$install_dir = Read-Host "Installatiemap [$default_dir]"
if ([string]::IsNullOrWhiteSpace($install_dir)) {
    $install_dir = $default_dir
}

if (-not (Test-Path $install_dir)) {
    New-Item -ItemType Directory -Path $install_dir -Force | Out-Null
    Write-Host "Map aangemaakt: $install_dir" -ForegroundColor Green
}

# --- Download exe van GitHub (laatste pre-release) ---
Write-Host ""
Write-Host "Laatste testversie ophalen van GitHub..." -ForegroundColor Yellow

try {
    # Haal alle releases op en zoek de laatste pre-release voor deze tool
    $releases_url = "https://api.github.com/repos/$GITHUB_REPO/releases?per_page=20"
    $headers  = @{ "User-Agent" = "spinnekop-installer"; "Accept" = "application/vnd.github.v3+json" }
    $releases = Invoke-RestMethod -Uri $releases_url -Headers $headers -TimeoutSec 15

    # Filter op pre-releases met de tool-prefix in de tag
    $tool_prefix = ($TOOL_NAME -split "-")[0] + "-"
    $release = $releases | Where-Object {
        $_.tag_name -like "$tool_prefix*" -and $_.prerelease -eq $true
    } | Select-Object -First 1

    # Als geen pre-release gevonden, gebruik stabiele versie
    if (-not $release) {
        Write-Host "Geen pre-release gevonden — meest recente stabiele versie wordt gebruikt." -ForegroundColor Yellow
        $release = $releases | Where-Object {
            $_.tag_name -like "$tool_prefix*"
        } | Select-Object -First 1
    }

    if (-not $release) {
        throw "Geen release gevonden voor '$TOOL_NAME' in repo $GITHUB_REPO"
    }

    $asset = $release.assets | Where-Object { $_.name -eq $EXE_NAME } | Select-Object -First 1
    if (-not $asset) {
        throw "Geen '$EXE_NAME' gevonden in release $($release.tag_name)"
    }

    $version  = $release.tag_name
    $exe_path = Join-Path $install_dir $EXE_NAME

    Write-Host "Downloaden: $EXE_NAME ($version)..." -ForegroundColor Yellow
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

# --- config.json aanmaken (als die nog niet bestaat) ---
$config_path = Join-Path $install_dir "config.json"
if (-not (Test-Path $config_path)) {
    $config = @{
        sql_server         = "10.0.1.5\RIDDERIQ"
        sql_auth           = "sql"
        sql_user           = "ridderadmin"
        sql_password       = "riad01*"
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
    $desktop  = [Environment]::GetFolderPath("Desktop")
    $shortcut = Join-Path $desktop "$DISPLAY_NAME (TEST).lnk"
    $wsh      = New-Object -ComObject WScript.Shell
    $lnk      = $wsh.CreateShortcut($shortcut)
    $lnk.TargetPath       = Join-Path $install_dir $EXE_NAME
    $lnk.WorkingDirectory = $install_dir
    $lnk.Description      = "$DISPLAY_NAME (testversie)"
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
Write-Host "  Kanaal  : TEST (pre-release updates)"
Write-Host ""
Write-Host "  De tool controleert automatisch op updates bij elke opstart."
Write-Host "  Testversies worden automatisch opgepikt zodra ze beschikbaar zijn."
Write-Host ""
Read-Host "Druk op Enter om te sluiten"
