# Phase 1: Foundation - Context

**Gathered:** 2026-02-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Versienummering toevoegen aan de bom-import-tool broncode en GUI, de huidige exe migreren naar een nieuwe locatie, en de server-mappenstructuur opzetten zodat stable en dev gescheiden zijn. Evy krijgt een snelkoppeling.

</domain>

<decisions>
## Implementation Decisions

### Versie-opzet
- `__version__ = '1.0.0'` bovenaan `main.py` — single source of truth
- Startversie is 1.0.0 (tool werkt, is versie 1)
- Versienummer zichtbaar in GUI (Claude kiest exacte plek — title bar en/of startscherm)
- Omgeving (speel/live) ALTIJD zichtbaar in de title bar — bijv. "BOM Import Tool v1.0.0 [Speelomgeving]"

### Mappenstructuur server
- **Stable (Evy):** `C:\import\bom-import-tool.exe` — direct in de import map, geen submap
- **Dev/test (Rik):** `C:\import-test\bom-import-tool.exe` — aparte map voor testen
- **Archive:** `C:\import\archive\{versienummer}\bom-import-tool.exe` — voor rollback
- **Output (stable):** blijft `C:\import\{omgeving}\{username}\` — niet verplaatsen
- **Output (test):** eigen mappen onder `C:\import-test\{omgeving}\{username}\` — volledig gescheiden
- **import-history.db:** blijft op `C:\import\import-history.db` — niet verhuizen
- Geen version.txt naast de exe — versie staat in de GUI

### Migratie
- Huidige exe verplaatsen van `C:\import\bom-import-tool\bom-import-tool.exe` naar `C:\import\bom-import-tool.exe`
- Oude map `C:\import\bom-import-tool\` opruimen na migratie
- Evy heeft nu GEEN shortcut — navigeert handmatig

### Evy's shortcut
- Snelkoppeling op **Public Desktop** (`C:\Users\Public\Desktop`) — zichtbaar voor alle RDP-gebruikers
- Wijst naar `C:\import\bom-import-tool.exe`
- Naam en icoon: Claude's discretie (herkenbaar en duidelijk)
- Rik werkt als `ridderadmin` — ziet dezelfde shortcut, geen aparte nodig

### Claude's Discretion
- Exacte weergave van versie in GUI (title bar, startscherm, of beide)
- Shortcut naam en icoon-keuze
- Hoe de output base-path wordt geconfigureerd (zodat test-versie naar C:\import-test\ schrijft)

</decisions>

<specifics>
## Specific Ideas

- De gebruiker wil het zo simpel mogelijk: "te veel mapjes" vermijden
- Exe direct in C:\import\ is bewuste keuze — geen extra nesting
- import-test is een aparte wortel zodat test-output nooit in productie-paden terechtkomt

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-foundation*
*Context gathered: 2026-02-19*
