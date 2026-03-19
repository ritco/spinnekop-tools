# Feature Research

**Domain:** Job costing / nacalculatie reporting database — ETO metal manufacturer
**Researched:** 2026-03-19
**Confidence:** MEDIUM — core job costing theory HIGH (well-established domain); Spinnekop-specific data availability MEDIUM (uren-keten confirmed, inkoop-keten TBD); Power BI feature scope MEDIUM (training data, not verified against current docs)

---

## Context for This Research

Spinnekop is a 50-person ETO/CTO metal manufacturer (Ieper + Roeselare). They have no reporting culture yet — this is the first time operational data will be surfaced. The system reads from `Spinnekop Live 2` on SQL Server 2016, writes to `Spinnekop_Reporting` (separate database, same instance), and surfaces data via Power BI Desktop.

**Confirmed data chains (from PROJECT.md):**
- Uren: `R_TIMESHEETLINE → R_PRODUCTIONORDER → R_SALESORDER`
- Inkoop: inkoopfacturen → VO link **TBD** (must be confirmed in next VPN session before building)

**Pilot scope:** Horafrost project — uren per verkooporder.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features that must exist for the reporting system to be credible. Missing any of these = "the report doesn't tell me what I need."

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Uren per verkooporder (werkelijk) | Basis nacalculatie — wat kost een project aan mensenwerk? | LOW | Data confirmed: R_TIMESHEETLINE → R_SALESORDER. Pilot feature. |
| Uren werkelijk vs. begroot per VO | Alleen werkelijk is zinloos zonder referentie — "is dit goed of slecht?" | MEDIUM | Begrote uren zitten vermoedelijk in offerte/calculatie in RidderIQ — moet geverifieerd worden welke tabel |
| Aankoopkosten per verkooporder (werkelijk) | De andere helft van de kostprijs — uren zijn niet genoeg | MEDIUM | Inkoop-keten TBD: inkoopfacturen → VO. Blokkerend als niet gevonden. |
| Aankoop werkelijk vs. begroot per VO | Zelfde reden als bij uren — variantie is het verhaal | MEDIUM | Afhankelijk van begrotingsdata beschikbaarheid in RidderIQ |
| Overzicht alle lopende VO's met status | Operationeel dashboard — "waar staan we?" | LOW | Status zit in R_SALESORDER, join met R_PRODUCTIONORDER voor productie-status |
| Kosten per medewerker per periode | Wie werkt aan wat — capaciteitsplanning en facturatie-check | LOW | Direct uit R_TIMESHEETLINE + medewerker-dimensie |
| Datum filtering (maand / kwartaal / jaar) | Managers willen periodes vergelijken | LOW | Standaard in Power BI via datum-dimensie |
| Inkoop per artikelgroep per VO | Inzicht in materiaalkosten — staal, elektro, onderaanneming | MEDIUM | Afhankelijk van inkoop-keten oplossing |

### Differentiators (Waardevolle Extra's)

Features die niet verwacht worden maar echte beslisvragen beantwoorden voor Francis/Carl.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Marge per VO (uren + aankoop vs. verkoopprijs) | "Verdienen we geld op dit type project?" — stuurt prijszetting | HIGH | Vereist verkoopprijs uit offertes; data-keten moet nog geverifieerd worden |
| Uren per productiestap / bewerkingstype | Welke bewerkingen kosten meer dan gedacht — input voor volgende offerte | MEDIUM | Afhankelijk van hoe bewerkingen geregistreerd staan in productieorders |
| Vergelijking soortgelijke projecten (historisch) | "Sauterelle van 2024 kostte X uren — deze kost Y" — learning per projecttype | HIGH | Vereist categorisatie/tagging van projecten; data loopt terug in de tijd |
| Doorlooptijd per VO (bestelling tot levering) | ETO-specifiek KPI — klantbelofte vs. realiteit | MEDIUM | Datums beschikbaar in R_SALESORDER en R_PRODUCTIONORDER |
| Open aankoopbehoeftes per VO | Wat is nog niet besteld/ontvangen — risico op vertraging | MEDIUM | Koppeling met inkoopbehoeftes module; aparte data-keten |
| Wekelijkse uren-trend per vestiging | Productiviteitsverloop Ieper vs. Roeselare zichtbaar maken | LOW | Eenvoudige aggregatie als uren-keten werkt; vestiging zit op medewerker of order |

### Anti-Features (Bewust Niet Bouwen in v1)

Features die logisch klinken maar verkeerd zijn voor deze schaal en dit stadium.

| Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Real-time dashboard (< 1 uur vertraging) | Vereist streaming of near-real-time ETL — complexiteit x10, waarde marginaal voor een bedrijf dat op dagtotalen werkt | Nachtelijke ETL is voldoende; data is 's ochtends vers. Real-time pas als expliciet gevraagd en onderbouwd. |
| Volledig data warehouse (Kimball-stijl met SCD type 2) | Overkill voor 50 medewerkers en één bron — bouwt technische schuld, geen waarde | Raw/core/report drie-laags is genoeg. Historisering via snapshot_date, niet via SCD. |
| Kostprijsberekening met overhead-allocatie | Methodologisch complex (welke overhead-sleutel?), uitkomst betwistbaar, accounting is niet het doel | Uren + directe aankopen rapporteren. Overhead-discussie horen bij boekhouder/accountant, niet bij dit systeem. |
| Forecasting / voorspellende analyses | Geen historische baseline aanwezig voor zinvolle voorspellingen; data is nog niet schoon genoeg | Pas bouwen na 12+ maanden goed gevulde rapportage-DB. Differentiator voor v3+ |
| Self-service rapportage (gebruikers bouwen eigen rapporten) | Spinnekop heeft geen BI-cultuur; vereist training en governance; levert chaos op | Vaste rapporten bouwen die antwoord geven op de bekende vragen. Power BI Desktop voor Rik, niet voor eindgebruikers. |
| Alerting / e-mail notificaties bij overschrijdingen | Infrastructuur (SMTP, scheduling, Power BI Pro) vereist, waarde onzeker totdat basislijn bekend is | Eerst basislijn bepalen. "Alarm bij 20% overschrijding" heeft geen referentie als er nog nooit gemeten is. |
| Multi-valuta / multi-entiteit consolidatie | Spinnekop is één bedrijf, één valuta (EUR) | Niet relevant. Weg ermee. |
| Mobiele app of mobiel dashboard | Operationele beslissingen over nacalculatie worden op kantoor genomen | Power BI op desktop/laptop volstaat voor pilot. Mobiel pas als expliciet gevraagd. |

---

## Feature Dependencies

```
[Uren per VO (werkelijk)]
    └──requires──> [ETL: R_TIMESHEETLINE snapshot]
                       └──requires──> [Reporting DB aangemaakt + raw schema]

[Uren werkelijk vs. begroot]
    └──requires──> [Uren per VO (werkelijk)]
    └──requires──> [Begrote uren beschikbaar in RidderIQ — MOET GEVERIFIEERD]

[Aankoopkosten per VO (werkelijk)]
    └──requires──> [ETL: inkoopfacturen snapshot]
    └──requires──> [FK: inkoopfactuur → VO gevonden — MOET GEVERIFIEERD]

[Marge per VO]
    └──requires──> [Aankoopkosten per VO]
    └──requires──> [Uren per VO]
    └──requires──> [Verkoopprijs beschikbaar in RidderIQ — MOET GEVERIFIEERD]

[Power BI rapport]
    └──requires──> [Report-laag views aangemaakt]
                       └──requires──> [Core-laag feiten + dimensies]
                                          └──requires──> [Raw-laag snapshots]
```

### Dependency Notes

- **Uren-keten is bevestigd** — dit is de veilige start. Pilot Horafrost kan gebouwd worden zodra ETL draait.
- **Inkoop-keten is NIET bevestigd** — blokkerend voor de helft van de nacalculatie. Prioriteit: in eerste VPN-sessie SQL-verkenning uitvoeren.
- **Begrote uren/kosten zijn NIET bevestigd** — zonder begroot heeft "werkelijk" geen context. Offertedata in RidderIQ moet geverifieerd worden voor "vs. begroot"-rapporten.
- **Verkoopprijs beschikbaar?** — voor marge-berekening. Waarschijnlijk in R_SALESORDER, maar veldnaam en betrouwbaarheid onbekend.

---

## MVP Definition

### Launch With (v1 — Pilot Horafrost)

Minimum om iets zinvols te tonen aan Francis/Carl. Valideert het concept.

- [ ] Reporting DB aangemaakt met raw/core/report schemas
- [ ] Nachtelijke ETL: R_TIMESHEETLINE, R_PRODUCTIONORDER, R_SALESORDER, medewerkers
- [ ] Core-laag: feit_uren (uren per productieorder per medewerker per dag), dim_salesorder, dim_medewerker, dim_datum
- [ ] Report-view: uren per VO (werkelijk, gefilterd op Horafrost)
- [ ] Power BI rapport: uren per VO — tabel + eenvoudige bar chart
- [ ] Datum-filter op het rapport (van/tot)

**Bewuste uitsluiting uit v1:** aankoop, begroot vs. werkelijk, marge. Te veel onbevestigde data-ketens.

### Add After Validation (v1.x)

Zodra pilot positief is en inkoop-keten bevestigd is.

- [ ] ETL uitbreiden met inkoopfacturen — trigger: FK gevonden in SQL-verkenning
- [ ] Aankoopkosten per VO in core-laag
- [ ] Nacalculatie-view: uren + aankoop per VO naast elkaar
- [ ] Begrotingsdata toevoegen (als beschikbaar) — trigger: tabel + velden bevestigd
- [ ] Uitbreiding Power BI: uren + aankoop per VO, alle VO's overzicht

### Future Consideration (v2+)

Pas relevant na 3-6 maanden data.

