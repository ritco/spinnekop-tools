# Spinnekop - Claude Code Project

Dit is een consultancy-project voor **Spinnekop**, een metaalverwerkend bedrijf met vestigingen in Ieper en Roeselare.

## Projecttype

**Obsidian vault** voor lean consultancy en procesverbetering.

## Wat is dit project?

Een externe consultant helpt Spinnekop met:
- Lean implementatie en continue verbetering
- Magazijn- en logistieke optimalisatie
- Procesverbetering en organisatie
- Efficienter gebruik van RidderIQ (ERP) en Windchill (PLM)

## Bedrijfscontext

- **Productiemodel**: Engineer-to-Order (ETO) en Configure-to-Order (CTO)
- **ERP-systeem**: RidderIQ
- **PLM**: Windchill 13.0.1.3 via Innoptus
- **CAD**: SolidWorks
- **Twee vestigingen**: Ieper en Roeselare

## Projectvisie — De Rode Draad

> **"Van smidse naar productiebedrijf"** — de transformatie van een ambachtelijke werkplaats
> naar een professioneel productiebedrijf dat kwaliteit levert, afspraken nakomt,
> en kan groeien zonder evenredig meer overhead.

Het volledige visiedocument staat in `PROJECT-VISIE.md`. **Raadpleeg dit bij elke taak** —
het is de kapstok: past deze actie in het verhaal? Brengt het ons dichter bij het doel?

De reis in vier lagen: **Fundament → Integratie → Automatisering → Intelligentie**.
We zitten nu in de overgang van Laag 1 (magazijn, artikelbeheer) naar Laag 2 (BOM import, PLM-ERP).

---

## Werkwijze — Voice-first Backlog

De consultant werkt met **spraak-naar-tekst** (Win+H in Windows 11) via Claude Code in VSCode. Dit is de primaire manier van communicatie.

### Hoe het werkt

1. Gebruiker drukt **Win+H** en spreekt tegen de laptop
2. Windows zet spraak om naar tekst in het Claude Code inputveld
3. Claude verwerkt de update en past `todo.md` aan

### Wat Claude doet bij een update

- Vind het juiste item in de backlog
- Vink af, voeg toe, of werk bij
- Pas statustabel, voortgangsbalken en blokkades aan
- Herbereken "Eerstvolgende acties" als er iets verschuift
- Update het Mermaid diagram als een traject van status verandert

### Backlog = todo.md

De centrale backlog leeft in `todo.md` in de project-root. Structuur:
- **Trajectoverzicht**: Mermaid diagram met afhankelijkheden en kleurcodes
- **Statustabel**: voortgang per traject met blokkades
- **Blokkades**: wie/wat houdt dingen tegen
- **Eerstvolgende acties**: top 5 zonder blokkades
- **Trajecten 1-7**: gedetailleerde items per werkstroom
- **Parkeerplaats**: items zonder urgentie
- **Afgerond**: historie in inklapbare callout

Zie skill `backlog` voor volledige details over bijwerken.

---

## WAT Framework - Workflows, Agents, Tools

Dit project werkt volgens het WAT-framework: laat AI doen waar het goed in is (redeneren, coordineren) en laat code doen waar het goed in is (consistent uitvoeren).

### Laag 1: Workflows (De Draaiboeken)

Markdown SOPs in `workflows/`. Elk workflow beschrijft:
- Doel en benodigde input
- Welke tools worden aangeroepen
- Verwachte output
- Wat te doen als het misgaat

Geschreven als onboarding-document voor een scherpe nieuwe medewerker.

### Laag 2: Agent (De Coordinator)

Dat ben jij. Jouw doel is intelligente orkestratie:
- Lees het juiste workflow, voer tools in de goede volgorde uit
- Handel fouten kalm af en stel vragen bij onduidelijkheid
- Jij bent de brug tussen intentie en actie - zonder zelf de actie te zijn

**Voorbeeld:** Data nodig van een systeem? Open het relevante workflow, bepaal wat nodig is, en roep het juiste script aan.

### Laag 3: Tools (De Spierkracht)

Python- en PowerShell-scripts in `scripts/` die het echte werk doen:
- API-calls, datatransformaties, bestandsoperaties
- Credentials en API keys leven in `.env`
- Voorspelbaar, testbaar, performant

### Waarom dit werkt

AI-nauwkeurigheid daalt snel over sequentiele stappen. Bij 90% per stap zit je na vijf stappen op 59%. Door uitvoering aan deterministische scripts over te laten, blijf je in de baan waar je het meest toevoegt: denken, beslissen, coordineren.

---

## Operationeel Protocol

### 1. Check bestaande tools voor je nieuwe maakt

Scan altijd eerst `scripts/` en `workflows/`. Bouw alleen iets nieuws als er echt niets past.

### 2. Behandel fouten als input

Als iets breekt:
1. Lees de volledige foutmelding en stack trace
2. Patch het script en hertest
3. **Als een tool betaalde API-calls of credits verbruikt**: bevestig met de gebruiker voor je opnieuw probeert
4. Leg wat je leert vast in het betreffende workflow

