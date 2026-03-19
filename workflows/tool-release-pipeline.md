# Tool Release Pipeline — Spinnekop Tools

Hoe we desktop tools bouwen, releasen en distribueren via GitHub.
Dit is de standaard werkwijze voor **alle** tools in `ritco/spinnekop-tools`.

---

## Overzicht

```
Lokale code (scripts/)
  → PyInstaller build (dist/tool.exe)
    → GitHub Release (bom-v1.2.3)
      → Auto-update bij elke gebruiker (bij opstart)
```

**Repo**: `https://github.com/ritco/spinnekop-tools` (public)

**Waarom public?** Tools werken enkel intern (VPN + SQL server achter firewall).
Geen credentials in de repo — wachtwoord wordt bij installatie gevraagd en DPAPI-encrypted opgeslagen.

---

## Bestaande tools

| Tool | exe-naam | Tag-prefix | Entry point |
|------|----------|------------|-------------|
| BOM Import Tool | `bom-import-tool.exe` | `bom-` | `scripts/main.py` |
| Productiestructuur | `productiestructuur.exe` | `productiestructuur-` | `scripts/phantom_tool.py` |
| **ePlan Import Tool** | `eplan-import-tool.exe` | `eplan-` | `scripts/eplan_main.py` |

---

## Release aanmaken (stap voor stap)

### 1. Versie verhogen

In `scripts/main.py` (BOM Import Tool):
```python
__version__ = '1.2.4'  # verhoog patch/minor/major
```

In `scripts/phantom_tool.py` (Productiestructuur):
```python
__version__ = '1.0.2'
```

**Conventies:**
- `patch` (1.2.x) — bugfix of kleine verbetering
- `minor` (1.x.0) — nieuwe feature
- `major` (x.0.0) — grote wijziging of breaking change

### 2. Bouwen

```bash
cd scripts/
python -m PyInstaller --clean bom-import-tool.spec
# Output: scripts/dist/bom-import-tool.exe
```

Vereisten: `pip install pyinstaller`, alle dependencies in requirements.txt.

### 3. Stabiele release aanmaken

```bash
gh release create bom-v1.2.4 \
  "scripts/dist/bom-import-tool.exe" \
  --repo ritco/spinnekop-tools \
  --title "BOM Import Tool v1.2.4" \
  --notes "Beschrijving van wijzigingen"
```

### 4. Testrelease aanmaken (pre-release)

```bash
gh release create bom-v1.2.4-test \
  "scripts/dist/bom-import-tool.exe" \
  --repo ritco/spinnekop-tools \
  --title "BOM Import Tool v1.2.4 (test)" \
  --prerelease \
  --notes "Testversie — niet voor productie"
```

### 5. Verificatie

```bash
gh release view bom-v1.2.4 --repo ritco/spinnekop-tools
```

Of ga naar: `https://github.com/ritco/spinnekop-tools/releases`

Controleer dat `bom-import-tool.exe` als asset zichtbaar is.

---

## Naamconventies

| Patroon | Tool | Kanaal |
|---------|------|--------|
| `bom-v1.2.3` | BOM Import Tool | Stabiel (live gebruikers) |
| `bom-v1.2.3-test` | BOM Import Tool | Prerelease (testomgeving) |
| `productiestructuur-v1.0.2` | Productiestructuur | Stabiel |
| `productiestructuur-v1.0.2-test` | Productiestructuur | Prerelease |
| `eplan-v1.0.0` | ePlan Import Tool | Stabiel (live gebruikers) |
| `eplan-v1.0.0-test` | ePlan Import Tool | Prerelease (testomgeving) |

**Regel**: tag begint altijd met de tool-naam (of het eerste woord), gevolgd door `-v`.

---

## Installatie (eenmalig per werkplek)

### Stabiele versie (gebruikers)
1. Download `install-live.ps1` van de GitHub repo
2. Rechtsklik → "Uitvoeren met PowerShell"
3. Kies installatiemap (standaard `C:\Tools\BOM-Import`)
4. **Voer SQL wachtwoord in** (verschijnt als sterretjes, wordt DPAPI-encrypted opgeslagen)
5. Tool downloadt automatisch de laatste stabiele versie

