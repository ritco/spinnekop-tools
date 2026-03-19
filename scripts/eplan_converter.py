"""ePlan Converter - ePlan Excel naar RidderIQ CSV import
Spinnekop BV

Leest ePlan stuklijst-exports, matcht componenten aan bestaande
RidderIQ-artikelen via SQL, en genereert CSV-bestanden voor import.

Gebruik:
    result = convert(excel_path, env='speel', dry_run=True)   # analyse
    result = convert(excel_path, env='speel', dry_run=False)  # genereer CSV
"""

import csv
import io
import logging
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

try:
    import openpyxl
except ImportError:
    openpyxl = None

# app_config ligt naast dit bestand in scripts/. Importeer direct of via
# sys.path zodat de module werkt als scripts.eplan_converter (vanuit project-root)
# én als standalone script (vanuit scripts/).
try:
    from app_config import get_connection, get_output_basis
except ImportError:
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    from app_config import get_connection, get_output_basis

log = logging.getLogger(__name__)

# =============================================================================
# CONSTANTEN
# =============================================================================

EPLAN_ARTIKELGROEP_PK = 673      # CODE "26" - Elektrische componenten divers
EPLAN_REGISTRATIONPATH = 5       # Handmatig afboeken
EPLAN_INVENTORYKIND = 4          # Stockhouden
EPLAN_ARTIKELEENHEID = 5         # STUKS
EPLAN_STUKLIJST_STATUS = 4       # Beschikbaar
CSV_SEPARATOR = ';'
CSV_ENCODING = 'utf-8-sig'

# CSV kolomheaders — identiek aan bom_converter.py zodat dezelfde
# RidderIQ importschema's herbruikt kunnen worden.
ARTIKEL_HEADERS = [
    'Artikelcode', 'Omschrijving', 'Omschrijving Engels',
    'Artikelgroep', 'Artikeleenheid', 'Registratietraject', 'Stocktype',
]
HEADER_HEADERS = [
    'Stuklijstnummer', 'Omschrijving', 'Tekeningnummer',
    'Datum revisie', 'Stuklijst status', 'Revisie',
    'Maakdeelvoorkeur', 'Artikelcode',
]
REGELS_HEADERS = [
    'Stuklijstnummer', 'Artikelcode', 'Omschrijving',
    'Aantal', 'Posnr', 'Lengte', 'Verstek links', 'Verstek rechts',
    'Rotatie',
]


# =============================================================================
# DATACLASSES
# =============================================================================

@dataclass
class EplanRow:
    bestelnummer: str        # bijv. 'SE.GV2ME08'
    fabrikant: str           # bijv. 'SE' (Schneider Electric)
    naam_in_schema: str      # bijv. 'Q1'
    hoeveelheid: float
    excel_rij: int


@dataclass
class ConversionResult:
    errors: List[str] = field(default_factory=list)       # blokkerend
    warnings: List[str] = field(default_factory=list)     # niet-blokkerend
    matched: List[dict] = field(default_factory=list)     # {'bestelnummer', 'ridderiq_code', 'omschrijving', 'qty'}
    new_items: List[dict] = field(default_factory=list)   # {'bestelnummer', 'new_code', 'omschrijving', 'qty', 'fabrikant'}
    skipped: List[dict] = field(default_factory=list)     # {'rij', 'reden'}
    projectnaam: str = ''

    @property
    def has_blockers(self) -> bool:
        return len(self.errors) > 0


# =============================================================================
# EXCEL PARSING
# =============================================================================

