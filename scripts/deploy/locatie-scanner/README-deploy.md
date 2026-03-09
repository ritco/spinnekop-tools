# Locatie Scanner - Deploy op Server

## Prereqs

- Python 3.12 geinstalleerd op VMSERVERRUM
- VPN actief (OpenVPN Connect)
- Z: drive gemapped (`\\10.0.1.5\import`)

## Stappen

### 0. Wheels downloaden (eenmalig, op PC met internet)

De server heeft geen internet. Download Python wheels lokaal:

```powershell
cd scripts/deploy/locatie-scanner
pip download -r requirements.txt -d wheels --only-binary :all: --platform win_amd64 --python-version 312
```

Dit downloadt o.a. `cryptography` (nodig voor SSL certificaat generatie).
De `wheels/` map wordt automatisch meegekopieerd door het install script.

### 1. Bestanden klaarzetten

Kopieer naar `Z:\deploy\locatie-scanner\`:
- `install-service.ps1` (dit script)
- `requirements.txt`
- `locatie_scanner.py` (uit `scripts/`)
- `wheels/` map (uit stap 0)

### 2. RDP naar server

Verbind via Remote Desktop naar `10.0.1.5` met user `ridderadmin`.

### 3. PowerShell als Administrator

Open PowerShell **als Administrator** (rechtermuisklik > "Als administrator uitvoeren").

### 4. Script draaien

```powershell
cd C:\import\deploy\locatie-scanner
.\install-service.ps1
```

Het script doet automatisch:
- NSSM downloaden (als nog niet aanwezig)
- Python venv aanmaken + dependencies installeren
- Windows Service configureren (auto-start, crash recovery)
- Firewall rule openzetten
- Service starten en testen

### 5. Testen

Open op telefoon (in magazijn-wifi): **https://10.0.1.5:5050**

Bij eerste keer: accepteer de certificaatwaarschuwing (eenmalig, self-signed cert).
Daarna werkt camera-toegang zonder Chrome flags.

Verwacht:
- Locatie Scanner laadt
- Locatie vergrendelen werkt
- Artikel scannen en opslaan werkt

## Troubleshooting

| Probleem | Oplossing |
|----------|-----------|
| App laadt niet | Check `nssm status LocatieScanner` |
| Service crashed | Bekijk `C:\LocatieScanner\logs\service.log` |
| Python pad fout | Pas `$PythonExe` aan in install-service.ps1 |
| Poort bezet | Pas `$Port` aan in install-service.ps1 |

### Handmatige service commands

```powershell
nssm status LocatieScanner     # Status opvragen
nssm restart LocatieScanner    # Herstarten
nssm stop LocatieScanner       # Stoppen
nssm start LocatieScanner      # Starten
nssm remove LocatieScanner confirm  # Volledig verwijderen
```

### Logs bekijken

```powershell
Get-Content C:\LocatieScanner\logs\service.log -Tail 50
```
