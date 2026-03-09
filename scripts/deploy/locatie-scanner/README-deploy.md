# Locatie Scanner - Deploy op Server

## Prereqs

- Python 3.12 geinstalleerd op VMSERVERRUM
- VPN actief (OpenVPN Connect)
- Z: drive gemapped (`\\10.0.1.5\import`)

## Stappen

### 1. Bestanden klaarzetten

Kopieer naar `Z:\deploy\locatie-scanner\`:
- `install-service.ps1` (dit script)
- `requirements.txt`
- `locatie_scanner.py` (uit `scripts/`)

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

Open op telefoon (in magazijn-wifi): **http://10.0.1.5:5050**

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
