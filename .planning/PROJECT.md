# BOM Import Tool — Release Management

## What This Is

Release management voor de `bom-import-tool.exe`, een PyInstaller GUI-applicatie die SolidWorks BOM Excel-bestanden omzet naar CSV's voor RidderIQ import. De tool draait op VMSERVERRUM (de RidderIQ server) en wordt gebruikt door twee mensen: Evy (BOM-validatie) en Rik (ontwikkeling + daadwerkelijke import). Het doel is dat Evy op een stabiele versie kan werken terwijl Rik verder bouwt.

## Core Value

Evy kan altijd een werkende versie van de tool gebruiken, ongeacht waar Rik in de ontwikkeling zit.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Stabiele versie voor Evy beschikbaar op de server, gescheiden van dev-versies
- [ ] Versienummering in de tool (zichtbaar in GUI)
- [ ] Build script dat lokaal de exe bouwt met versienummer
- [ ] Deploy script dat de exe naar de juiste map op de server kopieert (stable of dev)
- [ ] Rollback mogelijk naar vorige stabiele versie
- [ ] Evy hoeft niets te configureren — haar snelkoppeling werkt altijd

### Out of Scope

- CI/CD pipeline — te zwaar voor 2 gebruikers en 1 tool
- Git hosting (GitHub/GitLab) — scripts leven in Obsidian vault, lokale git volstaat
- Automatische updates — Evy's versie wordt handmatig gepromoot
- Multi-platform builds — alleen Windows, alleen deze server

## Context

- **Tool locatie server**: `C:\import\bom-import-tool\bom-import-tool.exe` (bereikbaar als `Z:\bom-import-tool\` via VPN)
- **Broncode**: `scripts/` in de Spinnekop Obsidian vault (lokaal op Rik's laptop)
- **Build**: PyInstaller via `bom-import-tool.spec`
- **Dependencies**: customtkinter, xlrd, openpyxl, pyodbc, pyinstaller
- **Server**: VMSERVERRUM (10.0.1.5), bereikbaar via VPN + Z: drive mapping
- **Evy's gebruik**: opent tool via RDP op de server, laadt Excel, bekijkt validatieresultaten
- **Rik's gebruik**: bouwt lokaal, test lokaal + op server, doet de CSV import in RidderIQ
- **SQL validatie**: werkt alleen op de server (localhost\RIDDERIQ, poort 1433 niet extern bereikbaar)
- **User-isolatie**: output gaat naar `C:\import\{omgeving}\{username}\`, concurrent gebruik ingebouwd

## Constraints

- **Netwerk**: VPN valt regelmatig weg — deploy scripts moeten robuust zijn (ping check)
- **Server toegang**: geen PowerShell Remoting, alleen Z: drive mapping en RDP
- **Bash/UNC**: UNC-paden werken niet in bash — altijd via .ps1 scripts
- **Lokale SQL**: SQL Server alleen bereikbaar op de server zelf, niet via VPN
- **Timeline**: Evy moet volgende week kunnen starten

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Semi-auto release management | Volledig geautomatiseerd is overkill voor 2 users, handmatig is te foutgevoelig | — Pending |
| Stable/dev mappenstructuur op server | Simpelste manier om Evy's versie te scheiden van dev builds | — Pending |
| Lokale git, geen remote | Scripts zijn onderdeel van Obsidian vault, geen apart software project | — Pending |

---
*Last updated: 2026-02-19 after initialization*
