# Spinnekop Tools

Desktop tools voor Spinnekop BV — BOM import, productiestructuur en verdere automatisering.

## Tools

| Tool | Beschrijving | Laatste versie |
|------|-------------|----------------|
| `bom-import-tool.exe` | SolidWorks BOM exporteren naar RidderIQ ERP | zie Releases |
| `productiestructuur.exe` | Productiestructuur beheer | zie Releases |

## Installatie (eenmalig)

1. Ga naar [Releases](https://github.com/ritco/spinnekop-tools/releases)
2. Download de gewenste `.exe`
3. Zet het bestand op de gewenste locatie (bv. `C:\Tools\Spinnekop\`)
4. Dubbelklik om te starten — de tool configureert zichzelf bij de eerste keer

> **Let op**: kopieer ook `config.json` van een andere werkplek of vraag de consultant.

## Automatische updates

Elke tool controleert bij het opstarten of er een nieuwe versie beschikbaar is.
Als er een update is, verschijnt een melding — klik op **Updaten** en de tool herstart automatisch.

- **Stabiele versies**: tools geconfigureerd met `update_channel: "stable"` (standaard)
- **Testversies**: tools geconfigureerd met `update_channel: "prerelease"` (testomgevingen)

Geen actie nodig van de gebruiker, behalve op de updateknop klikken.

---

## Voor de ontwikkelaar — Release Pipeline

### Vereisten

- Python + PyInstaller (`pip install pyinstaller`)
- GitHub CLI (`gh`) — ingelogd als `ritco`
- Werkende VPN-verbinding niet vereist voor releases

### Release aanmaken (stap voor stap)

#### 1. Versie verhogen

In `scripts/main.py` (BOM Import Tool):
```python
__version__ = '1.2.3'  # verhoog patch/minor/major
```

In `scripts/phantom_tool.py` (Productiestructuur):
```python
__version__ = '1.0.2'
```

#### 2. Bouwen

```bash
cd scripts/
python -m PyInstaller --clean bom-import-tool.spec
python -m PyInstaller --clean productiestructuur.spec   # indien van toepassing
```

Output: `scripts/dist/bom-import-tool.exe`

#### 3. Release aanmaken

**Stabiele release (live gebruikers):**
```bash
gh release create bom-v1.2.3 \
  "scripts/dist/bom-import-tool.exe" \
  --repo ritco/spinnekop-tools \
  --title "BOM Import Tool v1.2.3" \
  --notes "Beschrijving van wijzigingen"
```

**Testrelease (testomgeving — pre-release flag):**
```bash
gh release create bom-v1.2.3-test \
  "scripts/dist/bom-import-tool.exe" \
  --repo ritco/spinnekop-tools \
  --title "BOM Import Tool v1.2.3 (test)" \
  --prerelease \
  --notes "Testversie — niet voor productie"
```

#### 4. Verificatie

- Ga naar https://github.com/ritco/spinnekop-tools/releases
- Controleer dat de exe als asset zichtbaar is
- Start de tool op een werkplek → melding "Update beschikbaar" → klik Updaten

---

### Naamconventies releases

| Patroon | Tool | exe naam | Kanaal |
|---------|------|----------|--------|
| `bom-v1.2.3` | BOM Import Tool | `bom-import-tool.exe` | Stabiel (live) |
| `bom-v1.2.3-test` | BOM Import Tool | `bom-import-tool.exe` | Prerelease (test) |
| `productiestructuur-v1.0.2` | Productiestructuur | `productiestructuur.exe` | Stabiel (live) |
| `productiestructuur-v1.0.2-test` | Productiestructuur | `productiestructuur.exe` | Prerelease (test) |

> **Regel**: de tag begint altijd met de tool-naam (of het eerste woord ervan), gevolgd door `-v`. De tool herkent zijn eigen releases automatisch op basis van dit prefix.

---

### Nieuwe tool toevoegen

1. Voeg tool toe in `app_config.py` als het dezelfde update-infrastructuur gebruikt
2. Kies een unieke prefix voor release tags (bv. `scanner-v1.0.0`)
3. Gebruik dezelfde naamconventie voor het `.exe` bestand
4. Documenteer hier in de tabel bovenaan

---

### config.json instellingen (per werkplek)

```json
{
  "sql_server": "10.0.1.5\\RIDDERIQ",
  "sql_auth": "sql",
  "sql_user": "ridderadmin",
  "sql_password": "...",
  "databases": {
    "speel": "Speeltuin 2",
    "live": "Spinnekop Live 2"
  },
  "output_basis": "C:\\BOM-Output",
  "update_github_repo": "ritco/spinnekop-tools",
  "update_channel": "stable"
}
```

Voor testomgevingen: `"update_channel": "prerelease"`

---

## Architectuur

```
GitHub Release (bom-v1.2.3)
  └── bom-import-tool.exe        ← gedownload door auto-update

Werkplek
  ├── bom-import-tool.exe        ← actieve versie
  ├── config.json                ← lokale instellingen (niet in GitHub!)
  └── [output mappen]            ← gegenereerde CSV bestanden
```

De tools gebruiken `config.json` naast de `.exe` voor alle instellingen.
Nooit `config.json` in GitHub zetten — bevat credentials.
