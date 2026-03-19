# Roadmap: BOM Import Tool & Locatie Scanner

## Milestones

- ✅ **v1.0 Release Management** - Phases 1-3 (shipped 2026-02-24)
- ✅ **v1.1 Config + Self-update** - Phases 4-6 (shipped 2026-02-26)
- 🚧 **v2.0 Locatie Scanner — Productie** - Phases 7-9 (in progress)
- 🚧 **v3.0 ePlan Import Tool** - Phases 11-13 (in progress)
- 📋 **v4.0 Rapporterings-DB** - Phases 14-18 (planned)

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

- [x] **Phase 11: Core Converter** - Headless engine: parse ePlan Excel, match artikelen, genereer output bestanden
 (completed 2026-03-19)
- [x] **Phase 12: GUI** - CustomTkinter interface maakt de converter bruikbaar voor Florian/Toby (completed 2026-03-19)
- [ ] **Phase 13: Build & Deploy** - Standalone exe via PyInstaller, GitHub release pipeline, installatiescripts

### 📋 v4.0 Rapporterings-DB

**Milestone Goal:** Een aparte rapporterings-database (`Spinnekop_Reporting`) gevuld via nachtelijke Python ETL, met drie lagen (raw/core/report) als fundament voor nacalculatie en operationele rapportering. Francis kan per VO zien wat het aan uren en aankoop heeft gekost — zonder in het ERP te moeten duiken.

- [ ] **Phase 14: DB + Infrastructuur** - `Spinnekop_Reporting` aangemaakt met raw/core/report schemas, kalender-tabel en ETL-controle tabel
- [ ] **Phase 15: ETL** - Nachtelijke Python extract draait via Task Scheduler, append-only naar raw, idempotent en VPN-bestendig
- [ ] **Phase 16: Core-laag** - Star schema gevuld: drie dimensies (VO, medewerker, artikel) + fact_uren
- [ ] **Phase 17: Report + Power BI** - Report-views voor nacalculatie live, Power BI pilot rapport voor Horafrost klaar
- [ ] **Phase 18: Inkoop-keten** - FK inkoopfactuur → VO bevestigd, fact_aankoop gevuld, volledige nacalculatie-view beschikbaar

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
  4. De converter schrijft `02-stuklijst-header.csv` met projectnaam als stuklijstcode en `03-stuklijstregels.csv` voor R_ASSEMBLYDETAILITEM import (zelfde kolomstructuur als BOM tool)
  5. Als de stuklijstcode al bestaat in R_ASSEMBLY, stopt de converter met een blokkerende fout voordat er bestanden worden geschreven
**Plans**: 2 plans

Plans:
- [ ] 11-01-PLAN.md — Datamodel, Excel-parser en SQL-matchinglogica (PARSE + MATCH + ART)
- [ ] 11-02-PLAN.md — Output-generatie: drie CSV-bestanden + end-to-end integratietest (BOM)

### Phase 12: GUI
**Goal**: Florian/Toby kan de ePlan Import Tool openen, een bestand kiezen, de analyse bekijken, en de outputbestanden genereren — zonder commandoregel of technische kennis
**Depends on**: Phase 11
**Requirements**: GUI-01, GUI-02, GUI-03, GUI-04, HIST-01, HIST-02
**Success Criteria** (what must be TRUE):
  1. Florian/Toby opent de tool, klikt "Bestand kiezen", selecteert een ePlan Excel en ziet direct een validatiesamenvatting met aantallen gevonden artikelen, nieuwe artikelen, overgeslagen rijen en eventuele fouten
  2. Florian/Toby kiest Speeltuin of Live omgeving via een duidelijke selector voordat ze importeert
  3. Bij blokkerende fouten is de "Genereer output" knop uitgeschakeld — Florian/Toby kan pas verder als alle fouten opgelost zijn
  4. Na goedkeuring toont de tool stapsgewijze importinstructies en bevestigt welke bestanden zijn aangemaakt
  5. Recente imports zijn zichtbaar in de StartFrame na een succesvolle import
**Plans**: 2 plans

