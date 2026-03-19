"""BOM + ePlan Import Tool — SQL Server Audit Logger
Spinnekop BV

Schrijft een gecentraliseerd logboek naar de SpinnekopTools database op de SQL Server.
Elke gebruiker die de tool uitvoert schrijft hier naar toe, ongeacht welk toestel.

Faalveilig: als de SQL Server niet bereikbaar is, wordt dit stilzwijgend genegeerd.
De normale werking van de tool wordt nooit geblokkeerd door audit-fouten.
"""

import logging
import os
import socket
from datetime import datetime

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SQL statements
# ---------------------------------------------------------------------------

# Maak de tabel aan als die nog niet bestaat
# Database SpinnekopTools moet eenmalig aangemaakt worden via setup-spinnekoptools.sql (als sa)
_CREATE_TABLE_SQL = """
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'BOM_IMPORT_LOG')
CREATE TABLE BOM_IMPORT_LOG (
    id                  INT IDENTITY PRIMARY KEY,
    tijdstip            DATETIME2        NOT NULL,
    gebruiker           NVARCHAR(100)    NOT NULL,
    toestel             NVARCHAR(100)    NOT NULL,
    omgeving            NVARCHAR(50)     NOT NULL,
    database_naam       NVARCHAR(200)    NOT NULL DEFAULT '',
    excel_bestand       NVARCHAR(500),
    bovenste_artikel    NVARCHAR(100),
    stap                NVARCHAR(50)     NOT NULL,
    status              NVARCHAR(20)     NOT NULL,
    artikelen           INT,
    stuklijsten         INT,
    zaagregels          INT,
    fouten_json         NVARCHAR(MAX),
    waarschuwingen      INT,
    csv_files           NVARCHAR(MAX),
    output_map          NVARCHAR(500),
    kmb_artikelen       INT,
    kmb_substuklijsten  INT,
    kmb_overgeslagen    INT,
    kmb_fouten          NVARCHAR(MAX)
);
"""

