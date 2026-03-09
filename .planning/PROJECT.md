# BOM Import Tool — Release Management

## What This Is

Release management voor de `bom-import-tool.exe` en `productiestructuur.exe`, twee PyInstaller GUI-applicaties voor Spinnekop BV. Beide tools draaien lokaal op laptops, hebben een eigen config.json, en updaten zichzelf automatisch via een netwerk share. Evy gebruikt de BOM Import Tool (SolidWorks BOM → RidderIQ CSV), Jurgen gebruikt de Productiestructuur Tool (phantom-vlaggen instellen).

## Core Value

Evy kan altijd een werkende versie van de tool gebruiken, ongeacht waar Rik in de ontwikkeling zit.

## Current Milestone: v2.0 Locatie Scanner — Productie

**Goal:** De werkende Locatie Scanner prototype (`scripts/locatie_scanner.py`) omzetten naar een stabiele productietool die magazijniers zelfstandig kunnen gebruiken.

**Prototype context (2026-03-09):**
- Flask + embedded HTML, single file, camera barcode scanning via html5-qrcode
- Offline wachtrij (localStorage) voor slechte wifi in magazijn
- Direct SQL INSERT in R_ITEMWAREHOUSELOCATION (Spinnekop Live 2)
- Barcodes bevatten PK_R_ITEM — lookup aangepast
- HTTP poort 5050, camera via Chrome flag workaround
- Draait op laptop consultant, telefoon verbindt via wifi

**Target features:**
- Server deploy als Windows Service op VMSERVERRUM (altijd beschikbaar)
- Gebruiker-identificatie (wie scant wat) met audit trail
- HTTPS voor camera zonder Chrome flag workaround

## Requirements

### Validated

- ✓ Stabiele versie voor Evy beschikbaar op de server, gescheiden van dev-versies — v1.0
- ✓ Versienummering in de tool (zichtbaar in GUI) — v1.0
- ✓ Build script dat lokaal de exe bouwt met versienummer — v1.0
- ✓ Deploy script dat de exe naar de dev-map op de server kopieert — v1.0
- ✓ Promote commando dat dev naar stable kopieert met archivering — v1.0
- ✓ Rollback mogelijk naar vorige stabiele versie (via archive) — v1.0
- ✓ Evy hoeft niets te configureren — haar snelkoppeling werkt altijd — v1.0
- ✓ Promote genereert version.json op Z: met versies van beide tools — v1.1
- ✓ Self-update check bij opstart via netwerk share met graceful fallback — v1.1
- ✓ CTk update dialog met versienummers en Updaten/Later knoppen — v1.1
- ✓ Exe-swap + automatische herstart na update — v1.1
- ✓ Productiestructuur tool met eigen config.json en identieke self-update — v1.1

### Active

(Defined in REQUIREMENTS.md for v2.0)

### Out of Scope

- CI/CD pipeline — te zwaar voor 2 gebruikers en 2 tools
- Git hosting (GitHub/GitLab) — scripts leven in Obsidian vault, lokale git volstaat
- Multi-platform builds — alleen Windows
- Installer/MSI — exe volstaat, geen installatie nodig
- Auto-update zonder dialog — gebruiker moet bewust kiezen om te updaten
- Gedeelde config.json — elke tool eigen config, voorkomt conflicten
- Update via internet — tools draaien intern, updates via LAN share

## Context

- **Shipped v1.0** op 2026-02-19 (3 fasen, 5 plannen, ~55 min)
- **Shipped v1.1** op 2026-02-26 (3 fasen, 5 plannen, ~222 min)
- **Twee tools live op Z:**
  - bom-import-tool.exe v1.2.1 (Evy)
  - productiestructuur.exe v1.0.0 (Jurgen)
- **Self-update werkt E2E**: version.json check → CTk dialog → exe-swap → herstart via explorer
- **Codebase**: ~5000 LOC Python + PowerShell in `scripts/`
- **Build pipeline**: PyInstaller → deploy naar Y: → promote naar Z: via promote.ps1
- **Server**: VMSERVERRUM (10.0.1.5), bereikbaar via VPN + Z:/Y: drive mapping
- **Dependencies**: customtkinter, xlrd, openpyxl, pyodbc, pyinstaller

## Constraints

- **Netwerk**: VPN valt regelmatig weg — deploy scripts moeten robuust zijn (ping check)
- **Server toegang**: geen PowerShell Remoting, alleen Z:/Y: drive mapping en RDP
- **Bash/UNC**: UNC-paden werken niet in bash — altijd via .ps1 scripts
- **SQL Server**: direct bereikbaar via VPN (poort 1433), geen RDP nodig voor queries
- **PyInstaller windowed**: `start ""` vanuit CREATE_NO_WINDOW context faalt — gebruik `explorer` voor exe-launch
- **Wifi magazijn**: slechte dekking door metaal — offline queue vereist
- **Camera op HTTP**: vereist Chrome flag of HTTPS — Chrome flag is per-device handmatig

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Semi-auto release management | Volledig geautomatiseerd is overkill voor 2 users, handmatig te foutgevoelig | ✓ Good — pipeline werkt betrouwbaar |
| Stable/dev mappenstructuur op server | Simpelste manier om Evy's versie te scheiden van dev builds | ✓ Good — Evy ongestoord, Rik vrij |
| Lokale git, geen remote | Scripts zijn onderdeel van Obsidian vault, geen apart software project | ✓ Good — past bij werkwijze |
| __version__ in main.py als single source of truth | Importeerbaar zonder circulaire deps, Python conventie | ✓ Good |
| Y: = import-test, Z: = import (stable) | Logische scheiding test vs productie | ✓ Good |
| Archive-before-overwrite bij promote | Rollback altijd mogelijk zonder extra tooling | ✓ Good |
| Eigen config per tool | Tools draaien op aparte machines, gedeeld config levert problemen | ✓ Good — v1.1 |
| Self-update via netwerk share (UNC) | Evy heeft geen Z: — tool checkt UNC pad rechtstreeks | ✓ Good — v1.1 |
| Threading-based timeout voor share access | Voorkomt 30s hang als share onbereikbaar is | ✓ Good — v1.1 |
| Two-phase update check (pre-GUI + post-GUI) | Voorkomt CTk dual-root crash | ✓ Good — v1.1 |
| explorer.exe voor exe-launch na update | start "" vanuit CREATE_NO_WINDOW veroorzaakt PyInstaller DLL failure | ✓ Good — v1.1 |
| Unblock-File na copy van UNC share | Verwijdert Zone.Identifier ADS, voorkomt Defender blokkade | ✓ Good — v1.1 |
| Flask + embedded HTML voor Locatie Scanner | Single file, geen build pipeline, snel te itereren | — Pending |
| Direct SQL INSERT ipv CSV import | Sneller, real-time feedback, geen import-cyclus | — Pending |

---
*Last updated: 2026-03-09 after v2.0 milestone start*