Plans:
- [x] 12-01-PLAN.md — eplan_gui.py: StartFrame + AnalysisFrame + EplanApp (twee-staps dry_run flow, history logging)
- [x] 12-02-PLAN.md — eplan_main.py: entry point met versie, update-check thread, visuele checkpoint ✅

### Phase 13: Build & Deploy
**Goal**: eplan-import-tool.exe is beschikbaar als standalone executable, volgt de GitHub release pipeline en kan worden geinstalleerd via scripts
**Depends on**: Phase 12
**Requirements**: BUILD-01, BUILD-02, BUILD-03
**Success Criteria** (what must be TRUE):
  1. `eplan-import-tool.exe` start op een machine zonder Python installatie en toont de GUI zonder foutmeldingen
  2. Bij een nieuwe release controleert de tool bij opstart of er een update beschikbaar is en biedt aan te updaten via dezelfde CTk dialog als de BOM Import Tool
  3. `install-live.ps1` en `install-test.ps1` installeren de exe op de correcte serverlocatie met een ping-check voordat ze kopiëren
**Plans**: 2 plans

Plans:
- [ ] 13-01-PLAN.md — PyInstaller spec + install scripts + workflow doc update (BUILD-02, BUILD-03)
- [ ] 13-02-PLAN.md — Build exe + GitHub release eplan-v1.0.0 + checkpoint GUI verificatie (BUILD-01, BUILD-02)

### Phase 14: DB + Infrastructuur
**Goal**: `Spinnekop_Reporting` bestaat op de SQL Server met de drie schemas, een gevulde kalender-tabel en een werkende ETL-controle tabel — het fundament waarop alle volgende lagen bouwen
**Depends on**: Nothing (nieuwe database op bestaande instantie)
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04
**Success Criteria** (what must be TRUE):
  1. Database `Spinnekop_Reporting` is bereikbaar via pyodbc op `10.0.1.5\RIDDERIQ` en bevat de schemas `raw`, `core` en `report`
  2. `core.dim_datum` bevat rijen voor 2020 t/m 2030 met week, maand, kwartaal en jaar kolommen — een SELECT op een willekeurige datum geeft de juiste waarden terug
  3. `raw.etl_log` bestaat en accepteert een INSERT met run_date, tabel, rows_extracted, rows_loaded, status en error_msg
  4. Alle DDL-scripts kunnen twee keer achter elkaar worden uitgevoerd zonder fouten (idempotent)
**Plans**: TBD

Plans:
- [ ] 14-01: TBD (run /gsd:plan-phase 14 to break down)

### Phase 15: ETL
**Goal**: Een Python-script extracteert nachtelijk de relevante RidderIQ-tabellen naar `raw.*`, logt elke run, is bestand tegen VPN-drops en draait automatisch via Task Scheduler
**Depends on**: Phase 14
**Requirements**: ETL-01, ETL-02, ETL-03, ETL-04, ETL-05, ETL-06, ETL-07
**Success Criteria** (what must be TRUE):
  1. Na een nachtelijke run bevatten `raw.R_TIMESHEETLINE`, `raw.R_PRODUCTIONORDER`, `raw.R_SALESORDER`, `raw.R_ITEM` en `raw.R_EMPLOYEE` rijen met de `snapshot_date` van gisteren
  2. Als het script tweemaal op dezelfde dag wordt uitgevoerd, bevat elke raw-tabel precies één set rijen voor die datum (geen duplicaten)
  3. `raw.etl_log` toont een geslaagde run met correcte rowcounts; bij een VPN-fout staat er een foutmelding in plaats van een lege rij
  4. `raw.schema_snapshot` bevat kolomnamen van de brondatabases zodat ERP-updates detecteerbaar zijn
  5. Task Scheduler voert het script uit om 02:00 en slaat de run over als `10.0.1.5` niet pingbaar is
**Plans**: TBD

Plans:
- [ ] 15-01: TBD (run /gsd:plan-phase 15 to break down)

