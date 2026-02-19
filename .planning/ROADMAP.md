# Roadmap: BOM Import Tool — Release Management

## Overview

The bom-import-tool.exe gets a proper release structure so Evy always has a working stable version while Rik develops freely. Three phases: first the versioning and server folder layout, then the build/deploy scripts that automate Rik's workflow, then the promote + archive mechanism that gives Evy a protected stable channel.

## Phases

- [x] **Phase 1: Foundation** - Version the tool and create the stable/dev folder structure on the server
- [x] **Phase 2: Build & Deploy** - Scripts to build the exe with version embedded and push to import-test/
- [ ] **Phase 3: Stable Release** - Promote command that moves dev to stable with archive of old version

## Phase Details

### Phase 1: Foundation
**Goal**: The tool has a version number and the server has the folder structure that separates Evy's stable version from dev builds
**Depends on**: Nothing (first phase)
**Requirements**: VER-01, VER-02, SRV-01, SRV-02, SRV-03
**Success Criteria** (what must be TRUE):
  1. The tool source code has a single version variable (semver) that is the single source of truth
  2. When the exe runs, the title bar shows the version number and active environment
  3. The server has `C:\import\bom-import-tool.exe` (stable) and `C:\import-test\` (dev) with `speel\` and `live\` subdirectories
  4. The server has `C:\import\archive\` for previous versions
  5. Evy has a Public Desktop shortcut that points to `C:\import\bom-import-tool.exe`
**Plans**: 2 plans

Plans:
- [x] 01-01-PLAN.md — Versievariabele in main.py + dynamische title bar met versie en omgeving in gui.py
- [x] 01-02-PLAN.md — Server-mappenstructuur, exe-migratie en Public Desktop snelkoppeling

### Phase 2: Build & Deploy
**Goal**: Rik can build a versioned exe and push it to the dev folder on the server with a single command
**Depends on**: Phase 1
**Requirements**: BLD-01, BLD-02
**Success Criteria** (what must be TRUE):
  1. Running the build script produces an exe with the version from the source variable embedded in the filename or readable from the binary
  2. Running the deploy script copies the exe to `C:\import-test\` after verifying VPN/ping connectivity — and fails cleanly if the server is unreachable
  3. Rik can go from source change to testable exe on the server in one command sequence
**Plans**: 2 plans

Plans:
- [x] 02-01-PLAN.md — Build script: leest __version__ uit main.py, draait PyInstaller, produceert versioned exe
- [x] 02-02-PLAN.md — Deploy script: ping check, drive mapping, kopieert exe naar import-test op server + SMB share aanmaken

### Phase 3: Stable Release
**Goal**: Rik can promote the dev version to stable, and the previous stable is archived so a bad deploy can be recovered from
**Depends on**: Phase 2
**Requirements**: BLD-03, RBK-01
**Success Criteria** (what must be TRUE):
  1. Running the promote command moves the current stable exe to `C:\import\archive\{versie}\` before replacing it with the dev build
  2. After promote, Evy's desktop shortcut opens the newly promoted version without any action on her part
  3. The archive folder contains a dated/versioned copy of every previous stable build
**Plans**: 1 plan

Plans:
- [ ] 03-01-PLAN.md -- Create promote.ps1 (archive + promote + verify) and test end-to-end on server

## Progress

**Execution Order:** Phase 1 -> Phase 2 -> Phase 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 2/2 | Complete | 2026-02-19 |
| 2. Build & Deploy | 2/2 | Complete | 2026-02-19 |
| 3. Stable Release | 0/1 | Planned | - |
