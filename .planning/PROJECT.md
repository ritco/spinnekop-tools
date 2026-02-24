# BOM Import Tool — Release Management

## What This Is

Release management voor de `bom-import-tool.exe`, een PyInstaller GUI-applicatie die SolidWorks BOM Excel-bestanden omzet naar CSV's voor RidderIQ import. De tool draait op VMSERVERRUM (de RidderIQ server) en wordt gebruikt door twee mensen: Evy (BOM-validatie) en Rik (ontwikkeling + daadwerkelijke import). Evy werkt op een stabiele versie terwijl Rik vrij kan doorontwikkelen via een gescheiden dev/stable pipeline.

## Core Value

Evy kan altijd een werkende versie van de tool gebruiken, ongeacht waar Rik in de ontwikkeling zit.

## Requirements

### Validated

- ✓ Stabiele versie voor Evy beschikbaar op de server, gescheiden van dev-versies — v1.0
- ✓ Versienummering in de tool (zichtbaar in GUI) — v1.0
- ✓ Build script dat lokaal de exe bouwt met versienummer — v1.0
- ✓ Deploy script dat de exe naar de dev-map op de server kopieert — v1.0
- ✓ Promote commando dat dev naar stable kopieert met archivering — v1.0
- ✓ Rollback mogelijk naar vorige stabiele versie (via archive) — v1.0
- ✓ Evy hoeft niets te configureren — haar snelkoppeling werkt altijd — v1.0

### Active

(None — next milestone scope TBD)

### Out of Scope

- CI/CD pipeline — te zwaar voor 2 gebruikers en 1 tool
- Git hosting (GitHub/GitLab) — scripts leven in Obsidian vault, lokale git volstaat
- Automatische updates — Evy's versie wordt handmatig gepromoot
- Multi-platform builds — alleen Windows, alleen deze server
- Installer/MSI — exe volstaat, geen installatie nodig

## Context

- **Shipped v1.0** op 2026-02-19 (~55 min totale executie, 3 fasen, 5 plannen)
- **Codebase**: ~5000 LOC Python + PowerShell in `scripts/`
- **Tool locatie server**: `C:\import\bom-import-tool.exe` (stable), `C:\import-test\` (dev)
- **Broncode**: `scripts/` in de Spinnekop Obsidian vault (lokaal op Rik's laptop)
- **Build pipeline**: `build.ps1` → `deploy.ps1` → `promote.ps1`
- **Server**: VMSERVERRUM (10.0.1.5), bereikbaar via VPN + Z:/Y: drive mapping
- **Dependencies**: customtkinter, xlrd, openpyxl, pyodbc, pyinstaller

## Constraints

- **Netwerk**: VPN valt regelmatig weg — deploy scripts moeten robuust zijn (ping check)
- **Server toegang**: geen PowerShell Remoting, alleen Z:/Y: drive mapping en RDP
- **Bash/UNC**: UNC-paden werken niet in bash — altijd via .ps1 scripts
- **SQL Server**: direct bereikbaar via VPN (poort 1433), geen RDP nodig voor queries

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Semi-auto release management | Volledig geautomatiseerd is overkill voor 2 users, handmatig te foutgevoelig | ✓ Good — pipeline werkt betrouwbaar |
| Stable/dev mappenstructuur op server | Simpelste manier om Evy's versie te scheiden van dev builds | ✓ Good — Evy ongestoord, Rik vrij |
| Lokale git, geen remote | Scripts zijn onderdeel van Obsidian vault, geen apart software project | ✓ Good — past bij werkwijze |
| __version__ in main.py als single source of truth | Importeerbaar zonder circulaire deps, Python conventie | ✓ Good |
| Y: = import-test, Z: = import (stable) | Logische scheiding test vs productie | ✓ Good |
| Archive-before-overwrite bij promote | Rollback altijd mogelijk zonder extra tooling | ✓ Good |
| Setup-scripts niet als admin vereisen | Vermijdt onnodige privilege-escalatie | ✓ Good |

---
*Last updated: 2026-02-24 after v1.0 milestone*
