# Requirements: BOM Import Tool — Release Management

**Defined:** 2026-02-19
**Core Value:** Evy kan altijd een werkende versie van de tool gebruiken, ongeacht waar Rik in de ontwikkeling zit.

## v1 Requirements

### Versioning

- [x] **VER-01**: Tool heeft een centrale versievariabele (semver, bijv. 1.0.0)
- [x] **VER-02**: Versienummer is zichtbaar in de GUI title bar (incl. actieve omgeving)

### Server-structuur

- [x] **SRV-01**: Stabiele versie staat op `C:\import\bom-import-tool.exe`
- [x] **SRV-02**: Dev/test locatie op `C:\import-test\` met `speel\` en `live\` submappen
- [x] **SRV-03**: Evy heeft een Public Desktop snelkoppeling die naar `C:\import\bom-import-tool.exe` wijst

### Build & Deploy

- [x] **BLD-01**: PowerShell build script dat PyInstaller draait en versienummer inbakt in de exe
- [x] **BLD-02**: PowerShell deploy script dat exe naar `C:\import-test\` op de server kopieert (met VPN/ping check)
- [x] **BLD-03**: Promote commando dat dev versie kopieert naar stable (met archivering oude stable)

### Rollback

- [x] **RBK-01**: Bij promote wordt de oude stable versie verplaatst naar `C:\import\archive\{versie}\`

## v2 Requirements

### Rollback

- **RBK-02**: Rollback commando dat de vorige stabiele versie terugzet vanuit archive

### Automatisering

- **AUT-01**: Changelog generatie bij promote (uit git log)
- **AUT-02**: Automatische versie-bump op basis van commit messages

## Out of Scope

| Feature | Reason |
|---------|--------|
| CI/CD pipeline | Overkill voor 2 gebruikers en 1 tool |
| Git hosting (GitHub/GitLab) | Scripts leven in Obsidian vault, lokale git volstaat |
| Automatische updates | Evy's versie wordt bewust handmatig gepromoot |
| Multi-platform builds | Alleen Windows, alleen deze server |
| Installer/MSI | Exe volstaat, geen installatie nodig |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| VER-01 | Phase 1 | Done |
| VER-02 | Phase 1 | Done |
| SRV-01 | Phase 1 | Done |
| SRV-02 | Phase 1 | Done |
| SRV-03 | Phase 1 | Done |
| BLD-01 | Phase 2 | Done |
| BLD-02 | Phase 2 | Done |
| BLD-03 | Phase 3 | Done |
| RBK-01 | Phase 3 | Done |

**Coverage:**
- v1 requirements: 9 total
- Mapped to phases: 9
- Unmapped: 0

---
*Requirements defined: 2026-02-19*
*Last updated: 2026-02-19 after roadmap creation — traceability complete*