### 3. Onderhoud levende workflows

Workflows zijn niet statisch - ze worden scherper over tijd. Wanneer je betere aanpakken ontdekt, nieuwe beperkingen tegenkomt, of terugkerende wrijving opmerkt: werk het document bij.

**Maak of overschrijf nooit workflows zonder te checken met de gebruiker**, tenzij je daar expliciet toestemming voor hebt.

### 4. De Verbetercyclus

Elke fout voedt terug in een sterker systeem:
1. Bepaal wat misging
2. Repareer de tool
3. Bevestig dat de reparatie werkt
4. Verwerk de les in het workflow
5. Ga verder met een robuustere opzet

### 5. Tools — release pipeline na elke code-wijziging

Bij **elke wijziging** aan toolcode (`eplan_converter.py`, `eplan_gui.py`, `eplan_main.py`, `bom_converter.py`, `gui.py`, `main.py`, etc.) moet altijd een nieuwe release aangemaakt worden:
1. Versienummer verhogen in het entry point (`__version__ = 'X.Y.Z'`) — patch (+0.0.1) voor fixes, minor (+0.1.0) voor nieuwe functionaliteit
2. Exe bouwen: `python -m PyInstaller --clean <tool>.spec` vanuit `scripts/`
3. GitHub release aanmaken: `gh release create <prefix>-vX.Y.Z "scripts/dist/<tool>.exe" --repo ritco/spinnekop-tools`
   - ePlan Import Tool: prefix `eplan-`
   - BOM Import Tool: prefix `bom-`
- **Niet achteraf** — release aanmaken terwijl je bouwt, niet als de gebruiker het mist
- **Reden**: geïnstalleerde tools controleren bij opstart op nieuwe GitHub releases. Zonder nieuwe release ziet de gebruiker nooit dat er iets veranderd is.

### 6. BOM Import Tool — documentatie bijhouden

Bij **elke wijziging** aan de BOM Import Tool (`scripts/bom_converter.py`, `sql_validator.py`, `gui.py`, etc.) moet de bijbehorende documentatie onmiddellijk mee bijgewerkt worden:
- **Memory**: `ridderiq-import.md` — technische details, FK-relaties, SQL-kennis, veldwaarden
- **Memory**: `build-deploy.md` — build/deploy procedures, entry points, bekende valkuilen
- Dit geldt voor: nieuwe features, bugfixes, ontdekte database-structuren, gewijzigde mappings, enz.
- **Niet achteraf** — documenteer terwijl je bouwt, niet als de gebruiker het moet vragen

---

## Mappenstructuur

```
Spinnekop/
├── _inbox/              # Te verwerken items
├── 00-klant/            # Klantdocumenten en achtergrond
│   └── Docs/            # Ontvangen documenten (incl. RidderIQ handleiding)
├── 10-logboek/          # Chronologisch verslag van bezoeken
├── 20-analyse/          # Huidige situatie en pijnpunten (geen todo's!)
│   └── processen/       # Deelprocessen (zie procesflows.md voor overzicht)
├── 30-aanbevelingen/    # Verbetervoorstellen
├── 40-implementatie/    # Uitvoering en resultaten
├── Meetings/            # Meeting notes
├── templates/           # Herbruikbare templates
├── scripts/             # Tools: Python/PowerShell scripts (WAT Laag 3)
│   ├── build/           # Build artifacts
│   └── dist/            # Gecompileerde executables
├── workflows/           # SOPs: Markdown draaiboeken (WAT Laag 1)
├── .tmp/                # Scratch space (tussenbestanden, wegwerpbaar)
├── todo.md              # Centrale backlog met trajecten, status en blokkades
└── .claude/skills/      # Domeinkennis skills
```

### Bestandsregels

- **Deliverables** gaan naar cloud services (SharePoint, etc.) waar de gebruiker ze kan bereiken
- **Tussenbestanden** in `.tmp/` - behandel als wegwerpbaar
- **Credentials** uitsluitend in `.env` (nergens anders)
- Lokale bestanden bestaan puur voor verwerking

---

## Skill Routing

Bij ELKE gebruikersvraag wordt de `coordinator` skill automatisch geactiveerd.
Deze bepaalt welke skill(s) nodig zijn en activeert ze. Je hoeft skills niet
handmatig aan te roepen tenzij de gebruiker expliciet `/skill-naam` typt.

## Beschikbare Skills

Skills worden automatisch geactiveerd via de coordinator, of handmatig met `/skill-naam`.

| Skill | Gebruik wanneer |
|-------|-----------------|
| `coordinator` | **Automatisch** — routeert naar de juiste skill(s) |
| `backlog` | Statusupdates, nieuwe taken, blokkades, voortgangsvragen |
| `spinnekop-context` | Vragen over het bedrijf, organisatie, algemene context |
| `documentbeheer` | Waar documenten horen, naamconventies, mappenstructuur |
| `procesbeheer` | Processen documenteren, procesflows, statusbeheer |
| `lean-manufacturing` | 5S, Kaizen, PDCA, visueel management, flow |
| `eto-cto` | Maatwerk productie, werkvoorbereiding, offerte-naar-order |
| `magazijn-logistiek` | Voorraadbeheer, picking, magazijnindeling |
| `ridderiq` | ERP vragen, werkorders, planning, stuklijsten |
| `windchill` | PLM, tekeningen, revisies, documentbeheer, CAD-integratie |

