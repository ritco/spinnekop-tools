# Requirements: Locatie Scanner v2.0

**Defined:** 2026-03-09
**Core Value:** Magazijniers kunnen zelfstandig vaste artikellocaties scannen en registreren in RidderIQ — altijd beschikbaar, zonder hulp van consultant.

## v2.0 Requirements

### Deployment

- [ ] **DEPL-01**: Locatie Scanner draait als Windows Service op VMSERVERRUM — altijd beschikbaar
- [ ] **DEPL-02**: Service herstart automatisch na crash of server reboot
- [ ] **DEPL-03**: App bereikbaar op vast IP/poort vanuit het magazijn-netwerk

### UX

- [ ] **UX-01**: Toetsenbord sluit automatisch wanneer camera scanner opent

### Gebruikers

- [ ] **USER-01**: Magazijnier selecteert zijn naam uit dropdown voor hij begint met scannen
- [ ] **USER-02**: Elke scan registreert wie het deed (CREATOR/USERCHANGED in DB)
- [ ] **USER-03**: Audit log zichtbaar in de app (wie scande wat, wanneer)

### HTTPS

- [ ] **CERT-01**: App draait op HTTPS zodat camera werkt zonder Chrome flag
- [ ] **CERT-02**: Telefoon kan de app openen zonder certificaatwaarschuwing (of eenmalig accepteren)

## Future Requirements

- Meerdere magazijnen (Roeselare) ondersteunen
- Locatie verwijderen / artikel van locatie halen
- Zoekfunctie: welke artikelen liggen op locatie X?
- Dashboard met scan-statistieken

## Out of Scope

| Feature | Reason |
|---------|--------|
| Native mobile app | Web app op telefoon is voldoende, geen App Store complexiteit |
| Login/wachtwoord systeem | Dropdown met namen volstaat voor intern magazijngebruik |
| Multi-tenant | Eén bedrijf, één server |
| Automatische updates | Server-side app, update = deploy nieuwe versie |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DEPL-01 | Phase 7 | Pending |
| DEPL-02 | Phase 7 | Pending |
| DEPL-03 | Phase 7 | Pending |
| UX-01 | Phase 8 | Pending |
| USER-01 | Phase 9 | Pending |
| USER-02 | Phase 9 | Pending |
| USER-03 | Phase 9 | Pending |
| CERT-01 | Phase 8 | Pending |
| CERT-02 | Phase 8 | Pending |

**Coverage:**
- v2.0 requirements: 9 total
- Mapped to phases: 9
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-09*
*Last updated: 2026-03-09 after roadmap creation*
