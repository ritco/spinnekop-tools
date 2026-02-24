# Roadmap: BOM Import Tool — Release Management

## Milestones

- :white_check_mark: **v1.0 Release Management** - Phases 1-3 (shipped 2026-02-19)
- :construction: **v1.1 Config + Self-update** - Phases 4-6 (in progress)

## Phases

<details>
<summary>v1.0 Release Management (Phases 1-3) - SHIPPED 2026-02-19</summary>

### Phase 1: Foundation
**Goal**: The tool has a version number and the server has the folder structure that separates Evy's stable version from dev builds
**Plans**: 2 plans

Plans:
- [x] 01-01: Versievariabele in main.py + dynamische title bar
- [x] 01-02: Server-mappenstructuur, exe-migratie en Desktop snelkoppeling

### Phase 2: Build & Deploy
**Goal**: Rik can build a versioned exe and push it to the dev folder on the server with a single command
**Plans**: 2 plans

Plans:
- [x] 02-01: Build script met __version__ en PyInstaller
- [x] 02-02: Deploy script met ping check en drive mapping

### Phase 3: Stable Release
**Goal**: Rik can promote dev to stable with archive of the old version
**Plans**: 1 plan

Plans:
- [x] 03-01: promote.ps1 met archive + promote + verify

</details>

### v1.1 Config + Self-update (In Progress)

**Milestone Goal:** Beide tools (bom-import-tool + productiestructuur) draaien lokaal met config.json, checken bij opstart of er een update is op de netwerk share, en Evy heeft v1.2.0 werkend op haar laptop.

- [ ] **Phase 4: Promote v1.2.0 + version.json** - Promote genereert version.json en zet v1.2.0 live op Z:
- [ ] **Phase 5: Self-update** - Tool checkt bij opstart op updates en biedt update-dialog aan
- [ ] **Phase 6: Productiestructuur Config + Update** - Productiestructuur tool krijgt eigen config.json en self-update

## Phase Details

### Phase 4: Promote v1.2.0 + version.json
**Goal**: promote.ps1 genereert een version.json met versies van beide tools, en v1.2.0 (config-refactoring) staat live op Z: voor Evy
**Depends on**: Phase 3 (v1.0 promote pipeline)
**Requirements**: PRV-01, PRV-02
**Success Criteria** (what must be TRUE):
  1. Na promote staat er een version.json op Z: met daarin de versienummers van bom-import-tool en productiestructuur
  2. v1.2.0 van bom-import-tool staat op Z: (stable) en Evy kan het starten via haar snelkoppeling
  3. De oude versie is gearchiveerd in Z:\archive\ conform bestaand archive-mechanisme
**Plans**: 1 plan

Plans:
- [ ] 04-01-PLAN.md — Refactor promote.ps1 met -Tool parameter, version.json generatie, en promote v1.2.0

### Phase 5: Self-update
**Goal**: bom-import-tool checkt bij opstart of er een nieuwere versie beschikbaar is op de netwerk share en biedt de gebruiker een update aan
**Depends on**: Phase 4 (version.json moet bestaan op Z:)
**Requirements**: UPD-01, UPD-02, UPD-03, UPD-04
**Success Criteria** (what must be TRUE):
  1. Bij opstart leest de tool version.json van `\\10.0.1.5\import` en vergelijkt met de lokale versie
  2. Als er een nieuwere versie is, ziet de gebruiker een dialog met de huidige en nieuwe versienummers en een "Updaten" knop
  3. Bij klikken op "Updaten" wordt de nieuwe exe gekopieerd naar de lokale locatie en herstart de tool automatisch
  4. Als de netwerk share niet bereikbaar is, start de tool gewoon op zonder foutmelding of vertraging
**Plans**: TBD

Plans:
- [ ] 05-01: TBD

### Phase 6: Productiestructuur Config + Update
**Goal**: productiestructuur.exe heeft een eigen config.json en dezelfde self-update logica als bom-import-tool
**Depends on**: Phase 5 (self-update logica is bewezen in bom-import-tool)
**Requirements**: PST-01, PST-02
**Success Criteria** (what must be TRUE):
  1. productiestructuur.exe leest SQL server, credentials en databases uit een eigen config.json naast de exe
  2. Bij opstart checkt productiestructuur.exe version.json op de netwerk share en biedt een update-dialog aan (identiek gedrag als bom-import-tool)
  3. Als config.json ontbreekt, opent de settings dialog automatisch (consistent met bom-import-tool gedrag)
**Plans**: TBD

Plans:
- [ ] 06-01: TBD

## Progress

**Execution Order:** Phase 4 -> Phase 5 -> Phase 6

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 2/2 | Complete | 2026-02-19 |
| 2. Build & Deploy | v1.0 | 2/2 | Complete | 2026-02-19 |
| 3. Stable Release | v1.0 | 1/1 | Complete | 2026-02-19 |
| 4. Promote v1.2.0 + version.json | v1.1 | 0/1 | Planned | - |
| 5. Self-update | v1.1 | 0/? | Not started | - |
| 6. Productiestructuur Config + Update | v1.1 | 0/? | Not started | - |