def parse_eplan_excel(excel_path: str) -> Tuple[str, List[EplanRow]]:
    """Lees een ePlan stuklijst Excel en geef (projectnaam, rijen) terug.

    Vaste posities:
    - Rij 4 (index 3): projectnaam — cel B4
    - Rij 6 (index 5): kolomheaders
    - Rij 7+ (index 6+): dataregels

    Kolommen worden gezocht op naam (case-insensitief, strip whitespace):
      'Fabrikant', 'Bestelnummer', 'Hoeveelheid', 'Naam in schema'

    Raises:
        ValueError: als een verplichte kolom niet gevonden wordt
        ImportError: als openpyxl niet beschikbaar is
    """
    if openpyxl is None:
        raise ImportError(
            "openpyxl is vereist voor het lezen van ePlan Excel bestanden. "
            "Installeer met: pip install openpyxl"
        )

    path = Path(excel_path)
    wb = openpyxl.load_workbook(str(path), read_only=True)
    try:
        ws = wb.active
        all_rows = list(ws.iter_rows(values_only=True))
    finally:
        wb.close()

    if len(all_rows) < 6:
        raise ValueError(
            f"Excel bestand heeft minder dan 6 rijen — "
            f"geen geldige ePlan stuklijst: {path.name}"
        )

    # Rij 4 (index 3): projectnaam in kolom B (index 1)
    row4 = all_rows[3]
    projectnaam = ''
    if len(row4) > 1 and row4[1] is not None:
        projectnaam = str(row4[1]).strip()
    elif len(row4) > 0 and row4[0] is not None:
        # Fallback: kolom A als B leeg is
        val = str(row4[0]).strip()
        # Sla "Project:" label over
        if val.lower() not in ('project:', 'project'):
            projectnaam = val

    # Rij 6 (index 5): kolomheaders
    header_row = all_rows[5]
    headers = [str(h).strip() if h is not None else '' for h in header_row]

    # Kolommen zoeken op naam (case-insensitief)
    col_idx = {}
    for i, h in enumerate(headers):
        normalized = h.lower()
        if normalized == 'fabrikant':
            col_idx['fabrikant'] = i
        elif normalized == 'bestelnummer':
            col_idx['bestelnummer'] = i
        elif normalized == 'hoeveelheid':
            col_idx['hoeveelheid'] = i
        elif normalized == 'naam in schema':
            col_idx['naam_in_schema'] = i

    required = ['fabrikant', 'bestelnummer', 'hoeveelheid', 'naam_in_schema']
    missing = [k for k in required if k not in col_idx]
    if missing:
        raise ValueError(
            f"Verplichte kolommen niet gevonden: {missing}. "
            f"Gevonden headers: {headers}"
        )

    # Rij 7+ (index 6+): dataregels
    rijen: List[EplanRow] = []
    for rij_idx, raw in enumerate(all_rows[6:], start=7):
        if not raw:
            continue

        def _get_cel(key: str, default=''):
            idx = col_idx.get(key)
            if idx is None or idx >= len(raw):
                return default
            val = raw[idx]
            if val is None:
                return default
            return str(val).strip()

        bestelnummer = _get_cel('bestelnummer')
        fabrikant = _get_cel('fabrikant')
        naam_in_schema = _get_cel('naam_in_schema')
        hoeveelheid_str = _get_cel('hoeveelheid', '1')

        # Lege tussenrijen: alle relevante cellen leeg → overslaan
        if not bestelnummer and not fabrikant and not naam_in_schema:
            continue

        # Hoeveelheid parsen
        try:
            m = re.match(r'(\d+(?:[.,]\d+)?)', hoeveelheid_str)
            hoeveelheid = float(m.group(1).replace(',', '.')) if m else 1.0
        except (ValueError, AttributeError):
            hoeveelheid = 1.0

        rijen.append(EplanRow(
            bestelnummer=bestelnummer,
            fabrikant=fabrikant,
            naam_in_schema=naam_in_schema,
            hoeveelheid=hoeveelheid,
            excel_rij=rij_idx,
        ))

    return projectnaam, rijen


