# Roadmap: BOM Import Tool & Locatie Scanner

## Milestones

- ✅ **v1.0 Release Management** - Phases 1-3 (shipped 2026-02-24)
- ✅ **v1.1 Config + Self-update** - Phases 4-6 (shipped 2026-02-26)
- 🚧 **v2.0 Locatie Scanner — Productie** - Phases 7-9 (in progress)
- 🚧 **v3.0 ePlan Import Tool** - Phases 11-13 (in progress)

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

### 🚧 v3.0 ePlan Import Tool

**Milestone Goal:** Een tweede import tool naast de BOM Import Tool — leest ePlan stuklijst-exports, koppelt componenten aan bestaande RidderIQ-artikelen of maakt nieuwe aan, en importeert stuklijsten klaar voor gebruik in productiebons.

- [ ] **Phase 11: Core Converter** - Headless engine: parse ePlan Excel, match artikelen, genereer output bestanden
- [ ] **Phase 12: GUI** - CustomTkinter interface maakt de converter bruikbaar voor Evy
- [ ] **Phase 13: Build & Deploy** - Standalone exe via PyInstaller, GitHub release pipeline, installatiescripts

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
- [x] 07-01-PLAN.md — Deploy Locatie Scanner als Windows Service via NSSM ✅

### Phase 8: HTTPS + Scanner UX
**Goal**: Camera barcode scanner werkt op elke telefoon zonder handmatige Chrome flags — en toetsenbord stoort niet meer
**Depends on**: Phase 7
**Requirements**: CERT-01, CERT-02, UX-01
**Success Criteria** (what must be TRUE):
  1. Magazijnier opent https://10.0.1.5:5050 op zijn telefoon en camera start zonder Chrome flag workaround
  2. Telefoon toont geen certificaatwaarschuwing (of eenmalig accepteren, daarna niet meer)
  3. Wanneer de camera scanner opent, sluit het virtuele toetsenbord automatisch
**Plans**: 1 plan

Plans:
- [x] 08-01-PLAN.md — HTTPS met self-signed cert + keyboard UX fix ✅

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

### Phase 10: BOM Import Tool — SQL Server Audit Log ✅

**Goal:** Gecentraliseerd logboek op SQL Server + GitHub Release pipeline
**Completed:** 2026-03-18
**Plans:** 1 plan

Plans:
- [x] 10-01-PLAN.md — Audit log (SpinnekopTools.BOM_IMPORT_LOG) + GitHub release pipeline + DPAPI encryptie ✅

### Phase 11: Core Converter
**Goal**: De ePlan Excel-verwerking werkt volledig headless — inlezen, aggregeren, matchen tegen RidderIQ, nieuwe artikelen genereren, en output bestanden klaarzetten voor import
**Depends on**: Nothing (nieuwe codebase, deelt alleen app_config.py)
**Requirements**: PARSE-01, PARSE-02, PARSE-03, MATCH-01, MATCH-02, MATCH-03, MATCH-04, ART-01, ART-02, BOM-01, BOM-02, BOM-03
**Success Criteria** (what must be TRUE):
  1. Een ePlan Excel met 10 componenten (waarvan 2 duplicaten, 1 rij zonder Bestelnummer) levert exact 9 unieke regels op met geaggregeerde hoeveelheden en 1 waarschuwing
  2. Voor elk Bestelnummer vindt de converter het juiste RidderIQ-artikel via OMSCHRIJVING LIKE, of geeft een blokkerende fout bij meerdere matches
  3. Artikelen die niet bestaan in RidderIQ verschijnen in `01-nieuwe-artikelen-eplan.csv` met correct 26xxx code, artikelgroep PK 673, REGISTRATIONPATH=5 en INVENTORYKIND=4
  4. De converter schrijft `02-stuklijst-header.csv` met projectnaam als stuklijstcode en `03-stuklijstregels.sql` met INSERT statements voor alle geaggregeerde regels
  5. Als de stuklijstcode al bestaat in R_ASSEMBLY, stopt de converter met een blokkerende fout voordat er bestanden worden geschreven
**Plans**: TBD

Plans:
- [ ] 11-01: TBD (run /gsd:plan-phase 11 to break down)

### Phase 12: GUI
**Goal**: Evy kan de ePlan Import Tool openen, een bestand kiezen, de analyse bekijken, en de outputbestanden genereren — zonder commandoregel of technische kennis
**Depends on**: Phase 11
**Requirements**: GUI-01, GUI-02, GUI-03, GUI-04, HIST-01, HIST-02
**Success Criteria** (what must be TRUE):
  1. Evy opent de tool, klikt "Bestand kiezen", selecteert een ePlan Excel en ziet direct een validatiesamenvatting met aantallen gevonden artikelen, nieuwe artikelen, overgeslagen rijen en eventuele fouten
  2. Evy kiest Speeltuin of Live omgeving via een duidelijke selector voordat ze importeert
  3. Bij blokkerende fouten is de "Genereer output" knop uitgeschakeld — Evy kan pas verder als alle fouten opgelost zijn
  4. Na goedkeuring toont de tool stapsgewijze importinstructies en bevestigt welke bestanden zijn aangemaakt
  5. Recente imports zijn zichtbaar in de StartFrame na een succesvolle import
**Plans**: TBD

Plans:
- [ ] 12-01: TBD (run /gsd:plan-phase 12 to break down)

### Phase 13: Build & Deploy
**Goal**: eplan-import-tool.exe is beschikbaar als standalone executable, volgt de GitHub release pipeline en kan worden geinstalleerd via scripts
**Depends on**: Phase 12
**Requirements**: BUILD-01, BUILD-02, BUILD-03
**Success Criteria** (what must be TRUE):
  1. `eplan-import-tool.exe` start op een machine zonder Python installatie en toont de GUI zonder foutmeldingen
  2. Bij een nieuwe release controleert de tool bij opstart of er een update beschikbaar is en biedt aan te updaten via dezelfde CTk dialog als de BOM Import Tool
  3. `install-live.ps1` en `install-test.ps1` installeren de exe op de correcte serverlocatie met een ping-check voordat ze kopiëren
**Plans**: TBD

Plans:
- [ ] 13-01: TBD (run /gsd:plan-phase 13 to break down)

## Progress

**Execution Order:** Phase 7 → Phase 8 → Phase 9 | Phase 11 → Phase 12 → Phase 13

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 2/2 | Complete | 2026-02-19 |
| 2. Build & Deploy | v1.0 | 2/2 | Complete | 2026-02-19 |
| 3. Stable Release | v1.0 | 1/1 | Complete | 2026-02-19 |
| 4. Promote v1.2.0 | v1.1 | 1/1 | Complete | 2026-02-26 |
| 5. Self-update | v1.1 | 2/2 | Complete | 2026-02-26 |
| 6. Productiestructuur | v1.1 | 2/2 | Complete | 2026-02-26 |
| 7. Server Deployment | v2.0 | 1/1 | Complete | 2026-03-09 |
| 8. HTTPS + Scanner UX | v2.0 | 1/1 | Complete | 2026-03-11 |
| 9. Gebruiker-identificatie | v2.0 | 0/1 | Not started | - |
| 11. Core Converter | v3.0 | 0/? | Not started | - |
| 12. GUI | v3.0 | 0/? | Not started | - |
| 13. Build & Deploy | v3.0 | 0/? | Not started | - |
