#!/usr/bin/env python3
"""BOM Converter - SolidWorks naar RidderIQ CSV Import
Spinnekop BV

Converteert SolidWorks multi-level BOM Excel exports naar
CSV bestanden voor import in RidderIQ ERP.

Gebruik vanuit RidderIQ "Vooraf uitvoeren":
  bom-converter.exe --stap artikelen --omgeving speel --excel "C:\\import\\input\\bom.xlsx"
  bom-converter.exe --stap headers --omgeving live --excel "C:\\import\\input\\bom.xlsx"

Stappen:
  artikelen        -> 01-artikelen.csv              (R_ITEM)
  headers          -> 02-stuklijst-headers.csv      (R_ASSEMBLY)
  regels           -> 03-stuklijstregels.csv        (R_ASSEMBLYDETAILITEM)
  substuklijsten   -> 04-substuklijsten.csv         (R_ASSEMBLYDETAILSUBASSEMBLY)
  bewerkingen      -> 05-bewerkingen.csv            (R_ASSEMBLYMISCWORKSTEP)
  kmb-artikel      -> 06-kmb-artikel-bewerking.csv  (R_ASSEMBLYITEMWORKSTEP)
  kmb-substuklijst -> 07-kmb-substuklijst-bewerking.csv (R_ASSEMBLYSUBASSEMBLYWORKSTEP)
  alles            -> Alle bovenstaande stappen

Omgevingen:
  speel  -> {basis}/speel/   (speelomgeving)
  live   -> {basis}/live/    (productieomgeving)

Basis pad default: C:\\import (de gedeelde map op de RidderIQ server)
"""

import argparse
import csv
import io
import logging
import re
import shutil
import sys
import traceback
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

try:
    import openpyxl
except ImportError:
    openpyxl = None

try:
    import xlrd
except ImportError:
    xlrd = None

if not openpyxl and not xlrd:
    print("FOUT: Geen Excel-reader beschikbaar. "
          "Installeer xlrd (voor .xls) of openpyxl (voor .xlsx).")
    sys.exit(1)


# =============================================================================
# LOGGING - schrijft naar bestand EN console
# =============================================================================