def aggregate_rows(rijen: List[EplanRow]) -> Tuple[List[EplanRow], List[dict]]:
    """Aggregeer rijen: groepeer op bestelnummer (case-insensitief), sommeer hoeveelheden.

    Rijen zonder Bestelnummer EN zonder Fabrikant worden overgeslagen.

    Returns:
        (geaggregeerde_rijen, skipped_lijst)
    """
    skipped: List[dict] = []
    aggregated: dict = {}  # bestelnummer_lower -> EplanRow (eerste, met opgetelde qty)

    for rij in rijen:
        # Rijen zonder Bestelnummer EN zonder Fabrikant: overslaan
        if not rij.bestelnummer and not rij.fabrikant:
            skipped.append({
                'rij': rij.excel_rij,
                'reden': 'Geen Bestelnummer of Fabrikant',
            })
            continue

        key = rij.bestelnummer.lower() if rij.bestelnummer else ''

        if key not in aggregated:
            # Eerste keer dit bestelnummer: maak kopie en gebruik die
            aggregated[key] = EplanRow(
                bestelnummer=rij.bestelnummer,
                fabrikant=rij.fabrikant,
                naam_in_schema=rij.naam_in_schema,
                hoeveelheid=rij.hoeveelheid,
                excel_rij=rij.excel_rij,
            )
        else:
            # Duplicaat: sommeer hoeveelheid
            aggregated[key].hoeveelheid += rij.hoeveelheid

    return list(aggregated.values()), skipped


# =============================================================================
# ZOEKTERM EXTRACTIE
# =============================================================================

def _extract_zoekterm(bestelnummer: str) -> Tuple[str, bool]:
    """Extraheer de zoekterm uit een bestelnummer.

    Bevat punt: split op EERSTE punt, gebruik het deel NA het punt.
    Geen punt: gebruik volledige string als zoekterm.

    Returns:
        (zoekterm, heeft_punt)

    Voorbeelden:
        'SE.GV2ME08'  -> ('GV2ME08', True)
        'GV2ME08'     -> ('GV2ME08', False)
        'SE.LC1.D09'  -> ('LC1.D09', True)  # split op EERSTE punt
    """
    if '.' in bestelnummer:
        # Split op eerste punt, gebruik deel na het punt
        idx = bestelnummer.index('.')
        zoekterm = bestelnummer[idx + 1:]
        return zoekterm, True
    return bestelnummer, False


# =============================================================================
# SQL — ARTIKELCODE GENERATIE
# =============================================================================