### Testversie (consultant/developer)
1. Download `install-test.ps1` van de GitHub repo
2. Zelfde stappen — installeert in `C:\Tools\BOM-Import-Test`
3. Volgt pre-releases automatisch op

### Wat de install scripts doen
- Installatiemap aanmaken
- Laatste release downloaden van GitHub API
- `Unblock-File` uitvoeren (voorkomt Windows Defender blokkade)
- `config.json` aanmaken naast de exe:
  - SQL server, gebruiker, databases (speel/live)
  - DPAPI-encrypted wachtwoord (`dpapi:AQAAANCMnd8B...`)
  - `update_github_repo` en `update_channel`
- Snelkoppeling op bureaublad

---

## Auto-update mechanisme

Bij elke opstart checkt de tool GitHub:

```
config.json: update_channel = "stable"
  → GitHub API: /releases/latest
  → Vergelijkt versie
  → Als nieuwer: dialoog "Update beschikbaar"
  → Gebruiker klikt "Updaten"
  → Nieuwe exe gedownload, Unblock-File, bat-script herstart
```

**Test-kanaal** (`update_channel = "prerelease"`):
- Checkt `/releases?per_page=20` en filtert op pre-releases met de tool-prefix
- Valt terug op stabiele versie als geen pre-release gevonden

**Faalveilig**: als GitHub niet bereikbaar (geen internet, firewall) → tool start gewoon op.

---

## Wachtwoord beveiliging (DPAPI)

`config.json` bevat **nooit** een plaintext wachtwoord.

```json
{
  "sql_password": "dpapi:AQAAANCMnd8BFdERjHoAwE/Cl+sBAAAA..."
}
```

- Encrypted door Windows op de installatiemachine
- Onbruikbaar op een andere machine of gebruikersaccount
- `app_config.py` decrypteert transparant via PowerShell bij elke verbinding
- Bij herbouw of nieuwe installatie: wachtwoord opnieuw ingeven

---

## Nieuwe tool toevoegen

1. Maak `scripts/nieuwe-tool.py` met `__version__ = '1.0.0'`
2. Maak `scripts/nieuwe-tool.spec` (zie bom-import-tool.spec als voorbeeld)
3. Kies een unieke tag-prefix (bv. `scanner-v`)
4. Voeg toe aan tabel bovenaan dit document
5. Registreer `update_github_repo` en `update_channel` in de tool via `app_config.py`
6. Bouw en maak eerste release aan
7. Schrijf `install-nieuwe-tool.ps1` op basis van `install-live.ps1`

---

## config.json structuur (per werkplek)

```json
{
  "sql_server": "10.0.1.5\\RIDDERIQ",
  "sql_auth": "sql",
  "sql_user": "ridderadmin",
  "sql_password": "dpapi:...",
  "databases": {
    "speel": "Speeltuin 2",
    "live": "Spinnekop Live 2"
  },
  "output_basis": "C:\\Tools\\BOM-Import",
  "update_github_repo": "ritco/spinnekop-tools",
  "update_channel": "stable"
}
```

`config.json` staat **nooit** in GitHub — bevat machine-specifieke DPAPI credentials.

---

## Troubleshooting

### Stap 1: check de debug log

Bij elk probleem met auto-update: open `update-debug.log` naast de exe.

```
C:\Tools\BOM-Import-Test\update-debug.log   (testkanaal)
C:\Tools\BOM-Import\update-debug.log        (live)
```

Wat je ziet bij een gezonde run:
```
16:06:15 Update check gestart (huidige versie: 1.3.0)
16:06:15 Config pad: C:\Tools\BOM-Import-Test\config.json
16:06:15 Config: repo=ritco/spinnekop-tools channel=prerelease
16:06:15 check_for_update resultaat: {'remote_version': '1.3.1', ...}
16:06:15 Update gevonden: 1.3.1 — dialog tonen
```

Wat je ziet bij een probleem:
```
Config: repo=ritco/spinnekop-tools channel=stable   ← config niet gelezen (zie valkuil 1)
check_for_update resultaat: None                    ← geen update gevonden
```

---

### Bekende valkuilen (hard geleerd)

#### Valkuil 1: PowerShell BOM maakt config.json onleesbaar

**Symptoom**: debug log toont `channel=stable` terwijl config.json `"update_channel": "prerelease"` bevat.

