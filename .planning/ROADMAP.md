# Roadmap: BOM Import Tool — Release Management

## Overview

The bom-import-tool.exe gets a proper release structure so Evy always has a working stable version while Rik develops freely. Three phases: first the versioning and server folder layout, then the build/deploy scripts that automate Rik's workflow, then the promote + archive mechanism that gives Evy a protected stable channel.

## Phases

- [ ] **Phase 1: Foundation** - Version the tool and create the stable/dev folder structure on the server
- [ ] **Phase 2: Build & Deploy** - Scripts to build the exe with version embedded and push to dev/
- [ ] **Phase 3: Stable Release** - Promote command that moves dev to stable with archive of old version

## Phase Details

### Phase 1: Foundation
**Goal**: The tool has a version number and the server has the folder structure that separates Evy's stable version from dev builds
**Depends on**: Nothing (first phase)
**Requirements**: VER-01, VER-02, SRV-01, SRV-02, SRV-03
**Success Criteria** (what must be TRUE):
  1. The tool source code has a single version variable (semver) that is the single source of truth
  2. When the exe runs, the title bar shows the version number
  3. The server has `C:\import\bom-import-tool\stable\` and `C:\import\bom-import-tool\dev\` folders
  4. Evy has a desktop shortcut that points to stable\bom-import-tool.exe and does not need to be updated when new versions ship
**Plans**: TBD

Plans:
- [ ] 01-01: Add version variable to tool source and display in GUI title bar
- [ ] 01-02: Create server folder structure (stable/, dev/, archive/) and Evy's desktop shortcut

### Phase 2: Build & Deploy
**Goal**: Rik can build a versioned exe and push it to the dev folder on the server with a single command
**Depends on**: Phase 1
**Requirements**: BLD-01, BLD-02
**Success Criteria** (what must be TRUE):
  1. Running the build script produces an exe with the version from the source variable embedded in the filename or readable from the binary
  2. Running the deploy script copies the exe to `C:\import\bom-import-tool\dev\` after verifying VPN/ping connectivity — and fails cleanly if the server is unreachable
  3. Rik can go from source change to testable exe on the server in one command sequence
**Plans**: TBD

Plans:
- [ ] 02-01: Write build.ps1 that runs PyInstaller and injects version into the exe
- [ ] 02-02: Write deploy.ps1 that ping-checks VMSERVERRUM and copies exe to dev/ via Z: drive

### Phase 3: Stable Release
**Goal**: Rik can promote the dev version to stable, and the previous stable is archived so a bad deploy can be recovered from
**Depends on**: Phase 2
**Requirements**: BLD-03, RBK-01
**Success Criteria** (what must be TRUE):
  1. Running the promote command moves the current stable exe to `archive/{versie}/` before replacing it
  2. After promote, Evy's desktop shortcut opens the newly promoted version without any action on her part
  3. The archive folder contains a dated/versioned copy of every previous stable build
**Plans**: TBD

Plans:
- [ ] 03-01: Write promote.ps1 that archives old stable, copies dev to stable, verifies shortcut still works

## Progress

**Execution Order:** Phase 1 -> Phase 2 -> Phase 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 0/2 | Not started | - |
| 2. Build & Deploy | 0/2 | Not started | - |
| 3. Stable Release | 0/1 | Not started | - |