def get_next_26xxx_code(conn, _counter: list = None) -> str:
    """Genereer de volgende vrije 26xxx artikelcode.

    Haalt MAX(CODE) op uit R_ITEM WHERE CODE LIKE '26%'.
    Geeft '260001' als er nog geen 26xxx codes zijn.

    Args:
        conn: Open pyodbc verbinding
        _counter: Optionele lijst [int] als lokale teller (voor meerdere nieuwe
                  artikelen in één run zonder tussentijdse DB updates)
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(CODE) FROM R_ITEM WHERE CODE LIKE '26%'")
        row = cursor.fetchone()
        cursor.close()

        max_code = row[0] if row and row[0] else None

        if max_code is None:
            base_num = 0
        else:
            # Strip '26' prefix, parse als int
            suffix = str(max_code)[2:]
            try:
                base_num = int(suffix)
            except ValueError:
                base_num = 0

        # Verhoog met 1 (of meer als we een lokale teller bijhouden)
        offset = 1
        if _counter is not None:
            offset = _counter[0] + 1
            _counter[0] = offset

        new_num = base_num + offset
        return f'26{new_num:04d}'

    except Exception as e:
        log.warning("get_next_26xxx_code: fout bij MAX query: %s", e)
        return '260001'


# =============================================================================
# SQL MATCHING
# =============================================================================

def match_components(rijen: List[EplanRow], conn) -> ConversionResult:
    """Match ePlan componenten aan bestaande RidderIQ artikelen via SQL.

    Voor elk component:
    - Extraheer zoekterm uit Bestelnummer (split op eerste punt)
    - Zoek in R_ITEM.OMSCHRIJVING LIKE '%zoekterm%'
    - 0 matches -> nieuw artikel (26xxx code)
    - 1 match -> gebruik bestaande CODE
    - 2+ matches -> blokkerende fout

    Args:
        rijen: Geaggregeerde EplanRow lijst
        conn:  Open pyodbc verbinding (of None)

    Returns:
        ConversionResult met matches, new_items, warnings, errors
    """
    result = ConversionResult()

    if conn is None:
        result.errors.append(
            "Geen verbinding met RidderIQ. Controleer VPN en serveradres."
        )
        return result

    # Haal MAX 26xxx code eenmalig op, bijgehouden via lokale teller
    _counter = [0]  # [0] = aantal reeds aangemaakt in deze run

    # Initialiseer teller op 0 (get_next_26xxx_code verhoogt intern)
    # We halen de BASE waarde op en verhogen zelf:
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(CODE) FROM R_ITEM WHERE CODE LIKE '26%'")
        row = cursor.fetchone()
        cursor.close()
        max_code = row[0] if row and row[0] else None
        if max_code is None:
            base_26_num = 0
        else:
            suffix = str(max_code)[2:]
            try:
                base_26_num = int(suffix)
            except ValueError:
                base_26_num = 0
    except Exception as e:
        log.warning("Kan MAX 26xxx code niet ophalen: %s", e)
        base_26_num = 0

    nieuw_teller = 0  # Hoeveel nieuwe artikelen in deze run aangemaakt

    for rij in rijen:
        zoekterm, heeft_punt = _extract_zoekterm(rij.bestelnummer)

        if not heeft_punt:
            result.warnings.append(
                f"Rij {rij.excel_rij}: Bestelnummer '{rij.bestelnummer}' heeft geen punt "
                f"— gebruik volledige string als zoekterm"
            )

        # SQL zoekquery op OMSCHRIJVING
        zoek_param = f'%{zoekterm}%'
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT CODE, OMSCHRIJVING FROM R_ITEM WHERE OMSCHRIJVING LIKE ?",
                (zoek_param,)
            )
            matches = cursor.fetchall()
            cursor.close()
        except Exception as e:
            result.errors.append(
                f"Rij {rij.excel_rij}: SQL fout bij zoeken naar "
                f"'{rij.bestelnummer}': {e}"
            )
            continue

        n = len(matches)

        if n == 0:
            # Nieuw artikel: genereer 26xxx code
            nieuw_teller += 1
            new_num = base_26_num + nieuw_teller
            new_code = f'26{new_num:04d}'

            result.new_items.append({
                'bestelnummer': rij.bestelnummer,
                'new_code': new_code,
                'omschrijving': rij.naam_in_schema,
                'qty': rij.hoeveelheid,
                'fabrikant': rij.fabrikant,
            })

        elif n == 1:
            ridderiq_code = matches[0][0]
            omschrijving = matches[0][1] or rij.naam_in_schema
            result.matched.append({
                'bestelnummer': rij.bestelnummer,
                'ridderiq_code': ridderiq_code,
                'omschrijving': omschrijving,
                'qty': rij.hoeveelheid,
            })

        else:  # n >= 2
            conflict_codes = ', '.join(str(m[0]) for m in matches)
            result.errors.append(
                f"Rij {rij.excel_rij}: Bestelnummer '{rij.bestelnummer}' "
                f"heeft {n} matches in R_ITEM: {conflict_codes} — "
                f"pas OMSCHRIJVING aan of gebruik artikelcode direct"
            )

    return result


# =============================================================================
# CSV SCHRIJVEN
# =============================================================================

def _write_csv(path: Path, headers: List[str], rows: List[list]):
    """Schrijf een CSV bestand met ; separator en UTF-8 BOM encoding."""
    with open(path, 'w', newline='', encoding=CSV_ENCODING) as f:
        writer = csv.writer(f, delimiter=CSV_SEPARATOR)
        writer.writerow(headers)
        writer.writerows(rows)
    log.info("  %s: %d regels geschreven", path.name, len(rows))


def _datum_revisie() -> str:
    """Huidige datum in RidderIQ formaat: DD/MM/YY HH:MM:SS"""
    return datetime.now().strftime('%d/%m/%y 00:00:00')


def write_output(projectnaam: str, rijen: List[EplanRow],
                 result: ConversionResult, env: str):
    """Schrijf de 3 output CSV bestanden naar de output map.

    Bestanden:
      01-nieuwe-artikelen-eplan.csv  — R_ITEM import (alleen als nieuwe artikelen)
      02-stuklijst-header.csv        — R_ASSEMBLY import
      03-stuklijstregels.csv         — R_ASSEMBLYDETAILITEM import

    CSV kolommen zijn identiek aan bom_converter.py zodat dezelfde
    RidderIQ importschema's gebruikt kunnen worden.
    """
    output_basis = get_output_basis()
    output_dir = output_basis / env
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- 01: Nieuwe artikelen (R_ITEM) ---
    if result.new_items:
        artikel_rows = []
        for item in result.new_items:
            artikel_rows.append([
                item['new_code'],
                item['omschrijving'],
                item['omschrijving'],        # Omschrijving Engels (zelfde)
                EPLAN_ARTIKELGROEP_PK,
                EPLAN_ARTIKELEENHEID,
                EPLAN_REGISTRATIONPATH,
                EPLAN_INVENTORYKIND,
            ])
        _write_csv(
            output_dir / '01-nieuwe-artikelen-eplan.csv',
            ARTIKEL_HEADERS,
            artikel_rows,
        )

    # --- 02: Stuklijst header (R_ASSEMBLY) ---
    datum = _datum_revisie()
    # Gebruik projectnaam als stuklijstnummer
    stuklijst_nr = projectnaam or 'EPLAN-IMPORT'
    header_rows = [[
        stuklijst_nr,       # Stuklijstnummer
        stuklijst_nr,       # Omschrijving
        stuklijst_nr,       # Tekeningnummer
        datum,              # Datum revisie
        EPLAN_STUKLIJST_STATUS,  # Stuklijst status
        0,                  # Revisie
        1,                  # Maakdeelvoorkeur
        stuklijst_nr,       # Artikelcode
    ]]
    _write_csv(
        output_dir / '02-stuklijst-header.csv',
        HEADER_HEADERS,
        header_rows,
    )

    # --- 03: Stuklijstregels (R_ASSEMBLYDETAILITEM) ---
    regel_rows = []
    posnr = 10

    # Eerst: gematchte artikelen
    for item in result.matched:
        regel_rows.append([
            stuklijst_nr,
            item['ridderiq_code'],
            item['omschrijving'],
            int(item['qty']),
            posnr,
            '',  # Lengte (niet van toepassing)
            '',  # Verstek links
            '',  # Verstek rechts
            0,   # Rotatie
        ])
        posnr += 10

    # Dan: nieuwe artikelen
    for item in result.new_items:
        regel_rows.append([
            stuklijst_nr,
            item['new_code'],
            item['omschrijving'],
            int(item['qty']),
            posnr,
            '',  # Lengte
            '',  # Verstek links
            '',  # Verstek rechts
            0,   # Rotatie
        ])
        posnr += 10

    _write_csv(
        output_dir / '03-stuklijstregels.csv',
        REGELS_HEADERS,
        regel_rows,
    )

    log.info(
        "Output geschreven naar: %s (%d matched, %d nieuw)",
        output_dir, len(result.matched), len(result.new_items)
    )


# =============================================================================
# HOOFD INTERFACE
# =============================================================================

def convert(excel_path: str, env: str, dry_run: bool = True) -> ConversionResult:
    """Converteer een ePlan Excel stuklijst naar RidderIQ CSV bestanden.

    Stap 1: Excel parsen
    Stap 2: Aggregeren (dedupliceren op Bestelnummer)
    Stap 3: SQL verbinding openen
    Stap 4: Componenten matchen aan R_ITEM
    Stap 5: (plan 02) Stuklijst-duplicaatcheck
    Stap 6: CSV schrijven (alleen als dry_run=False en geen blockers)

    Args:
        excel_path: Pad naar ePlan Excel export
        env:        Omgeving: 'speel' of 'live'
        dry_run:    True = analyse zonder bestanden te schrijven

    Returns:
        ConversionResult met alle matches, nieuwe artikelen, fouten, waarschuwingen
    """
    result = ConversionResult()

    # Stap 1: Excel parsen
    try:
        projectnaam, rijen = parse_eplan_excel(excel_path)
        result.projectnaam = projectnaam
        log.info("Excel gelezen: %d rijen, projectnaam=%r", len(rijen), projectnaam)
    except Exception as e:
        result.errors.append(f"Excel lezen mislukt: {e}")
        return result

    # Stap 2: Aggregeren
    rijen, skipped = aggregate_rows(rijen)
    result.skipped.extend(skipped)
    log.info(
        "Aggregatie: %d unieke componenten, %d overgeslagen",
        len(rijen), len(skipped)
    )
    if not rijen:
        result.warnings.append("Excel bevat geen dataregels (rij 7+)")

    # Stap 3: SQL verbinding
    try:
        conn, info = get_connection(env)
    except Exception as e:
        result.errors.append(f"Verbindingsfout: {e}. Controleer VPN.")
        return result

    if conn is None:
        result.errors.append(
            f"Geen verbinding: {info}. Controleer VPN en serveradres."
        )
        return result

    log.info("Verbonden: %s", info)

    # Stap 4: Matchen
    try:
        match_result = match_components(rijen, conn)
        result.errors.extend(match_result.errors)
        result.warnings.extend(match_result.warnings)
        result.matched.extend(match_result.matched)
        result.new_items.extend(match_result.new_items)
    finally:
        conn.close()

    # Stap 5: Stuklijst-duplicaatcheck (BOM-01)
    try:
        conn2, _ = get_connection(env)
        if conn2:
            cursor = conn2.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM R_ASSEMBLY WHERE CODE = ?",
                (result.projectnaam,)
            )
            count = cursor.fetchone()[0]
            conn2.close()
            if count > 0:
                result.errors.append(
                    f"Stuklijst '{result.projectnaam}' bestaat al in R_ASSEMBLY. "
                    f"Verwijder de bestaande stuklijst in RidderIQ of gebruik "
                    f"een andere projectnaam."
                )
    except Exception as e:
        result.warnings.append(f"Kan stuklijst-duplicaatcheck niet uitvoeren: {e}")

    # Stap 6: CSV schrijven
    if not dry_run and not result.has_blockers:
        try:
            write_output(result.projectnaam, rijen, result, env)
        except Exception as e:
            result.errors.append(f"CSV schrijven mislukt: {e}")

    log.info(
        "Convert klaar: %d matched, %d nieuw, %d fouten, %d waarschuwingen",
        len(result.matched), len(result.new_items),
        len(result.errors), len(result.warnings)
    )
    return result


# =============================================================================
# MAIN — voor handmatig testen
# =============================================================================

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    _log = logging.getLogger(__name__)

    excel = sys.argv[1] if len(sys.argv) > 1 else '20-analyse/Inputdocumenten/Stuklijst.xlsx'
    env = sys.argv[2] if len(sys.argv) > 2 else 'speel'

    _log.info("ePlan Converter — dry run")
    _log.info(f"  Excel: {excel}")
    _log.info(f"  Omgeving: {env}")

    result = convert(excel, env, dry_run=True)

    _log.info("")
    _log.info("Resultaat:")
    _log.info(f"  Matched:      {len(result.matched)}")
    _log.info(f"  Nieuw:        {len(result.new_items)}")
    _log.info(f"  Overgeslagen: {len(result.skipped)}")
    _log.info(f"  Warnings:     {len(result.warnings)}")
    _log.info(f"  Fouten:       {len(result.errors)}")

    for w in result.warnings:
        _log.warning(f"  WAARSCHUWING: {w}")
    for e in result.errors:
        _log.error(f"  FOUT: {e}")

    if result.has_blockers:
        _log.error("GEBLOKKEERD — geen bestanden worden geschreven")
        sys.exit(1)
    else:
        _log.info("OK — dry run geslaagd")