_INSERT_SQL = """
INSERT INTO BOM_IMPORT_LOG (
    tijdstip, gebruiker, toestel, omgeving, database_naam,
    excel_bestand, bovenste_artikel, stap, status,
    artikelen, stuklijsten, zaagregels, fouten_json, waarschuwingen,
    csv_files, output_map,
    kmb_artikelen, kmb_substuklijsten, kmb_overgeslagen, kmb_fouten
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

# ---------------------------------------------------------------------------
# ePlan audit — SQL statements
# ---------------------------------------------------------------------------

_CREATE_EPLAN_TABLE_SQL = """
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'EPLAN_IMPORT_LOG')
CREATE TABLE EPLAN_IMPORT_LOG (
    id                  INT IDENTITY PRIMARY KEY,
    tijdstip            DATETIME2        NOT NULL,
    gebruiker           NVARCHAR(100)    NOT NULL,
    toestel             NVARCHAR(100)    NOT NULL,
    omgeving            NVARCHAR(50)     NOT NULL,
    excel_bestand       NVARCHAR(500),
    project_naam        NVARCHAR(200),
    matched             INT,
    nieuwe_artikelen    INT,
    overgeslagen        INT,
    fouten              INT,
    duur_seconden       FLOAT,
    status              NVARCHAR(20)     NOT NULL,
    foutmelding         NVARCHAR(MAX)
);
"""

_INSERT_EPLAN_SQL = """
INSERT INTO EPLAN_IMPORT_LOG (
    tijdstip, gebruiker, toestel, omgeving,
    excel_bestand, project_naam, matched, nieuwe_artikelen,
    overgeslagen, fouten, duur_seconden, status, foutmelding
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


# ---------------------------------------------------------------------------
# Schema initialisatie
# ---------------------------------------------------------------------------

_schema_initialized = False
_eplan_schema_initialized = False


def _ensure_schema(conn):
    """Maak database en tabel aan als ze nog niet bestaan. Idempotent."""
    global _schema_initialized
    if _schema_initialized:
        return

    cur = conn.cursor()
    cur.execute(_CREATE_TABLE_SQL)
    conn.commit()

    _schema_initialized = True


# ---------------------------------------------------------------------------
# Publieke API
# ---------------------------------------------------------------------------

def log_import(
    *,
    omgeving: str,
    stap: str,
    status: str,
    gebruiker: str = None,
    toestel: str = None,
    database_naam: str = '',
    excel_bestand: str = None,
    bovenste_artikel: str = None,
    artikelen: int = None,
    stuklijsten: int = None,
    zaagregels: int = None,
    fouten_json: str = None,
    waarschuwingen: int = None,
    csv_files: str = None,
    output_map: str = None,
    kmb_artikelen: int = None,
    kmb_substuklijsten: int = None,
    kmb_overgeslagen: int = None,
    kmb_fouten: str = None,
):
    """Log een import-actie naar de SQL Server audit tabel.

    Parameters
    ----------
    omgeving        : 'speel' of 'live'
    stap            : 'csv_genereren' of 'kmb_linken'
    status          : 'ok', 'fout', of vrije tekst
    gebruiker       : Windows gebruikersnaam (auto-detected als None)
    toestel         : Hostname (auto-detected als None)
    database_naam   : Naam van de RidderIQ database die gebruikt werd
    excel_bestand   : Bestandsnaam van het Excel bestand (zonder pad)
    bovenste_artikel: Artikelnummer van het hoogste niveau (level 0)
    artikelen       : Aantal unieke artikelen in de BOM
    stuklijsten     : Aantal stuklijstkoppen
    zaagregels      : Aantal zaagregels
    fouten_json     : JSON dict met fouten per type {"RegelNaam": aantal}
    waarschuwingen  : Aantal waarschuwingen
    csv_files       : Kommalijst van aangemaakte CSV bestanden
    output_map      : Absoluut pad naar de output map
    kmb_artikelen   : Aantal artikel-bewerking koppelingen aangemaakt
    kmb_substuklijsten: Aantal substuklijst-bewerking koppelingen aangemaakt
    kmb_overgeslagen: Aantal bestaande koppelingen overgeslagen
    kmb_fouten      : JSON array van foutmeldingen bij KMB stap
    """
    try:
        from app_config import get_audit_connection

        conn, info = get_audit_connection()
        if conn is None:
            log.debug("Audit logging overgeslagen (geen verbinding): %s", info)
            return

        _ensure_schema(conn)

        if gebruiker is None:
            try:
                gebruiker = os.getlogin()
            except Exception:
                gebruiker = os.environ.get('USERNAME', 'onbekend')

        if toestel is None:
            try:
                toestel = socket.gethostname()
            except Exception:
                toestel = 'onbekend'

        cur = conn.cursor()
        cur.execute(_INSERT_SQL, (
            datetime.now(),
            gebruiker,
            toestel,
            omgeving,
            database_naam or '',
            excel_bestand,
            bovenste_artikel,
            stap,
            status,
            artikelen,
            stuklijsten,
            zaagregels,
            fouten_json,
            waarschuwingen,
            csv_files,
            output_map,
            kmb_artikelen,
            kmb_substuklijsten,
            kmb_overgeslagen,
            kmb_fouten,
        ))
        conn.commit()
        conn.close()

        log.debug("Audit log geschreven: %s/%s → %s", omgeving, stap, status)

    except Exception as e:
        log.warning("Audit logging mislukt (niet kritiek): %s", e)
        # Schrijf ook naar audit-debug.log naast de exe voor diagnose
        try:
            import sys
            from pathlib import Path
            log_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
            with open(log_dir / 'audit-debug.log', 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now():%H:%M:%S} FOUT ({stap}): {e}\n")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# ePlan schema initialisatie
# ---------------------------------------------------------------------------

def _ensure_eplan_schema(conn):
    """Maak EPLAN_IMPORT_LOG tabel aan als die nog niet bestaat. Idempotent."""
    global _eplan_schema_initialized
    if _eplan_schema_initialized:
        return

    cur = conn.cursor()
    cur.execute(_CREATE_EPLAN_TABLE_SQL)
    conn.commit()

    _eplan_schema_initialized = True


# ---------------------------------------------------------------------------
# ePlan publieke API
# ---------------------------------------------------------------------------

def log_eplan_import(
    *,
    omgeving: str,
    status: str,
    excel_bestand: str = None,
    project_naam: str = None,
    matched: int = None,
    nieuwe_artikelen: int = None,
    overgeslagen: int = None,
    fouten: int = None,
    duur_seconden: float = None,
    foutmelding: str = None,
    gebruiker: str = None,
    toestel: str = None,
):
    """Log een ePlan import-actie naar de SQL Server audit tabel.

    Parameters
    ----------
    omgeving         : 'speel' of 'live'
    status           : 'ok' of 'fout'
    excel_bestand    : Bestandsnaam van het Excel bestand (zonder pad)
    project_naam     : Projectnaam uit het ePlan Excel bestand (rij 4)
    matched          : Aantal gematchte componenten
    nieuwe_artikelen : Aantal nieuw aangemaakte artikelen (26xxx)
    overgeslagen     : Aantal overgeslagen rijen
    fouten           : Aantal blokkerende fouten
    duur_seconden    : Verwerkingstijd in seconden (optioneel, nullable)
    foutmelding      : Samengevatte foutmeldingen ('; '-gescheiden)
    gebruiker        : Windows gebruikersnaam (auto-detected als None)
    toestel          : Hostname (auto-detected als None)
    """
    try:
        from app_config import get_audit_connection

        conn, info = get_audit_connection()
        if conn is None:
            log.debug("Audit logging overgeslagen (geen verbinding): %s", info)
            return

        _ensure_eplan_schema(conn)

        if gebruiker is None:
            try:
                gebruiker = os.getlogin()
            except Exception:
                gebruiker = os.environ.get('USERNAME', 'onbekend')

        if toestel is None:
            try:
                toestel = socket.gethostname()
            except Exception:
                toestel = 'onbekend'

        cur = conn.cursor()
        cur.execute(_INSERT_EPLAN_SQL, (
            datetime.now(),
            gebruiker,
            toestel,
            omgeving,
            excel_bestand,
            project_naam,
            matched,
            nieuwe_artikelen,
            overgeslagen,
            fouten,
            duur_seconden,
            status,
            foutmelding,
        ))
        conn.commit()
        conn.close()

        log.debug("Audit log geschreven: ePlan %s → %s", omgeving, status)

    except Exception as e:
        log.warning("Audit logging mislukt (niet kritiek): %s", e)
        # Schrijf ook naar audit-debug.log naast de exe voor diagnose
        try:
            import sys
            from pathlib import Path
            log_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
            with open(log_dir / 'audit-debug.log', 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now():%H:%M:%S} FOUT (eplan_import): {e}\n")
        except Exception:
            pass