**Oorzaak**: PowerShell 5 (standaard op Windows Server en oudere Windows) schrijft UTF-8 **met BOM** (`\ufeff` aan het begin). Python's `json.load()` met `encoding='utf-8'` crasht op die BOM, gooit een `JSONDecodeError`, en `load_config()` valt stil terug op `DEFAULT_CONFIG` (channel=stable).

**Fix in code**: `app_config.py → load_config()` gebruikt `encoding='utf-8-sig'` — dit strip de BOM automatisch als die aanwezig is.

**Fix voor gebruiker**: verwijder `config.json` en herinstalleer — de nieuwe exe leest de BOM-versie correct.

**Belangrijk voor nieuwe tools**: gebruik altijd `utf-8-sig` bij het lezen van config-bestanden die door PowerShell aangemaakt kunnen zijn.

---

#### Valkuil 2: Settings-dialoog wiste `update_channel` en `update_github_repo`

**Symptoom**: na het openen en opslaan van de instellingen werkt auto-update niet meer.

**Oorzaak**: `_collect_config()` in `show_settings_dialog()` bevatte alleen de velden die zichtbaar zijn in het dialoog. Bij opslaan werden alle andere keys gewist uit `config.json`. Bij de volgende start vulde `DEFAULT_CONFIG` ze terug met `update_channel: 'stable'`.

**Fix in code**: `_save()` start nu vanuit de bestaande config en overlay de dialog-waarden:
```python
def _save():
    existing = load_config()
    existing.update(_collect_config())  # dialog-waarden overschrijven, rest blijft
    save_config(existing)
```

**Regel voor nieuwe tools**: bij elke settings-dialoog die niet alle config-keys toont: altijd starten vanuit bestaande config, nooit een kale dict opslaan.

---

#### Valkuil 3: exe-bestand vergrendeld bij herinstallatie

**Symptoom**: installatiescript faalt met "access denied" of "file in use".

**Oorzaak**: tool draait nog op de achtergrond.

**Fix**: sluit de tool volledig af voor je herinstalleert. Check ook system tray.

---

#### Valkuil 4: PowerShell execution policy blokkeert install script

**Symptoom**: dubbelklik op `.ps1` → wordt geopend in Kladblok of geeft security-fout.

**Fix**: gebruik de `.bat` launcher (staat naast het `.ps1` in de repo) die automatisch `-ExecutionPolicy Bypass` toepast. Of voer manueel uit:
```
PowerShell -ExecutionPolicy Bypass -File install-test.ps1
```

---

#### Valkuil 5: config.json herbouwen na settings-dialoog probleem

Als `update_channel` of `update_github_repo` kwijt zijn:

```
1. Sluit de tool
2. del C:\Tools\BOM-Import-Test\config.json
3. Herinstalleer via PowerShell one-liner (zie Installatie sectie)
```

Het install-script vraagt het SQL-wachtwoord opnieuw en maakt een correcte config.json aan.

---

### Troubleshooting tabel

| Symptoom in debug log | Oorzaak | Oplossing |
|-----------------------|---------|-----------|
| `channel=stable` maar config heeft `prerelease` | BOM in config.json (valkuil 1) | Verwijder config.json, herinstalleer |
| `channel=stable` na settings opslaan | Settings dialog wisde keys (valkuil 2) | Verwijder config.json, herinstalleer |
| `repo=` (leeg) | config.json niet gevonden, fallback naar defaults | Check "Config pad" in debug log — staat exe op juiste plek? |
| `FOUT: [SSL/TLS error]` | Python kan GitHub HTTPS niet bereiken | Controleer internet/firewall; SSL-fix zit in app_config.py |
| `check_for_update resultaat: None` na juiste config | Geen nieuwere versie op GitHub | Controleer releases op GitHub, is tag correct? |
| Update-dialoog verschijnt niet | Threading race (app nog niet klaar) | Wacht 10 sec na opstart; dialoog verschijnt als check klaar is |
| Download hangt | GitHub onbereikbaar | Timeout na 60 sec, tool werkt gewoon verder |
| "DPAPI decryptie mislukt" | Config van andere machine of user | Herinstalleren op huidige machine |
| Exe geblokkeerd door Defender | Zone.Identifier ADS | `Unblock-File` op exe, of herinstalleren |
