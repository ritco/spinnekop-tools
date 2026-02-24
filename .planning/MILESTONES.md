# Milestones

## v1.0 Release Management (Shipped: 2026-02-24)

**Phases completed:** 3 phases, 5 plans, 0 tasks

**Key accomplishments:**
- `__version__` single source of truth in main.py + dynamic title bar showing version and environment
- Server folder structure: stable (`C:\import\`), dev (`C:\import-test\`), archive (`C:\import\archive\`)
- Public Desktop shortcut for Evy — always points to stable exe
- build.ps1 — versioned PyInstaller build from source with pre-flight checks
- deploy.ps1 — VPN ping-check + Y: drive mapping + push to import-test
- promote.ps1 — archive-before-overwrite safety + one-command promote from dev to stable

---

