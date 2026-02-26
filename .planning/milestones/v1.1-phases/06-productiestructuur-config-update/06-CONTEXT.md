# Phase 6: Productiestructuur Config + Update - Context

**Gathered:** 2026-02-26
**Status:** Ready for planning

<domain>
## Phase Boundary

productiestructuur.exe krijgt een eigen config.json naast de exe (SQL server, credentials, databases) en dezelfde self-update logica als bom-import-tool. Na deze phase kan productiestructuur zelfstandig updates ophalen van de netwerk share.

</domain>

<decisions>
## Implementation Decisions

### Config scope
- Eigen config.json per tool, niet gedeeld (tools draaien op aparte machines)
- Identieke velden als bom-import-tool: sql_server, sql_auth, sql_user, sql_password, databases (speel/live), output_basis, update_share
- Hergebruik DEFAULT_CONFIG uit app_config.py
- Jurgen draait productiestructuur op een aparte machine, niet op Evy's laptop
- Eerste installatie: Rik kopieert exe + config.json handmatig naar Jurgens laptop

### Self-update integratie
- Identiek patroon als bom-import-tool: check voor GUI start, dialog na App init via app.after(100, ...)
- tool_name = 'productiestructuur', exe_name = 'productiestructuur.exe'
- Versie-bump van 0.1.0 naar 1.0.0
- Versie tonen in titelbalk: "Productiestructuur v1.0.0"
- _resolve_share(), share_override, twee-fase update check — allemaal hergebruiken

### Settings dialog
- Hergebruik show_settings_dialog() uit app_config.py, ongewijzigd
- Bestaande settings knop in phantom_tool.py roept show_settings_dialog() aan met callback om connectie te herladen
- Omgevingskeuze (Speel/Live) leest database namen uit config.json in plaats van hardcoded
- Als config.json ontbreekt: direct settings dialog openen (consistent met bom-import-tool)

### Build & deploy flow
- Identieke flow: build met PyInstaller, deploy naar Y:, promote naar Z: via promote.ps1 -Tool prod
- productiestructuur.spec is al correct (console=False, hiddenimports ok)
- Versie-bump, build, deploy, promote en E2E test zijn onderdeel van het uitvoeringsplan
- Rik test lokaal met checkpoint (net als bij bom-import-tool)

### Claude's Discretion
- Exacte refactoring van phantom_tool.py (welke hardcoded waarden worden vervangen door config)
- Hoe de twee-fase update check structureel past in phantom_tool.py's bestaande App class
- Eventuele hidden imports aanpassen als de integratie nieuwe dependencies toevoegt

</decisions>

<specifics>
## Specific Ideas

- Het patroon uit bom-import-tool (main.py) is het bewezen voorbeeld: _check_update_before_gui() + _show_update_after_gui()
- app_config.py hoeft waarschijnlijk niet aangepast te worden — alle functies zijn al tool-agnostisch (tool_name als parameter)
- promote.ps1 ondersteunt al -Tool prod

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 06-productiestructuur-config-update*
*Context gathered: 2026-02-26*
