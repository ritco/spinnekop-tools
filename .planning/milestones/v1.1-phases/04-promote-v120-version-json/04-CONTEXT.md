# Phase 4: Promote v1.2.0 + version.json - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

promote.ps1 uitbreiden zodat het een version.json genereert met versies van beide tools (bom-import-tool en productiestructuur), en v1.2.0 (config-refactoring) promoten naar Z: (stable). Evy krijgt daarna handmatig de eerste kopie op haar laptop.

</domain>

<decisions>
## Implementation Decisions

### Promote flow
- Per tool apart promoten, niet alles tegelijk
- Syntax: bijv. `promote.ps1 -Tool bom` of `promote.ps1 -Tool prod`
- Zonder parameter: promote alles (beide tools) — Claude kiest de interface
- version.json bevat altijd beide tools — bij promote van één tool behoudt de andere zijn vorige versie
- Als een tool niet op Y: staat: overslaan zonder fout, melding in output

### Fallback & veiligheid
- Atomair: version.json wordt pas geschreven/bijgewerkt NA succesvolle exe-kopie
- Bij falen van de kopie: version.json blijft ongewijzigd
- version.json wordt mee gearchiveerd in Z:\archive\ samen met de oude exe
- Eerste keer (version.json bestaat nog niet): automatisch aanmaken
- -Force flag slaat alle bevestigingen over, inclusief version.json update

### Evy's ervaring
- Evy draait de tool nog niet — dit is een blanco start voor haar
- Eerste installatie: Rik kopieert de exe handmatig naar Evy's laptop
- Na eerste installatie neemt self-update (Phase 5) het over
- Geen installer of setup-script nodig

### Claude's Discretion
- Exacte promote.ps1 parametersyntax (flag naming, defaults)
- version.json bestandsformaat (structuur van het JSON object)
- Output formatting van promote.ps1 (wat wordt er getoond tijdens promote)

</decisions>

<specifics>
## Specific Ideas

- promote.ps1 bestaat al en werkt — dit is een uitbreiding, geen herschrijving
- Huidige promote archiveert al naar Z:\archive\ met timestamp — version.json past in dat mechanisme
- -Force flag is al geïmplementeerd (commit 432ef16)
- version.json moet leesbaar zijn voor de self-update check in Phase 5

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-promote-v120-version-json*
*Context gathered: 2026-02-24*