- [ ] Marge per VO — trigger: verkoopprijs betrouwbaar en volledig in RidderIQ
- [ ] Vergelijking soortgelijke projecten — trigger: 12+ maanden historiek
- [ ] Doorlooptijd KPI — trigger: datumregistratie consistent gebleken
- [ ] Uren per productiestap — trigger: bewerkingstypes consistent geregistreerd

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Uren per VO (werkelijk) | HIGH | LOW | P1 |
| ETL-infrastructuur (raw + core + report) | HIGH | MEDIUM | P1 |
| Power BI pilot-rapport (Horafrost) | HIGH | LOW | P1 |
| Uren werkelijk vs. begroot | HIGH | MEDIUM | P2 |
| Aankoopkosten per VO | HIGH | MEDIUM | P2 — wacht op FK-verificatie |
| Overzicht alle VO's met status | MEDIUM | LOW | P2 |
| Kosten per medewerker per periode | MEDIUM | LOW | P2 |
| Marge per VO | HIGH | HIGH | P3 — wacht op stabiele basis |
| Doorlooptijd KPI | MEDIUM | MEDIUM | P3 |
| Historische vergelijking | HIGH | HIGH | P3 — wacht op historiek |

**Priority key:**
- P1: Bouwen in eerste fase (pilot Horafrost)
- P2: Toevoegen zodra pilot succesvol is en data-ketens bevestigd
- P3: Defer — afhankelijk van datakwaliteit en vraag vanuit management

---

## ETO-Specifieke Overwegingen

Deze kenmerken van ETO-productie beïnvloeden welke features zinvol zijn (MEDIUM confidence — gebaseerd op meerdere ETO-bronnen):

**Standard costing werkt niet voor ETO.** Elke order is uniek — variantie naar een standaard is betekenisloos. Nacalculatie moet altijd projectgebonden zijn (per VO), niet per artikelgroep of standaard-kostprijs.

**"Cost to go" is waardevoller dan "cost to date" voor lopende projecten.** Voor projecten die weken of maanden lopen, wil Francis weten "wat kost dit project nog" niet alleen "wat heeft het al gekost." Dit is echter een complexe berekening die pas zinvol is als de basisrapportage stabiel staat — bewust P3.

**Inkoop en uren hebben verschillende eigenaren.** Uren worden geregistreerd op de werkvloer (shop floor), aankopen door de inkoper. Dit betekent dat datakwaliteit per keten apart bewaakt moet worden in de ETL.

**Kleine fout in tijdregistratie = grote fout in nacalculatie.** Als medewerkers uren niet of fout registreren op productiebons, kloppen de rapporten niet. De ETL moet missing-data signaleren, niet stilzwijgend weglaten.

---

## Data Risks (beïnvloeden feature-keuzes)

| Risico | Impact | Mitigatie |
|--------|--------|-----------|
| Inkoop-FK naar VO niet gevonden | Aankoopkosten per VO niet mogelijk | SQL-verkenning als eerste actie; tijdelijke workaround via artikelgroep? |
| Begrote uren niet in RidderIQ opgeslagen | "Werkelijk vs. begroot" niet mogelijk | Check offerte-module; als niet beschikbaar, alleen werkelijk tonen |
| Medewerkers registreren uren niet op VO-niveau | Uren niet toewijsbaar aan project | Datakwaliteitscheck als onderdeel van ETL-output |
| Historische data onvolledig (voor 2025) | Trendanalyse pas mogelijk na 2026-start | Enkel vooruitkijken; geen historische vergelijking in v1 |
| Verkoopprijs niet betrouwbaar in R_SALESORDER | Marge-berekening onmogelijk of misleidend | Marge pas bouwen na expliciete verificatie van prijsveld |

---

## Sources

- Project context: `.planning/PROJECT.md` — bevestigde data-ketens, pilot scope, architectuur-beslissingen (HIGH confidence)
- ETO cost challenges: [Overcome Cost Issues in ETO Manufacturing — DSW](https://dswius.com/overcoming-cost-challenges-in-engineer-to-order-manufacturing/) (MEDIUM confidence — single source, WebSearch)
- Job costing fundamentals: [Job Costing Defined — NetSuite](https://www.netsuite.com/portal/resource/articles/accounting/job-costing.shtml) (MEDIUM confidence — authoritative source for concepts)
- ETO ERP requirements: [How ERPs Help ETO Manufacturers — Genius ERP](https://www.geniuserp.com/resources/blog/how-erps-help-eto-manufacturers/) (LOW confidence — vendor source, WebSearch only)
- Nacalculatie Belgian context: [Nacalculatie in Projectmanagement — one-two.com](https://www.one-two.com/nl/artikels/klamme-handjes-van-nacalculatie) (MEDIUM confidence — practitioner source)
- Variance analysis: [Understanding job cost variance — Bonsai](https://www.hellobonsai.com/blog/job-cost-variance) (MEDIUM confidence — multiple sources corroborate)
- Business Central ETO patterns: [How ETO Manufacturers Can Get More from Business Central](https://erpsoftwareblog.com/2026/02/how-eto-manufacturers-can-get-more-from-business-central/) (LOW confidence — WebSearch only)

---

*Feature research for: RidderIQ Reporting Database / Nacalculatie — Spinnekop BV*
*Researched: 2026-03-19*
