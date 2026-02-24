# Requirements: BOM Import Tool — Config + Self-update

**Defined:** 2026-02-24
**Core Value:** Evy kan altijd een werkende versie van de tool gebruiken, ongeacht waar Rik in de ontwikkeling zit.

## v1 Requirements

### Promote & Versioning

- [ ] **PRV-01**: promote.ps1 genereert version.json op Z: met versie van bom-import-tool en productiestructuur
- [ ] **PRV-02**: v1.2.0 is gepromoot naar Z: (stable) via promote.ps1

### Self-update

- [ ] **UPD-01**: Tool checkt bij opstart version.json op netwerk share (`\\10.0.1.5\import`)
- [ ] **UPD-02**: Als er een nieuwere versie is, toont de tool een dialog met versienummers en een "Updaten" knop
- [ ] **UPD-03**: Bij "Updaten" kopieert de tool de nieuwe exe van de share naar de lokale locatie en herstart
- [ ] **UPD-04**: Als de share niet bereikbaar is, start de tool gewoon op zonder foutmelding (graceful fallback)

### Productiestructuur Tool

- [ ] **PST-01**: productiestructuur.exe heeft eigen config.json naast de exe (SQL server, credentials, databases)
- [ ] **PST-02**: productiestructuur.exe heeft dezelfde self-update logica als bom-import-tool (UPD-01 t/m UPD-04)

## v2 Requirements

### Automatisering

- **AUT-01**: Changelog generatie bij promote (uit git log)
- **AUT-02**: Automatische versie-bump op basis van commit messages
- **RBK-02**: Rollback commando dat de vorige stabiele versie terugzet vanuit archive

## Out of Scope

| Feature | Reason |
|---------|--------|
| Auto-update zonder dialog | Gebruiker moet bewust kiezen om te updaten |
| Gedeelde config.json | Elke tool krijgt eigen config — voorkomt conflicten |
| Update via internet | Tools draaien intern, updates via LAN share |
| CI/CD pipeline | Overkill voor 2 gebruikers en 2 tools |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PRV-01 | Phase 4 | Pending |
| PRV-02 | Phase 4 | Pending |
| UPD-01 | Phase 5 | Pending |
| UPD-02 | Phase 5 | Pending |
| UPD-03 | Phase 5 | Pending |
| UPD-04 | Phase 5 | Pending |
| PST-01 | Phase 6 | Pending |
| PST-02 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 8 total
- Mapped to phases: 8
- Unmapped: 0

---
*Requirements defined: 2026-02-24*
*Last updated: 2026-02-24 after roadmap creation*