### Phase 16: Core-laag
**Goal**: Het star schema in `core` is gevuld — drie dimensies en `fact_uren` bevatten actuele data na een ETL-run, klaar om door rapportage-views te worden bevraagd
**Depends on**: Phase 15
**Requirements**: CORE-01, CORE-02, CORE-03, CORE-04, CORE-05
**Success Criteria** (what must be TRUE):
  1. `core.dim_verkooporder`, `core.dim_medewerker` en `core.dim_artikel` bevatten rijen die overeenkomen met de huidige stand in `Spinnekop Live 2`
  2. `core.fact_uren` bevat één rij per urenregel met FK's naar alle drie dimensies en naar `dim_datum` — een JOIN op een willekeurig VO-nummer geeft de bijbehorende uren terug
  3. De stored procs kunnen tweemaal achter elkaar worden aangeroepen zonder dubbele rijen of fouten (idempotent via MERGE of TRUNCATE+INSERT)
**Plans**: TBD

Plans:
- [ ] 16-01: TBD (run /gsd:plan-phase 16 to break down)

### Phase 17: Report + Power BI
**Goal**: Report-views zijn bevraagbaar via Power BI Import mode, en het pilot rapport voor Horafrost toont uren per VO met datum- en medewerkersfilter — klaar om te delen met Francis en Carl
**Depends on**: Phase 16
**Requirements**: REPORT-01, REPORT-02, REPORT-03, REPORT-04
**Success Criteria** (what must be TRUE):
  1. `report.v_uren_per_vo` geeft totaal uren per VO terug, filterbaar op periode en medewerker
  2. `report.v_nacalculatie_uren` geeft per urenregel het VO-nummer, de datum, de medewerker en het productiebonnummer terug
  3. Het Power BI `.pbix` rapport opent, verbindt via Import mode met `Spinnekop_Reporting`, en toont uren per VO voor Horafrost na een handmatige refresh
  4. Het rapport bevat een "data freshness" kaart die de datum van de laatste ETL-run toont zodat stale data direct zichtbaar is
**Plans**: TBD

Plans:
- [ ] 17-01: TBD (run /gsd:plan-phase 17 to break down)

### Phase 18: Inkoop-keten
**Goal**: De FK-keten inkoopfactuur → verkooporder is bevestigd en gedocumenteerd, het ETL is uitgebreid met inkooptabellen, en `fact_aankoop` maakt een volledige nacalculatie (uren + aankoop) per VO mogelijk
**Depends on**: Phase 17
**Requirements**: INKOOP-01, INKOOP-02, INKOOP-03, INKOOP-04, INKOOP-05
**Success Criteria** (what must be TRUE):
  1. De FK-keten `inkoopfactuur → R_SALESORDER` is gedocumenteerd in `20-analyse/` met tabelnames, kolomnamen en join-paden — verifieerbaar via een SQL-query die inkoopregels koppelt aan een VO-nummer
  2. `raw.*` bevat dagelijkse snapshots van de inkooptabellen na de nachtelijke ETL
  3. `core.dim_leverancier` en `core.fact_aankoop` bevatten actuele data na een ETL-run; een JOIN op een VO-nummer geeft zowel uren als aankoopkosten terug
  4. `report.v_nacalculatie_volledig` geeft per VO de totale uren en totale aankoopkosten naast elkaar — Francis kan op dit rapport besluiten nemen over projectrendabiliteit
**Plans**: TBD

Plans:
- [ ] 18-01: TBD (run /gsd:plan-phase 18 to break down)

## Progress

**Execution Order:** Phase 7 → Phase 8 → Phase 9 | Phase 11 → Phase 12 → Phase 13 | Phase 14 → Phase 15 → Phase 16 → Phase 17 → Phase 18

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
| 11. Core Converter | v3.0 | 2/2 | Complete | 2026-03-19 |
| 12. GUI | v3.0 | 2/2 | Complete | 2026-03-19 |
| 13. Build & Deploy | v3.0 | 0/2 | Not started | - |
| 14. DB + Infrastructuur | v4.0 | 0/? | Not started | - |
| 15. ETL | v4.0 | 0/? | Not started | - |
| 16. Core-laag | v4.0 | 0/? | Not started | - |
| 17. Report + Power BI | v4.0 | 0/? | Not started | - |
| 18. Inkoop-keten | v4.0 | 0/? | Not started | - |