### Skill Details

#### backlog
Centrale backlog in `todo.md`: statusupdates verwerken, taken toevoegen/afvinken, blokkades beheren, voortgangsbalken en Mermaid diagram bijwerken. Verwacht informele spraak-naar-tekst input.

#### spinnekop-context
Bedrijfscontext en sparring: algemene vragen over Spinnekop, afwegingen tussen vestigingen, praktische haalbaarheid van voorstellen.

#### documentbeheer
Structuur en conventies: waar documenten horen, naamconventies, logboek bijhouden.

#### procesbeheer
Procesdocumentatie: processen aanmaken/updaten, procesflows en Mermaid diagrammen, statusbeheer (draft - review - afgestemd - actief).

**Structuur:** `20-analyse/procesflows.md` (overzicht) + `20-analyse/processen/` (deelprocessen)

#### lean-manufacturing
Lean principes voor metaal/ETO: 5S, visueel management, Kanban en flow, Kaizen en PDCA.

#### eto-cto
Engineer-to-Order kennis: werkvoorbereiding, stuklijsten en routings, offerte-naar-order, doorlooptijdverkorting.

#### magazijn-logistiek
Magazijn en materiaalstromen: voorraadbeheer, ABC-analyse, picking/kitting, magazijnindeling, in-/outbound.

#### ridderiq
ERP systeem: werkorders, planning, stuklijsten, urenregistratie, integratie met lean processen.

**Let op**: Uitgebreide RidderIQ handleiding in `00-klant/Docs/ridderiq-handleiding/`

#### windchill
PLM en tekenbeheer: tekeningen en revisies, CAD-integratie (Creo), documentvrijgave, koppeling met RidderIQ.

---

## Gedragsrichtlijnen

1. **Praktisch denken**: Pas op voor te theoretische adviezen
2. **ETO/CTO realiteit**: Massaproductie-oplossingen werken hier vaak niet
3. **Twee vestigingen**: Denk aan impact op beide locaties
4. **Meetbaar maken**: Vraag naar metrics en baselines
5. **Eigenaarschap**: Wie draagt de verbetering?
6. **Wees betrouwbaar**: Doe wat je zegt, herstel wat breekt, en wordt steeds beter

---

## Documentconventies

### Backlog en acties
- **Alle acties horen in `todo.md`** (de centrale backlog) in de project-root
- Backlog is gestructureerd per traject met visuele statustabel en Mermaid diagram
- Analysedocumenten in `20-analyse/` bevatten **geen todo's of actielijsten**
- Analyses beschrijven de situatie, problemen en oplossingsrichtingen
- Acties die uit een analyse voortkomen worden toegevoegd aan `todo.md` met `[[link]]` naar de analyse
- **Bij verwerking in documenten**: altijd checken of er een gerelateerde backlog-item is dat afgevinkt of bijgewerkt moet worden
- **Bij statuswijzigingen**: ook statustabel, voortgangsbalken, blokkades en Mermaid diagram bijwerken

### Structuur analysedocumenten
Een analyse bevat typisch:
1. Context/uitgangspunt
2. Huidige situatie (met problemen)
3. Voorgestelde oplossing
4. Open vragen (zonder checkboxes)
5. Bijlagen/referenties

**Geen:** checkboxes, actielijsten, "prioriteit 1/2/3" secties

### Word-export richtlijnen

Export via Pandoc: in Obsidian via Ctrl+P - "Export to Word" (Shell commands plugin).

#### Tabellen
- **Max 5 kolommen** - meer past niet in Word
- **Korte kolomheaders** - max 10-12 karakters
- **Geen bold/italic in cellen** - rendering problemen
- Te breed? Splits in meerdere tabellen of gebruik lijsten

#### Diagrammen (Mermaid)
- `flowchart LR` voor simpele flows, `flowchart TD` voor complexe hierarchieen
- Max 6-8 nodes per diagram, korte labels
- Geen subgraphs tenzij echt nodig

#### Algemeen
- Vermijd unicode symbolen - gebruik tekst
- Geen code blocks voor gewone tekst
- Horizontale lijnen (`---`) worden page breaks in Word
- Bold spaarzaam - alleen voor nadruk

---

## Veelgestelde Vragen

**Waar vind ik de RidderIQ documentatie?**
`00-klant/Docs/ridderiq-handleiding/` met index in `_index.md`

**Hoe maak ik een nieuwe logboek entry?**
Kopieer template uit `templates/logboek-entry.md` naar `10-logboek/YYYY-MM-DD.md`

**Waar zet ik nieuwe documenten van de klant?**
In `00-klant/Docs/`

**Hoe werkt de skill activatie?**
Skills worden automatisch geactiveerd bij relevante vragen, of handmatig met `/skill-naam`
