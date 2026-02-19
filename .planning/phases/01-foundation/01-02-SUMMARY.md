---
plan: 01-02
phase: 01-foundation
status: complete
started: 2026-02-19
completed: 2026-02-19
---

# Plan 01-02 Summary: Server-mappenstructuur + migratie + shortcut

## What Was Built

PowerShell setup script (`scripts/setup-server-structure.ps1`) dat de server-mappenstructuur aanmaakt voor release management. Uitgevoerd op VMSERVERRUM via RDP als ridderadmin.

## Changes Made

### Created
- `scripts/setup-server-structure.ps1` — idempotent setup script (5 stappen + verificatie)

### Server Changes (via RDP)
- `C:\import\archive\` aangemaakt (rollback-locatie)
- `C:\import-test\` aangemaakt met `speel\` en `live\` submappen (dev/test output)
- `C:\import\bom-import-tool.exe` — exe gemigreerd vanuit oude submap
- `C:\import\bom-import-tool\` — oude map verwijderd (bevatte verouderde bronbestanden)
- `C:\Users\Public\Desktop\BOM Import Tool.lnk` — shortcut naar stable exe

## Deviations

1. `#Requires -RunAsAdministrator` verwijderd uit script — niet nodig voor de directory-operaties en blokkeerde uitvoering
2. Shortcut aanmaken vereiste apart als Administrator draaien (Public Desktop schrijfrechten)
3. Oude map bevatte nog bestanden (oude broncode, testscripts) — handmatig opgeruimd via Z: drive

## Decisions

- Setup-scripts NIET als admin vereisen tenzij strict nodig
- Oude bronbestanden op server niet bewaren — canonical source is de Obsidian vault

## Requirements Addressed

- SRV-01: Stabiele versie op `C:\import\bom-import-tool.exe` ✓
- SRV-02: Dev/test locatie op `C:\import-test\` ✓
- SRV-03: Desktop-snelkoppeling op Public Desktop ✓
