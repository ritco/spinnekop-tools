# BOM Import Tool — Release Management

## What This Is

Release management voor de `bom-import-tool.exe` en `productiestructuur.exe`, twee PyInstaller GUI-applicaties voor Spinnekop BV. Beide tools draaien lokaal op laptops, hebben een eigen config.json, en updaten zichzelf automatisch via een netwerk share. Evy gebruikt de BOM Import Tool (SolidWorks BOM → RidderIQ CSV), Jurgen gebruikt de Productiestructuur Tool (phantom-vlaggen instellen).

## Core Value

Evy kan altijd een werkende versie van de tool gebruiken, ongeacht waar Rik in de ontwikkeling zit.

## Current Milestone: v4.0 Rapporterings-DB

**Goal:** Een aparte rapporterings-database bouwen op dezelfde SQL Server, gevuld via nachtelijke Python ETL, met drie lagen (raw/core/report) als fundament voor nacalculatie en operationele rapportering.

**Context (2026-03-19):**
- Bron: `Spinnekop Live 2` op `10.0.1.5\RIDDERIQ` (SQL Server 2016, bereikbaar via VPN + pyodbc)
- Nieuwe database: `Spinnekop_Reporting` op dezelfde instantie — productie-DB volledig ontzien
- Drie schemas: `raw` (nachtelijke snapshot + append), `core` (feiten/dimensies), `report` (views voor Power BI)
- Uren-keten bevestigd: `R_TIMESHEETLINE → R_PRODUCTIONORDER → R_SALESORDER`
- Aankoop via inkoopfacturen (link TBD bij volgende VPN-sessie)
- Power BI Desktop gratis als start; Pro-licentie afhankelijk van M365-plan (checken bij Lebon IT)
- ETL: Python script via Windows Task Scheduler, nachtelijk (append per dag met `snapshot_date`)

**Target features:**
- Rapporterings-database aanmaken met raw/core/report schemas
- Nachtelijke ETL: relevante RidderIQ-tabellen kopiëren naar raw
- Core-laag: feiten (uren, aankoop) + dimensies (VO, medewerker, artikel, datum)
- Report-laag: views voor nacalculatie en operationele KPI's
- Power BI rapport voor pilot Horafrost (uren per VO)
- FK-verkenning inkoopfacturen → VO (voor aankoop in core-laag)

## Previous Milestone: v3.0 ePlan Import Tool

**Goal:** Een tweede import tool bouwen naast de BOM Import Tool — leest ePlan stuklijst-exports (Excel), koppelt componenten aan bestaande RidderIQ-artikelen of maakt nieuwe aan, en importeert stuklijsten + regels klaar voor gebruik in productiebons.

**Context (2026-03-18):**
- ePlan exporteert materiaalslijst als Excel: Project naam, Naam in schema, Fabrikant, Bestelnummer (format: `Fabrikant.Onderdeel`), Hoeveelheid
- Onderdeel-nummer (`GV2ME08` uit `SE.GV2ME08`) zit in artikelomschrijving in RidderIQ
- Elektrische componenten: handmatig afboeken (REGISTRATIONPATH=5), stock nooit negatief (INVENTORYKIND=4)
- Zelfde tech stack en build/deploy pipeline als BOM Import Tool

**Target features:**
- ePlan Excel inlezen en kwaliteitscontrole uitvoeren
- Artikelen opzoeken in RidderIQ op basis van Bestelnummer
- Nieuwe artikelen aanmaken als ze niet bestaan (groep 26, 26xxx codes)
- Stuklijst header + regels genereren en importeren
- CustomTkinter GUI (zelfde patroon als gui.py)
- Build + deploy via GitHub releases, tag prefix `eplan-`

## Previous Milestone: v3.0 ePlan Import Tool

**Goal:** Een tweede import tool bouwen naast de BOM Import Tool — leest ePlan stuklijst-exports (Excel), koppelt componenten aan bestaande RidderIQ-artikelen of maakt nieuwe aan, en importeert stuklijsten + regels klaar voor gebruik in productiebons.

**Status:** Phases 11-13 gepland (2026-03-18), nog niet uitgevoerd.

## Previous Milestone: v2.0 Locatie Scanner — Productie

**Goal:** De werkende Locatie Scanner prototype (`scripts/locatie_scanner.py`) omzetten naar een stabiele productietool die magazijniers zelfstandig kunnen gebruiken.

**Status:** Phase 7+8 shipped (2026-03-11). Phase 9 (gebruiker-identificatie) geparkeerd.

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
- Update via internet — tools draaien intern, updates via GitHub releases (via HTTPS)
- Locatie Scanner gebruiker-identificatie (Phase 9) — geparkeerd, later

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
*Last updated: 2026-03-18 after v3.0 milestone start*
