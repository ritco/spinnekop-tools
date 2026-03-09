# Roadmap: BOM Import Tool & Locatie Scanner

## Milestones

- ✅ **v1.0 Release Management** - Phases 1-3 (shipped 2026-02-24)
- ✅ **v1.1 Config + Self-update** - Phases 4-6 (shipped 2026-02-26)
- 🚧 **v2.0 Locatie Scanner — Productie** - Phases 7-9 (in progress)

## Phases

<details>
<summary>✅ v1.0 Release Management (Phases 1-3) - SHIPPED 2026-02-24</summary>

- [x] Phase 1: Foundation (2/2 plans) — completed 2026-02-19
- [x] Phase 2: Build & Deploy (2/2 plans) — completed 2026-02-19
- [x] Phase 3: Stable Release (1/1 plan) — completed 2026-02-19

</details>

<details>
<summary>✅ v1.1 Config + Self-update (Phases 4-6) - SHIPPED 2026-02-26</summary>

- [x] Phase 4: Promote v1.2.0 + version.json (1/1 plan) — completed 2026-02-26
- [x] Phase 5: Self-update (2/2 plans) — completed 2026-02-26
- [x] Phase 6: Productiestructuur Config + Update (2/2 plans) — completed 2026-02-26

</details>

### 🚧 v2.0 Locatie Scanner — Productie

**Milestone Goal:** De werkende Locatie Scanner prototype omzetten naar een stabiele productietool die magazijniers zelfstandig kunnen gebruiken — altijd beschikbaar op de server, HTTPS voor camera, en audit trail van wie wat scande.

- [ ] **Phase 7: Server Deployment** - Locatie Scanner draait als Windows Service op VMSERVERRUM
- [ ] **Phase 8: HTTPS + Scanner UX** - Camera werkt op telefoons zonder Chrome flags
- [ ] **Phase 9: Gebruiker-identificatie** - Audit trail van wie welke locatie scande

## Phase Details

### Phase 7: Server Deployment
**Goal**: Locatie Scanner draait permanent op VMSERVERRUM als Windows Service — magazijniers kunnen er altijd bij
**Depends on**: Nothing (prototype werkt al lokaal)
**Requirements**: DEPL-01, DEPL-02, DEPL-03
**Success Criteria** (what must be TRUE):
  1. Locatie Scanner is bereikbaar op http://10.0.1.5:5050 vanuit een telefoon in het magazijn-netwerk
  2. Na een server reboot start de Locatie Scanner automatisch opnieuw zonder handmatige actie
  3. Als het Flask-proces crasht, herstart de service het automatisch
**Plans**: 1 plan

Plans:
- [ ] 07-01-PLAN.md — Deploy Locatie Scanner als Windows Service via NSSM

### Phase 8: HTTPS + Scanner UX
**Goal**: Camera barcode scanner werkt op elke telefoon zonder handmatige Chrome flags — en toetsenbord stoort niet meer
**Depends on**: Phase 7
**Requirements**: CERT-01, CERT-02, UX-01
**Success Criteria** (what must be TRUE):
  1. Magazijnier opent https://10.0.1.5:5050 op zijn telefoon en camera start zonder Chrome flag workaround
  2. Telefoon toont geen certificaatwaarschuwing (of eenmalig accepteren, daarna niet meer)
  3. Wanneer de camera scanner opent, sluit het virtuele toetsenbord automatisch
**Plans**: TBD

Plans:
- [ ] 08-01: TBD

### Phase 9: Gebruiker-identificatie
**Goal**: Elke scan is traceerbaar naar een persoon — magazijniers selecteren wie ze zijn, en een audit log toont de geschiedenis
**Depends on**: Phase 8
**Requirements**: USER-01, USER-02, USER-03
**Success Criteria** (what must be TRUE):
  1. Magazijnier selecteert zijn naam uit een dropdown voordat hij begint met scannen
  2. In de RidderIQ database staat bij elke locatie-registratie wie het deed (CREATOR/USERCHANGED velden)
  3. In de app is een overzichtspagina zichtbaar met wie wat scande en wanneer
**Plans**: TBD

Plans:
- [ ] 09-01: TBD

## Progress

**Execution Order:** Phase 7 → Phase 8 → Phase 9

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 2/2 | Complete | 2026-02-19 |
| 2. Build & Deploy | v1.0 | 2/2 | Complete | 2026-02-19 |
| 3. Stable Release | v1.0 | 1/1 | Complete | 2026-02-19 |
| 4. Promote v1.2.0 | v1.1 | 1/1 | Complete | 2026-02-26 |
| 5. Self-update | v1.1 | 2/2 | Complete | 2026-02-26 |
| 6. Productiestructuur | v1.1 | 2/2 | Complete | 2026-02-26 |
| 7. Server Deployment | v2.0 | 0/1 | Not started | - |
| 8. HTTPS + Scanner UX | v2.0 | 0/1 | Not started | - |
| 9. Gebruiker-identificatie | v2.0 | 0/1 | Not started | - |
