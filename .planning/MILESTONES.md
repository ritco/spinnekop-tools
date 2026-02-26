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


## v1.1 Config + Self-update (Shipped: 2026-02-26)

**Phases completed:** 3 phases, 5 plans
**Timeline:** 7 days (2026-02-19 → 2026-02-26)
**Git range:** feat(04-01) → feat(06-02)

**Key accomplishments:**
- promote.ps1 met -Tool parameter en atomaire version.json generatie op Z:
- Self-update mechanisme: threading timeout voor UNC share, CTk update dialog, exe-swap via batch
- bom-import-tool v1.2.1 self-update E2E bewezen (update dialog, exe-swap + herstart, graceful fallback)
- productiestructuur.exe v1.0.0 met eigen config.json en identiek self-update patroon
- Critical fix: explorer-launch ipv `start ""` voor PyInstaller windowed builds (DLL loading)

---

