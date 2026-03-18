# =============================================================================
# BOM Import Tool - Installatie (TEST / pre-release versies)
# =============================================================================
# Gebruik: PowerShell -ExecutionPolicy Bypass -File install-test.ps1
# =============================================================================

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$EXE_NAME     = "bom-import-tool.exe"
$GITHUB_REPO  = "ritco/spinnekop-tools"
$CHANNEL      = "prerelease"
$DISPLAY_NAME = "BOM Import Tool"
$TOOL_PREFIX  = "bom-"

Write-Host ""
Write-Host "=============================================" -ForegroundColor Magenta
Write-Host "  $DISPLAY_NAME - Installatie (TEST)"        -ForegroundColor Magenta
Write-Host "=============================================" -ForegroundColor Magenta
Write-Host ""

# --- Installatiemap kiezen ---
$default_dir = "C:\Tools\BOM-Import-Test"
$install_dir = Read-Host "Installatiemap [$default_dir]"
if ([string]::IsNullOrWhiteSpace($install_dir)) { $install_dir = $default_dir }

if (-not (Test-Path $install_dir)) {
    New-Item -ItemType Directory -Path $install_dir -Force | Out-Null
    Write-Host "Map aangemaakt: $install_dir" -ForegroundColor Green
}

# --- GitHub release opzoeken ---
Write-Host ""
Write-Host "Stap 1/3: Release opzoeken op GitHub..." -ForegroundColor Yellow

try {
    $wc = New-Object System.Net.WebClient
    $wc.Headers.Add("User-Agent", "spinnekop-installer")
    $wc.Headers.Add("Accept", "application/vnd.github.v3+json")

    $json = $wc.DownloadString("https://api.github.com/repos/$GITHUB_REPO/releases?per_page=20")
    $releases = $json | ConvertFrom-Json

    $release = $releases | Where-Object { $_.tag_name -like "$TOOL_PREFIX*" -and $_.prerelease -eq $true } | Select-Object -First 1
    if (-not $release) {
        Write-Host "Geen pre-release gevonden - meest recente stabiele versie wordt gebruikt." -ForegroundColor Yellow
        $release = $releases | Where-Object { $_.tag_name -like "$TOOL_PREFIX*" } | Select-Object -First 1
    }
    if (-not $release) { throw "Geen release gevonden voor '$TOOL_PREFIX' in repo $GITHUB_REPO" }

    $asset = $release.assets | Where-Object { $_.name -eq $EXE_NAME } | Select-Object -First 1
    if (-not $asset) { throw "Geen '$EXE_NAME' gevonden in release $($release.tag_name)" }

    $version      = $release.tag_name
    $download_url = $asset.browser_download_url
    Write-Host "Gevonden: $version" -ForegroundColor Green
}
catch {
    Write-Host "FOUT bij opzoeken release: $_" -ForegroundColor Red
    Read-Host "Druk op Enter om te sluiten"
    exit 1
}

# --- Exe downloaden ---
Write-Host ""
Write-Host "Stap 2/3: Downloaden $EXE_NAME ($version)..." -ForegroundColor Yellow
Write-Host "  (kan 1-2 minuten duren, ~35MB)" -ForegroundColor DarkGray

$exe_path = Join-Path $install_dir $EXE_NAME
try {
    $wc2 = New-Object System.Net.WebClient
    $wc2.Headers.Add("User-Agent", "spinnekop-installer")
    $wc2.DownloadFile($download_url, $exe_path)
    Unblock-File -Path $exe_path
    Write-Host "Download klaar: $exe_path" -ForegroundColor Green
}
catch {
    Write-Host "FOUT bij downloaden: $_" -ForegroundColor Red
    Read-Host "Druk op Enter om te sluiten"
    exit 1
}

# --- SQL wachtwoord ---
Write-Host ""
Write-Host "Stap 3/3: SQL Server wachtwoord instellen..." -ForegroundColor Yellow
Write-Host "  Server : 10.0.1.5\RIDDERIQ" -ForegroundColor DarkGray
Write-Host "  Login  : ridderadmin" -ForegroundColor DarkGray
Write-Host ""
$sql_secure = Read-Host "SQL wachtwoord" -AsSecureString
$sql_dpapi  = "dpapi:" + (ConvertFrom-SecureString $sql_secure)

# --- config.json ---
$config_path = Join-Path $install_dir "config.json"
if (-not (Test-Path $config_path)) {
    $config = @{
        sql_server         = "10.0.1.5\RIDDERIQ"
        sql_auth           = "sql"
        sql_user           = "ridderadmin"
        sql_password       = $sql_dpapi
        databases          = @{ speel = "Speeltuin 2"; live = "Spinnekop Live 2" }
        output_basis       = $install_dir
        update_github_repo = $GITHUB_REPO
        update_channel     = $CHANNEL
    }
    $config | ConvertTo-Json -Depth 3 | Set-Content -Path $config_path -Encoding UTF8
    Write-Host "config.json aangemaakt: $config_path" -ForegroundColor Green
} else {
    Write-Host "config.json bestaat al - niet overschreven." -ForegroundColor Cyan
}

# --- Snelkoppeling ---
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
Write-Host ""
Read-Host "Druk op Enter om te sluiten"