def setup_logging(log_dir: Path):
    """Configureer logging naar bestand en console."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'bom-converter.log'

    # Formatter
    fmt = logging.Formatter(
        '%(asctime)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler (append)
    fh = logging.FileHandler(str(log_file), encoding='utf-8')
    fh.setFormatter(fmt)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logging.Formatter('%(message)s'))

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(fh)
    logger.addHandler(ch)

    return log_file


# =============================================================================
# CONFIGURATIE - Pas aan naar RidderIQ inrichting
# =============================================================================

# SolidWorks Production Process -> RidderIQ Bewerkingscode
PP_TO_BEWERKING = {
    'LS': 'LASEREN',
    'LP': None,         # LP levert 2 bewerkingen, zie LP_BEWERKINGEN
    'PL': 'PL/SN',
    'ZL': 'ZAGEN',
    'LA': 'LASSEN',
    'MO': 'MONTAGE',
    'DF': 'DRAAIEN',
    'OV': None,         # overig
    'AK': None,         # aankoop
}

# LP = Laseren + Plooien -> 2 bewerkingen in volgorde
LP_BEWERKINGEN = ['LASEREN', 'PLOOIEN']

# SolidWorks Finish -> extra RidderIQ bewerking
FINISH_TO_BEWERKING = {
    'GALVA':   'GALVA',
    'KLEUR 1': 'LAKKEN',
    'KLEUR 2': 'LAKKEN',
    'NONE':    None,
    'OTHER':   None,
    'None':    None,
    '':        None,
}

# Artikeleenheid: AK -> STUKS (ID=5), rest -> MAAKDEEL (ID=9)
EENHEID_STUKS = 5
EENHEID_MAAKDEEL = 9

# Registratietraject: Handmatig afboeken (5)
REGISTRATIETRAJECT = 5

# Stocktype: Stockhouden (4)
STOCKTYPE = 4

# Stuklijst status: Beschikbaar (4)
STUKLIJST_STATUS = 4

# Artikelgroep mapping: nummerprefix -> RidderIQ groepnummer
ARTIKELGROEP_PREFIX = {
    '212': 212,
    '231': 231,
    '233': 233,
    '240': 24,
    '260': 26,
    '293': 293,
    '420': 42,
    '450': 45,
}

# PP -> artikelgroep voor engineering nummers (000-xxx, 9xxx)
PP_TO_GROEP = {
    'LS': 6,
    'LP': 6,
    'PL': 6,
    'ZL': 6,
    'DF': 9,
    'LA': 1000,
    'MO': 1000,
    'OV': 6,
}

FALLBACK_GROEP = 293

# Kolomnaam mapping: genormaliseerde headernaam → intern veld
# Headers worden genormaliseerd: ALLE whitespace verwijderd, lowercase
# Dit is nodig omdat V2 Excel headers newlines midden in woorden hebben
# (bijv. 'Producti\non \nProcess' → 'productionprocess')
COLUMN_MAP = {
    'nr.': 'level_raw',
    'structurelevel': 'level_raw',       # V1 variant
    'tek.nr.': 'number',
    'number': 'number',                  # V1 variant
    'revision': 'version',
    'version': 'version',                # V1 variant
    'description': 'name',
    'name': 'name',                      # V1 variant
    'aant.': 'quantity',
    'quantity': 'quantity',              # V1 variant
    'productionprocess': 'production_process',
    'thickness': 'thickness',
    'ptc_wm_lifecycle_state': 'state',
    'state': 'state',                    # V1 variant
    'partmanagement': 'part_management',
    'finish': 'finish',
    'material': 'material',
    'articlecode': 'article_code',
    'length': 'length',
    'angle1': 'angle1',
    'angle2': 'angle2',
    'angledirection': 'angle_direction',
    'anglerotation': 'angle_rotation',
}


def _normalize_header(h: str) -> str:
    """Normaliseer kolomheader: verwijder ALLE whitespace, lowercase.

    Nodig omdat V2 Excel headers newlines midden in woorden hebben:
    'Producti\\non \\nProcess' → 'productionprocess'
    'PTC_WM_LIF\\nECYCLE_STA\\nTE' → 'ptc_wm_lifecycle_state'
    """
    return re.sub(r'\s+', '', str(h)).lower()


# CSV instellingen
CSV_SEPARATOR = ';'
CSV_ENCODING = 'utf-8-sig'

# Standaard basis pad op de RidderIQ server
DEFAULT_BASIS = r'C:\import'

# Stap -> bestandsnaam mapping
STAP_BESTANDEN = {
    'artikelen':       '01-artikelen.csv',
    'headers':         '02-stuklijst-headers.csv',
    'regels':          '03-stuklijstregels.csv',
    'substuklijsten':  '04-substuklijsten.csv',
    'bewerkingen':     '05-bewerkingen.csv',
    'kmb-artikel':     '06-kmb-artikel-bewerking.csv',
    'kmb-substuklijst': '07-kmb-substuklijst-bewerking.csv',
}

# Importvolgorde (voor alles-modus)
STAP_VOLGORDE = [
    'artikelen', 'headers', 'regels', 'substuklijsten',
    'bewerkingen', 'kmb-artikel', 'kmb-substuklijst',
]


# =============================================================================
# HELPERFUNCTIES
# =============================================================================

def get_artikelgroep(number: str, pp: str) -> int:
    """Bepaal de artikelgroep op basis van artikelnummer en productieproces."""
    if pp == 'AK':
        for prefix, groep in ARTIKELGROEP_PREFIX.items():
            if number.startswith(prefix):
                return groep
        return FALLBACK_GROEP

    if number.startswith('000'):
        return PP_TO_GROEP.get(pp, 6)

    if number[0:1].isdigit() and number.startswith('9'):
        return PP_TO_GROEP.get(pp, 6)

    return PP_TO_GROEP.get(pp, FALLBACK_GROEP)


def parse_quantity(qty_str) -> float:
    """Parse '2 each' -> 2.0, None -> 1.0"""
    if not qty_str:
        return 1.0
    m = re.match(r'(\d+(?:\.\d+)?)', str(qty_str).strip())
    return float(m.group(1)) if m else 1.0


def parse_version(version_str: str) -> int:
    """Parse '2.1 (Design)' -> 21 (punt verwijderen, als integer).

    Voorbeelden:
      '2.1'          -> 21
      '2.1 (Design)' -> 21
      '3'            -> 30  (geen minor → 0)
      ''             -> 0
    """
    if not version_str:
        return 0
    m = re.match(r'(\d+)(?:\.(\d+))?', str(version_str).strip())
    if not m:
        return 0
    major = int(m.group(1))
    minor = int(m.group(2)) if m.group(2) else 0
    return major * 10 + minor


def datum_revisie() -> str:
    """Huidige datum in RidderIQ formaat: DD/MM/YY HH:MM:SS"""
    return datetime.now().strftime('%d/%m/%y 00:00:00')


# =============================================================================
# DATA CLASS
# =============================================================================

@dataclass
class BomRow:
    """Een rij uit de SolidWorks BOM Excel (V1 of V2 formaat)."""
    level: int
    number: str
    version: str
    name: str
    quantity: float
    production_process: str
    thickness: str
    state: str
    finish: str
    part_management: str
    # V2 velden
    material: str = ''
    article_code: str = ''       # grondstofcode 140xxx (zaagregels)
    length: float = 0.0          # zaaglengte in mm
    angle1: float = 0.0
    angle2: float = 0.0
    angle_direction: str = ''
    angle_rotation: str = ''
    excel_rij: int = 0           # rijnummer in Excel (voor foutmeldingen)

    parent: Optional['BomRow'] = field(default=None, repr=False)
    children: list = field(default_factory=list, repr=False)

    @property
    def row_type(self) -> str:
        """Bepaal het type rij: artikel, zaagregel, of onbepaald.

        Volgorde is belangrijk: zaagregels hebben article_code + length,
        ook al krijgen ze number/pp toegewezen in de parser.
        """
        if self.article_code and self.length:
            return 'zaagregel'
        if self.number and self.production_process:
            return 'artikel'
        return 'onbepaald'

    @property
    def is_parent(self) -> bool:
        return len(self.children) > 0

    @property
    def is_purchase(self) -> bool:
        return self.production_process == 'AK'

    @property
    def is_zaagregel(self) -> bool:
        return self.row_type == 'zaagregel'

    @property
    def artikeleenheid(self) -> int:
        return EENHEID_STUKS if self.is_purchase else EENHEID_MAAKDEEL

    @property
    def artikelgroep(self) -> int:
        return get_artikelgroep(self.number, self.production_process)

    @property
    def revision_int(self) -> int:
        return parse_version(self.version)


# =============================================================================
# VALIDATIE
# =============================================================================

def validate_bom(bom_rows: list[BomRow]) -> tuple[list[str], list[str]]:
    """Valideer BOM data.

    Returns:
        (fouten, waarschuwingen) - fouten blokkeren conversie
    """
    fouten = []
    waarschuwingen = []

    if not bom_rows:
        fouten.append("Excel bevat geen data-rijen")
        return fouten, waarschuwingen

    for r in bom_rows:
        rij = r.excel_rij

        # Onbepaalde rijen: waarschuwing (niet blokkeren maar melden)
        if r.row_type == 'onbepaald':
            if r.name and r.name.lower() == 'sheet':
                waarschuwingen.append(
                    f"Rij {rij}: Sheet-materiaal zonder grondstofcode "
                    f"(parent: {r.parent.number if r.parent else '?'}, "
                    f"materiaal: {r.material or '?'})"
                )
            elif r.length and not r.article_code:
                fouten.append(
                    f"Rij {rij}: Zaagregel zonder Article Code "
                    f"(profiel: '{r.name}', lengte: {r.length}mm)"
                )
            else:
                waarschuwingen.append(
                    f"Rij {rij}: Onbepaalde rij — geen artikelcode en "
                    f"geen grondstofcode (naam: '{r.name or '(leeg)'}')"
                )
            continue

        # Fouten: stoppen de conversie
        if not r.number or r.number.strip() == '':
            fouten.append(
                f"Rij {rij}: Lege artikelcode "
                f"(niveau {r.level}, naam: '{r.name or '(leeg)'}')"
            )

        if r.quantity <= 0:
            fouten.append(
                f"Rij {rij}: Ongeldige hoeveelheid {r.quantity} "
                f"voor {r.number}"
            )

        # Waarschuwingen: doorgaan maar melden
        if r.number and not r.name:
            waarschuwingen.append(
                f"Rij {rij}: Artikel {r.number} heeft geen omschrijving"
            )

        if (r.production_process
                and r.production_process not in PP_TO_BEWERKING):
            waarschuwingen.append(
                f"Rij {rij}: Onbekend productieproces "
                f"'{r.production_process}' voor {r.number}"
            )

        if r.finish and r.finish not in FINISH_TO_BEWERKING:
            waarschuwingen.append(
                f"Rij {rij}: Onbekende finish "
                f"'{r.finish}' voor {r.number}"
            )

        if r.quantity > 1000:
            waarschuwingen.append(
                f"Rij {rij}: Hoge hoeveelheid ({r.quantity}) "
                f"voor {r.number} - controleer of dit klopt"
            )

    return fouten, waarschuwingen


# =============================================================================
# EXCEL PARSING
# =============================================================================

def _detect_level_format(raw_rows, col_index: dict) -> str:
    """Detecteer niveauformaat: 'dot' (puntnotatie) of 'int' (integer).

    Kijkt of er punten in de niveauwaarden voorkomen.
    """
    idx = col_index.get('level_raw')
    if idx is None:
        return 'int'
    for raw in raw_rows[:50]:
        val = str(raw[idx]).strip() if idx < len(raw) else ''
        if '.' in val:
            return 'dot'
    return 'int'


def _parse_level(raw: str, fmt: str = 'dot') -> int:
    """Parse niveauwaarde op basis van gedetecteerd formaat.

    Puntnotatie (V2): '1' = level 0, '1.1' = level 1, '1.1.1' = level 2
    Integer (V1): '0' = level 0, '1' = level 1, etc.
    """
    s = str(raw).strip()
    if fmt == 'dot':
        # Altijd op basis van diepte (aantal delen - 1)
        return len(s.split('.')) - 1
    return int(float(s))


def _parse_angle(val) -> float:
    """Parse hoekwaarde: '4.5°' -> 4.5, '0°' -> 0.0, '-' -> 0.0"""
    if not val:
        return 0.0
    s = str(val).strip().replace('°', '').replace('\u00b0', '')
    if s in ('-', '', '/'):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def _build_col_index(headers: list[str]) -> dict[str, int]:
    """Bouw mapping van intern veldnaam → kolomindex op basis van headers."""
    col_index = {}
    for i, h in enumerate(headers):
        normalized = _normalize_header(h)
        if normalized in COLUMN_MAP:
            field_name = COLUMN_MAP[normalized]
            if field_name not in col_index:
                col_index[field_name] = i
    return col_index


def _get(row, col_index: dict, field: str, default=''):
    """Haal veldwaarde op uit rij via kolomindex, met default."""
    idx = col_index.get(field)
    if idx is None or idx >= len(row):
        return default
    val = row[idx]
    if val is None:
        return default
    return val


def _clean_str(val, default='') -> str:
    """Converteer waarde naar schone string."""
    if val is None or val == '':
        return default
    s = str(val).strip().replace('\n', ' ')
    # Floats die eigenlijk integers zijn: 233018.0 -> '233018'
    if isinstance(val, float) and val == int(val) and val > 0:
        return str(int(val))
    return s


def parse_bom(excel_path: str) -> list[BomRow]:
    """Parse SolidWorks BOM Excel (V1 .xlsx of V2 .xls) naar BomRows.

    Detecteert automatisch het formaat op basis van:
    - Bestandsextensie (.xls vs .xlsx)
    - Kolomheaders (naam-gebaseerd, niet positie-gebaseerd)
    - Niveaunotatie (puntnotatie vs integer)
    """
    path = Path(excel_path)
    ext = path.suffix.lower()

    # ---- Stap 1: Excel openen en rijen lezen ----
    if ext == '.xls':
        if not xlrd:
            raise ImportError("xlrd is nodig voor .xls bestanden. "
                              "Installeer met: pip install xlrd")
        wb = xlrd.open_workbook(str(path))
        ws = wb.sheet_by_index(0)
        headers = [ws.cell_value(0, c) for c in range(ws.ncols)]
        raw_rows = []
        for r in range(1, ws.nrows):
            raw_rows.append([ws.cell_value(r, c) for c in range(ws.ncols)])
    else:
        if not openpyxl:
            raise ImportError("openpyxl is nodig voor .xlsx bestanden. "
                              "Installeer met: pip install openpyxl")
        wb = openpyxl.load_workbook(str(path), read_only=True)
        ws = wb.active
        all_rows = list(ws.iter_rows(values_only=True))
        wb.close()
        if not all_rows:
            return []
        headers = [str(h) if h else '' for h in all_rows[0]]
        raw_rows = all_rows[1:]

    # ---- Stap 2: Kolomindex opbouwen ----
    col_index = _build_col_index(headers)

    required = ['level_raw', 'name']
    missing = [f for f in required if f not in col_index]
    if missing:
        raise ValueError(
            f"Verplichte kolommen niet gevonden: {missing}. "
            f"Gevonden headers: {[_normalize_header(h) for h in headers]}")

    # Niveauformaat detecteren
    level_fmt = _detect_level_format(raw_rows, col_index)

    log = logging.getLogger()
    log.info(f"  Kolomindex: {col_index}")
    log.info(f"  Niveauformaat: {level_fmt}")

    # ---- Stap 3: Rijen parsen naar BomRows ----
    rows = []
    stack = {}

    for row_idx, raw in enumerate(raw_rows):
        excel_rij = row_idx + 2  # +1 voor 0-index, +1 voor header

        level_raw = _get(raw, col_index, 'level_raw')
        if not level_raw or str(level_raw).strip() == '':
            continue

        level = _parse_level(level_raw, level_fmt)
        tek_nr = _clean_str(_get(raw, col_index, 'number'))
        pp = _clean_str(_get(raw, col_index, 'production_process'))
        article_code = _clean_str(_get(raw, col_index, 'article_code'))
        length_val = _get(raw, col_index, 'length', 0)
        name = _clean_str(_get(raw, col_index, 'name'))

        # Parse length (kan newlines bevatten in V2: '3663.6\n3' → 3663.63)
        try:
            length_clean = re.sub(r'\s+', '', str(length_val)) if length_val else ''
            length = float(length_clean) if length_clean else 0.0
        except (ValueError, TypeError):
            length = 0.0

        # Bepaal het artikelnummer:
        # - Artikelen: Tek.nr. (bijv. 000-313-108)
        # - Zaagregels: Article Code (bijv. 140063)
        # - Onbepaald: leeg
        if tek_nr and pp:
            number = tek_nr
        elif article_code and length:
            number = article_code
            # Grondstoffen zijn altijd aankoopitems
            if not pp:
                pp = 'AK'
        else:
            number = tek_nr  # kan leeg zijn voor onbepaalde rijen

        bom_row = BomRow(
            level=level,
            number=number,
            version=_clean_str(_get(raw, col_index, 'version')),
            name=name,
            quantity=parse_quantity(_get(raw, col_index, 'quantity')),
            production_process=pp,
            thickness=_clean_str(_get(raw, col_index, 'thickness')),
            state=_clean_str(_get(raw, col_index, 'state')),
            finish=_clean_str(_get(raw, col_index, 'finish')),
            part_management=_clean_str(_get(raw, col_index, 'part_management')),
            material=_clean_str(_get(raw, col_index, 'material')),
            article_code=article_code,
            length=length,
            angle1=_parse_angle(_get(raw, col_index, 'angle1')),
            angle2=_parse_angle(_get(raw, col_index, 'angle2')),
            angle_direction=_clean_str(_get(raw, col_index, 'angle_direction')),
            angle_rotation=_clean_str(_get(raw, col_index, 'angle_rotation')),
            excel_rij=excel_rij,
        )

        # Boomstructuur opbouwen (zelfde logica als V1)
        if level > 0:
            parent = stack.get(level - 1)
            if parent:
                parent.children.append(bom_row)
                bom_row.parent = parent

        stack[level] = bom_row
        for l in list(stack.keys()):
            if l > level:
                del stack[l]

        rows.append(bom_row)

    return rows


# =============================================================================
# LS/LP PRUNING - Tak afkappen bij extern gelaserde aankoopstukken
# =============================================================================

def prune_lslp_branches(bom_rows: list[BomRow]) -> list[dict]:
    """Kap takken af onder LS/LP items met kinderen.

    LS/LP items met kinderen zijn extern gelaserde aankoopstukken.
    De onderliggende items (materiaal, zaaglijsten) zijn verantwoordelijkheid
    van de leverancier en worden niet geïmporteerd in RidderIQ.

    Muteert bom_rows in-place: verwijdert afgekapte rijen en maakt
    LS/LP nodes tot bladnodes (children leeggemaakt).

    Returns:
        Lijst van dicts met info over afgekapte takken (voor rapportage).
    """
    pruned = []

    # Verzamel alle LS/LP nodes die kinderen hebben
    lslp_parents = [
        r for r in bom_rows
        if r.production_process in ('LS', 'LP') and r.children
    ]

    if not lslp_parents:
        return pruned

    # Verzamel alle afstammelingen van LS/LP parents
    excluded = set()
    for node in lslp_parents:
        descendants = []
        _collect_descendants(node, descendants)
        excluded.update(id(d) for d in descendants)
        pruned.append({
            'number': node.number,
            'pp': node.production_process,
            'excel_rij': node.excel_rij,
            'n_children': len(descendants),
        })
        # Maak LS/LP node tot bladnode
        node.children.clear()

    # Verwijder afgekapte rijen uit de flat list
    bom_rows[:] = [r for r in bom_rows if id(r) not in excluded]

    return pruned


def _collect_descendants(node: BomRow, result: list):
    """Recursief alle afstammelingen van een node verzamelen."""
    for child in node.children:
        result.append(child)
        _collect_descendants(child, result)


# =============================================================================
# ANALYSE
# =============================================================================

def collect_parents(bom_rows: list[BomRow]) -> dict[str, BomRow]:
    """Verzamel alle unieke parents (artikelen met kinderen)."""
    parents = {}
    for r in bom_rows:
        if r.is_parent and r.number not in parents:
            parents[r.number] = r
    return parents


def collect_parent_numbers(bom_rows: list[BomRow]) -> set[str]:
    """Verzamel alle artikelnummers die ergens als parent voorkomen."""
    return {r.number for r in bom_rows if r.is_parent}


def compute_stuklijst_layout(parent: BomRow, parent_numbers: set) -> dict:
    """Bereken het Posnr-schema voor een stuklijst.

    Volgorde: PP-bewerking(en) -> kinderen -> finish-bewerking
    """
    layout = {
        'pp_bewerkingen': [],
        'children': [],
        'finish_bewerkingen': [],
    }

    posnr = 10
    volgnr = 10
    pp = parent.production_process

    # 1. PP-bewerking(en) vooraan
    if pp == 'LP':
        for bew in LP_BEWERKINGEN:
            layout['pp_bewerkingen'].append((bew, volgnr, posnr))
            posnr += 10
            volgnr += 10
    else:
        bew = PP_TO_BEWERKING.get(pp)
        if bew:
            layout['pp_bewerkingen'].append((bew, volgnr, posnr))
            posnr += 10
            volgnr += 10

    # 2. Kinderen
    for child in parent.children:
        is_sub = child.number in parent_numbers
        layout['children'].append((child, posnr, is_sub))
        posnr += 10

    # 3. Finish-bewerking achteraan
    finish_bew = FINISH_TO_BEWERKING.get(parent.finish)
    if finish_bew:
        existing_codes = {b[0] for b in layout['pp_bewerkingen']}
        if finish_bew not in existing_codes:
            layout['finish_bewerkingen'].append((finish_bew, volgnr, posnr))

    return layout


# =============================================================================
# CSV SCHRIJVEN EN ARCHIVEREN
# =============================================================================

def write_csv(path: Path, headers: list[str], rows: list[list]):
    """Schrijf CSV met ; separator en UTF-8 BOM encoding."""
    with open(path, 'w', newline='', encoding=CSV_ENCODING) as f:
        writer = csv.writer(f, delimiter=CSV_SEPARATOR)
        writer.writerow(headers)
        writer.writerows(rows)
    logging.getLogger().info(f"  {path.name}: {len(rows)} regels")


def archive_existing(output_dir: Path, bestandsnaam: str):
    """Verplaats bestaand CSV bestand naar archief/ met timestamp."""
    csv_path = output_dir / bestandsnaam
    if not csv_path.exists():
        return

    archief_dir = output_dir / 'archief'
    archief_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    archive_name = f"{csv_path.stem}_{timestamp}{csv_path.suffix}"
    dest = archief_dir / archive_name
    shutil.move(str(csv_path), str(dest))
    logging.getLogger().info(
        f"  Archief: {bestandsnaam} -> archief/{archive_name}"
    )


# =============================================================================
# CSV GENERATORS
# =============================================================================

def generate_artikelen(bom_rows, output_dir, article_filter=None):
    """01 - Unieke artikellijst voor R_ITEM import.

    Inclusief grondstoffen (140xxx) uit zaagregels als AK-artikelen.
    Onbepaalde rijen zonder artikelcode worden overgeslagen.
    """
    seen = set()
    rows = []

    for r in bom_rows:
        if not r.number or r.number.strip() == '':
            continue
        if r.number in seen:
            continue
        if article_filter and r.number not in article_filter:
            continue
        seen.add(r.number)
        rows.append([
            r.number,
            r.name,
            r.name,
            r.artikelgroep,
            r.artikeleenheid,
            REGISTRATIETRAJECT,
            STOCKTYPE,
        ])

    write_csv(
        output_dir / '01-artikelen.csv',
        ['Artikelcode', 'Omschrijving', 'Omschrijving Engels',
         'Artikelgroep', 'Artikeleenheid', 'Registratietraject', 'Stocktype'],
        rows
    )
    return len(rows)


def generate_stuklijst_headers(bom_rows, output_dir, article_filter=None):
    """02 - Stuklijst headers voor R_ASSEMBLY import."""
    parents = collect_parents(bom_rows)
    datum = datum_revisie()
    rows = []

    for number, r in parents.items():
        if article_filter and r.number not in article_filter:
            continue
        rows.append([
            r.number, r.name, r.number, datum,
            STUKLIJST_STATUS, r.revision_int, 1, r.number,
        ])

    write_csv(
        output_dir / '02-stuklijst-headers.csv',
        ['Stuklijstnummer', 'Omschrijving', 'Tekeningnummer',
         'Datum revisie', 'Stuklijst status', 'Revisie',
         'Maakdeelvoorkeur', 'Artikelcode'],
        rows
    )
    return len(rows)


def generate_stuklijstregels(bom_rows, output_dir, article_filter=None):
    """03 - Artikelregels (leaf-artikelen) voor R_ASSEMBLYDETAILITEM import."""
    parent_numbers = collect_parent_numbers(bom_rows)
    parents = collect_parents(bom_rows)
    rows = []

    for number, parent in parents.items():
        if article_filter and parent.number not in article_filter:
            continue
        layout = compute_stuklijst_layout(parent, parent_numbers)
        for child, posnr, is_sub in layout['children']:
            if not is_sub and (not article_filter
                               or child.number in article_filter):
                rows.append([
                    parent.number, child.number, child.name,
                    int(child.quantity), posnr,
                ])

    write_csv(
        output_dir / '03-stuklijstregels.csv',
        ['Stuklijstnummer', 'Artikelcode', 'Omschrijving',
         'Aantal', 'Posnr'],
        rows
    )
    return len(rows)


def generate_substuklijsten(bom_rows, output_dir, article_filter=None):
    """04 - Substuklijst-koppelingen voor R_ASSEMBLYDETAILSUBASSEMBLY."""
    parent_numbers = collect_parent_numbers(bom_rows)
    parents = collect_parents(bom_rows)
    rows = []

    for number, parent in parents.items():
        if article_filter and parent.number not in article_filter:
            continue
        layout = compute_stuklijst_layout(parent, parent_numbers)
        for child, posnr, is_sub in layout['children']:
            if is_sub and (not article_filter
                           or child.number in article_filter):
                rows.append([
                    parent.number, child.number, child.name,
                    int(child.quantity), posnr,
                ])

    write_csv(
        output_dir / '04-substuklijsten.csv',
        ['Stuklijstnummer', 'Substuklijst', 'Omschrijving',
         'Aantal', 'Posnr'],
        rows
    )
    return len(rows)


def generate_bewerkingen(bom_rows, output_dir, article_filter=None):
    """05 - Stuklijstregel bewerkingen voor R_ASSEMBLYMISCWORKSTEP."""
    parent_numbers = collect_parent_numbers(bom_rows)
    parents = collect_parents(bom_rows)
    rows = []
    seen = set()

    for number, parent in parents.items():
        if article_filter and parent.number not in article_filter:
            continue
        layout = compute_stuklijst_layout(parent, parent_numbers)
        for bew_code, volgnr, posnr in layout['pp_bewerkingen']:
            key = (parent.number, bew_code)
            if key not in seen:
                seen.add(key)
                rows.append([parent.number, bew_code, volgnr, posnr, 0.0, 1])
        for bew_code, volgnr, posnr in layout['finish_bewerkingen']:
            key = (parent.number, bew_code)
            if key not in seen:
                seen.add(key)
                rows.append([parent.number, bew_code, volgnr, posnr, 0.0, 1])

    write_csv(
        output_dir / '05-bewerkingen.csv',
        ['Stuklijstnummer', 'Bewerking', 'Volgnr', 'Posnr',
         'Loongroep', 'Cycli'],
        rows
    )
    return len(rows)


def generate_kmb_artikel_bewerking(bom_rows, output_dir,
                                   article_filter=None):
    """06 - KMB artikel-bewerking voor R_ASSEMBLYITEMWORKSTEP."""
    parent_numbers = collect_parent_numbers(bom_rows)
    parents = collect_parents(bom_rows)
    rows = []

    for number, parent in parents.items():
        if article_filter and parent.number not in article_filter:
            continue
        layout = compute_stuklijst_layout(parent, parent_numbers)
        if not layout['pp_bewerkingen']:
            continue
        pp_bew_code, pp_volgnr, pp_posnr = layout['pp_bewerkingen'][0]
        rev = parent.revision_int
        bew_key = (f"{parent.number} rev {rev} "
                   f"seq {pp_volgnr}-{pp_bew_code}")
        for child, posnr, is_sub in layout['children']:
            if not is_sub and (not article_filter
                               or child.number in article_filter):
                artikel_key = (f"{parent.number} rev {rev} "
                               f"pos {posnr}-{child.number}")
                rows.append([parent.number, artikel_key, bew_key])

    write_csv(
        output_dir / '06-kmb-artikel-bewerking.csv',
        ['Stuklijstnummer', 'KMB stuklijstregel artikel',
         'KMB stuklijstregel bewerking'],
        rows
    )
    return len(rows)


def generate_kmb_substuklijst_bewerking(bom_rows, output_dir,
                                        article_filter=None):
    """07 - KMB substuklijst-bewerking voor R_ASSEMBLYSUBASSEMBLYWORKSTEP."""
    parent_numbers = collect_parent_numbers(bom_rows)
    parents = collect_parents(bom_rows)
    rows = []

    for number, parent in parents.items():
        if article_filter and parent.number not in article_filter:
            continue
        layout = compute_stuklijst_layout(parent, parent_numbers)
        if not layout['pp_bewerkingen']:
            continue
        pp_bew_code, pp_volgnr, pp_posnr = layout['pp_bewerkingen'][0]
        rev = parent.revision_int
        bew_key = (f"{parent.number} rev {rev} "
                   f"seq {pp_volgnr}-{pp_bew_code}")
        for child, posnr, is_sub in layout['children']:
            if is_sub and (not article_filter
                           or child.number in article_filter):
                sub_key = (f"{parent.number} rev {rev} "
                           f"pos {posnr}-{child.number}")
                rows.append([parent.number, sub_key, bew_key])

    write_csv(
        output_dir / '07-kmb-substuklijst-bewerking.csv',
        ['Stuklijstnummer', 'KMB stuklijstregel substuklijst',
         'KMB stuklijstregel bewerking'],
        rows
    )
    return len(rows)


# Stap -> generator functie
STAP_GENERATORS = {
    'artikelen':       generate_artikelen,
    'headers':         generate_stuklijst_headers,
    'regels':          generate_stuklijstregels,
    'substuklijsten':  generate_substuklijsten,
    'bewerkingen':     generate_bewerkingen,
    'kmb-artikel':     generate_kmb_artikel_bewerking,
    'kmb-substuklijst': generate_kmb_substuklijst_bewerking,
}


# =============================================================================
# SAMENVATTING
# =============================================================================

def print_summary(bom_rows: list[BomRow]):
    """Print een beknopt overzicht van de BOM."""
    log = logging.getLogger()
    parent_numbers = collect_parent_numbers(bom_rows)
    unique = {r.number for r in bom_rows if r.number}

    # Rijtypes tellen
    n_artikel = sum(1 for r in bom_rows if r.row_type == 'artikel')
    n_zaag = sum(1 for r in bom_rows if r.row_type == 'zaagregel')
    n_onbepaald = sum(1 for r in bom_rows if r.row_type == 'onbepaald')

    log.info(f"  Totaal regels:    {len(bom_rows)}")
    log.info(f"  Unieke artikelen: {len(unique)}")
    log.info(f"  Stuklijsten:      {len(parent_numbers)}")
    if n_zaag or n_onbepaald:
        log.info(f"  Artikelregels:    {n_artikel}")
        log.info(f"  Zaagregels:       {n_zaag}")
        log.info(f"  Onbepaald:        {n_onbepaald}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='BOM Converter - SolidWorks naar RidderIQ CSV',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Stappen:
  artikelen        01-artikelen.csv
  headers          02-stuklijst-headers.csv
  regels           03-stuklijstregels.csv
  substuklijsten   04-substuklijsten.csv
  bewerkingen      05-bewerkingen.csv
  kmb-artikel      06-kmb-artikel-bewerking.csv
  kmb-substuklijst 07-kmb-substuklijst-bewerking.csv
  alles            Alle bovenstaande

Voorbeelden:
  bom-converter.exe --stap artikelen --omgeving speel --excel bom.xlsx
  bom-converter.exe --stap alles --omgeving live --excel bom.xlsx
  bom-converter.exe --stap regels --omgeving speel --excel bom.xlsx --filter "000-313-118,000-313-120"
"""
    )
    parser.add_argument(
        '--stap',
        required=True,
        choices=list(STAP_BESTANDEN.keys()) + ['alles'],
        help='Welke CSV te genereren (of "alles" voor alle stappen)'
    )
    parser.add_argument(
        '--omgeving',
        required=True,
        choices=['speel', 'live'],
        help='Doelomgeving: speel of live'
    )
    parser.add_argument(
        '--excel',
        required=True,
        help='Pad naar SolidWorks BOM Excel export'
    )
    parser.add_argument(
        '--basis',
        default=DEFAULT_BASIS,
        help=f'Basis pad voor output (default: {DEFAULT_BASIS})'
    )
    parser.add_argument(
        '--filter',
        default=None,
        help='Kommagescheiden artikelnummers om te filteren'
    )
    parser.add_argument(
        '--geen-archief',
        action='store_true',
        help='Bestaande CSV niet archiveren (overschrijven)'
    )

    args = parser.parse_args()

    # Logging starten - schrijf naar {basis}/{omgeving}/
    output_dir = Path(args.basis) / args.omgeving
    log_file = setup_logging(output_dir)
    log = logging.getLogger()

    try:
        # Paden bepalen
        excel_path = Path(args.excel)
        if not excel_path.exists():
            log.error(f"Excel bestand niet gevonden: {excel_path}")
            log.error(f"  Werkdirectory: {Path.cwd()}")
            sys.exit(1)

        if not output_dir.exists():
            log.error(f"Output directory bestaat niet: {output_dir}")
            sys.exit(1)

        # Filter parsen
        article_filter = None
        if args.filter:
            article_filter = {a.strip() for a in args.filter.split(',')}

        # Header
        log.info("=" * 60)
        log.info("BOM Converter - Spinnekop")
        log.info("=" * 60)
        log.info(f"  Excel:     {excel_path}")
        log.info(f"  Excel abs: {excel_path.resolve()}")
        log.info(f"  Omgeving:  {args.omgeving}")
        log.info(f"  Output:    {output_dir}")
        log.info(f"  Stap:      {args.stap}")
        log.info(f"  CWD:       {Path.cwd()}")
        if article_filter:
            log.info(f"  Filter:    {len(article_filter)} artikelen")

        # Excel inlezen
        log.info("Excel inlezen...")
        bom_rows = parse_bom(str(excel_path))

        # LS/LP takken afkappen
        pruned = prune_lslp_branches(bom_rows)
        for p in pruned:
            log.info(f"  LS/LP afgekapt: {p['number']} ({p['pp']}) "
                     f"— {p['n_children']} items verwijderd")

        print_summary(bom_rows)

        # Validatie
        log.info("Validatie...")
        fouten, waarschuwingen = validate_bom(bom_rows)

        for w in waarschuwingen:
            log.warning(f"  {w}")

        if fouten:
            log.error("FOUTEN GEVONDEN - conversie gestopt:")
            for f in fouten:
                log.error(f"  {f}")
            log.error(f"Totaal: {len(fouten)} fout(en), "
                       f"{len(waarschuwingen)} waarschuwing(en)")
            sys.exit(1)

        if waarschuwingen:
            log.info(f"  {len(waarschuwingen)} waarschuwing(en) - "
                     f"conversie gaat door")
        else:
            log.info("  OK")

        # Stappen bepalen
        if args.stap == 'alles':
            stappen = STAP_VOLGORDE
        else:
            stappen = [args.stap]

        # Genereren
        log.info("CSV genereren:")
        totaal_regels = 0
        for stap in stappen:
            bestandsnaam = STAP_BESTANDEN[stap]

            if not args.geen_archief:
                archive_existing(output_dir, bestandsnaam)

            generator = STAP_GENERATORS[stap]
            n = generator(bom_rows, output_dir, article_filter)
            totaal_regels += n

        log.info(f"Klaar: {len(stappen)} bestand(en), "
                 f"{totaal_regels} regels totaal")
        log.info(f"Output: {output_dir}")

    except SystemExit:
        raise
    except Exception:
        log.error("ONVERWACHTE FOUT:")
        log.error(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    # Crash-log: vangt ALLES op, ook fouten voor logging/argparse start
    CRASH_LOG = Path(DEFAULT_BASIS) / 'bom-converter-crash.log'
    try:
        main()
    except SystemExit as e:
        # Normale exit (ook bij argparse --help of fouten)
        with open(CRASH_LOG, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now()}: exit code {e.code}\n")
            f.write(f"  args: {sys.argv}\n")
            f.write(f"  cwd:  {Path.cwd()}\n\n")
        sys.exit(e.code)
    except Exception:
        with open(CRASH_LOG, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now()}: CRASH\n")
            f.write(f"  args: {sys.argv}\n")
            f.write(f"  cwd:  {Path.cwd()}\n")
            f.write(traceback.format_exc())
            f.write("\n")
        sys.exit(1)
