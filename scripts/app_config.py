"""App Config — Gedeelde configuratie voor BOM Import Tool en Productiestructuur
Spinnekop BV

Verantwoordelijkheden:
- config.json laden/opslaan naast de exe
- Gedeelde SQL Server connectie (vervangt dubbele implementatie)
- Basis pad detectie (vervangt gedupliceerde _detect_basis)
- Update check en self-update mechanisme
- Settings dialoog (CTk, herbruikbaar door beide tools)
"""

import json
import logging
import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path

def _parse_version(v: str) -> tuple:
    """Parse versiestring '1.2.3' naar tuple (1, 2, 3) voor vergelijking."""
    try:
        return tuple(int(x) for x in v.strip().split('.'))
    except (ValueError, AttributeError):
        return (0,)

try:
    import pyodbc
    HAS_PYODBC = True
except ImportError:
    HAS_PYODBC = False

log = logging.getLogger(__name__)

# =============================================================================
# BASIS PAD
# =============================================================================

def get_basis_path() -> Path:
    """Detecteer basis pad vanuit exe-locatie (PyInstaller) of scriptlocatie."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent


# =============================================================================
# CONFIG — LADEN / OPSLAAN
# =============================================================================

CONFIG_FILENAME = 'config.json'

DEFAULT_CONFIG = {
    'sql_server': r'10.0.1.5\RIDDERIQ',
    'sql_auth': 'sql',          # 'sql', 'windows', of 'auto'
    'sql_user': 'ridderadmin',
    'sql_password': 'riad01*',
    'databases': {
        'speel': 'Speeltuin 05-02-26',
        'live': 'Spinnekop Live',
    },
    'output_basis': '.',        # Relatief aan exe, of absoluut pad
    'update_share': r'\\10.0.1.5\import',
}

# ODBC drivers in volgorde van voorkeur
ODBC_DRIVERS = [
    'ODBC Driver 17 for SQL Server',
    'ODBC Driver 13 for SQL Server',
    'SQL Server Native Client 11.0',
    'SQL Server',
]


def _config_path() -> Path:
    """Pad naar config.json naast de exe/script."""
    return get_basis_path() / CONFIG_FILENAME


def load_config() -> dict:
    """Laad config.json. Geeft DEFAULT_CONFIG als bestand niet bestaat."""
    path = _config_path()
    if not path.exists():
        return dict(DEFAULT_CONFIG)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Vul ontbrekende keys aan met defaults
        merged = dict(DEFAULT_CONFIG)
        merged.update(data)
        if isinstance(data.get('databases'), dict):
            merged['databases'] = dict(DEFAULT_CONFIG['databases'])
            merged['databases'].update(data['databases'])
        return merged
    except Exception as e:
        log.warning("Kan config.json niet laden: %s — defaults gebruikt", e)
        return dict(DEFAULT_CONFIG)


def save_config(config: dict) -> Path:
    """Sla config op als config.json. Geeft het pad terug."""
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    log.info("Config opgeslagen: %s", path)
    return path


def config_exists() -> bool:
    """Check of er al een config.json bestaat."""
    return _config_path().exists()


def get_output_basis() -> Path:
    """Geeft het output basis pad terug, resolved tegen de exe-locatie."""
    config = load_config()
    basis = config.get('output_basis', '.')
    path = Path(basis)
    if not path.is_absolute():
        path = get_basis_path() / path
    return path.resolve()


# =============================================================================
# SQL CONNECTIE
# =============================================================================

def find_odbc_driver() -> str | None:
    """Vind de beste beschikbare ODBC driver."""
    if not HAS_PYODBC:
        return None
    try:
        available = pyodbc.drivers()
    except Exception:
        return None
    for candidate in ODBC_DRIVERS:
        if candidate in available:
            return candidate
    return None


def get_connection(omgeving: str, config: dict = None) -> tuple:
    """Maak verbinding met RidderIQ SQL Server.

    Leest instellingen uit config.json (of meegegeven config dict).
    Ondersteunt sql auth, windows auth, of auto (probeert sql, dan windows).

    Returns: (connection, info_string) bij succes,
             (None, error_string) bij falen.
    """
    if not HAS_PYODBC:
        return None, "pyodbc niet beschikbaar in deze build"

    if config is None:
        config = load_config()

    databases = config.get('databases', {})
    database = databases.get(omgeving)
    if not database:
        return None, f"Onbekende omgeving: '{omgeving}'"

    driver = find_odbc_driver()
    if not driver:
        try:
            available = pyodbc.drivers()
            drivers_txt = ', '.join(available) if available else '(geen)'
        except Exception:
            drivers_txt = '(kan niet opvragen)'
        return None, (
            f"Geen geschikte ODBC driver gevonden. "
            f"Beschikbaar: {drivers_txt}"
        )

    server = config.get('sql_server', DEFAULT_CONFIG['sql_server'])
    auth_mode = config.get('sql_auth', 'sql')

    # Bepaal connectie-modes om te proberen
    if auth_mode == 'auto':
        modes = ['sql', 'windows']
    else:
        modes = [auth_mode]

    for mode in modes:
        if mode == 'sql':
            uid = config.get('sql_user', '')
            pwd = config.get('sql_password', '')
            conn_str = (
                f"DRIVER={{{driver}}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"UID={uid};"
                f"PWD={pwd};"
                f"Trusted_Connection=no;"
                f"Connection Timeout=5;"
            )
        else:  # windows
            conn_str = (
                f"DRIVER={{{driver}}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"Trusted_Connection=yes;"
                f"Connection Timeout=5;"
            )

        try:
            conn = pyodbc.connect(conn_str, timeout=5)
            info = f"{mode} auth ({server}, {database})"
            log.info("Verbonden: %s", info)
            return conn, info
        except Exception as e:
            log.debug("Connectie mislukt (%s): %s", mode, e)
            last_error = str(e)
            continue

    return None, (
        f"Geen verbinding mogelijk met {server}/{database}. "
        f"Laatste fout: {last_error}"
    )


# =============================================================================
# UPDATE CHECK & SELF-UPDATE
# =============================================================================

VERSION_FILENAME = 'version.json'


def _read_version_json_with_timeout(share: str, timeout_sec: float = 2.0) -> dict | None:
    """Lees version.json van de UNC share met een threading-based timeout.

    UNC pad-access kan 30+ seconden hangen als de share onbereikbaar is.
    Dit wordt opgelost door het lezen in een aparte thread te doen.

    Returns: dict met versies als het lukt, None als timeout of fout.
    """
    result = [None]
    done = threading.Event()

    def _read():
        try:
            version_file = Path(share) / VERSION_FILENAME
            if not version_file.exists():
                return
            with open(version_file, 'r', encoding='utf-8') as f:
                result[0] = json.load(f)
        except (OSError, PermissionError, json.JSONDecodeError, Exception):
            pass  # Stil falen — geen update beschikbaar
        finally:
            done.set()

    t = threading.Thread(target=_read, daemon=True)
    t.start()
    done.wait(timeout=timeout_sec)
    return result[0]


def check_for_update(tool_name: str, current_version: str) -> dict | None:
    """Check of er een nieuwere versie beschikbaar is op de update share.

    Gebruikt een threading-based timeout zodat de tool binnen 3 seconden
    opstart, ook als de share onbereikbaar is.

    Returns dict met 'remote_version' en 'update_share' als er een update is,
    of None als we al up-to-date zijn of de share niet bereikbaar is.
    """
    config = load_config()
    share = config.get('update_share', '')
    if not share:
        return None

    versions = _read_version_json_with_timeout(share, timeout_sec=2.0)
    if not versions:
        return None  # Share niet bereikbaar of geen version.json

    remote_str = versions.get(tool_name)
    if not remote_str:
        return None

    remote = _parse_version(remote_str)
    current = _parse_version(current_version)

    if remote > current:
        return {
            'remote_version': remote_str,
            'update_share': share,
        }

    return None


def do_self_update(tool_name: str, exe_name: str) -> bool:
    """Voer een self-update uit: kopieer nieuwe exe van share, herstart.

    Stappen:
    1. Kopieer {share}/{exe_name} → {lokaal}/{exe_name}.new
    2. Schrijf _update.bat die de swap doet
    3. Start _update.bat, sluit huidige applicatie

    Returns True als update gestart is (caller moet sys.exit doen),
    False als er iets misging.
    """
    if not getattr(sys, 'frozen', False):
        log.warning("Self-update alleen mogelijk vanuit een exe")
        return False

    config = load_config()
    share = config.get('update_share', '')
    if not share:
        return False

    local_exe = Path(sys.executable)
    remote_exe = Path(share) / exe_name
    new_exe = local_exe.parent / f"{exe_name}.new"
    bat_path = local_exe.parent / '_update.bat'

    try:
        # Stap 1: Kopieer remote exe naar lokaal .new
        if not remote_exe.exists():
            log.error("Remote exe niet gevonden: %s", remote_exe)
            return False

        shutil.copy2(str(remote_exe), str(new_exe))

        # Stap 2: Schrijf update batch script
        # cd /d zorgt dat de working directory klopt, ook als batch elders gestart is.
        # move /y is atomischer dan del + ren: overschrijft het doel in 1 operatie,
        # wat robuuster is als de oude exe nog even gelockt is door het OS.
        bat_content = f"""@echo off
timeout /t 2 /nobreak >nul
cd /d "{local_exe.parent}"
move /y "{new_exe.name}" "{local_exe.name}"
start "" "{local_exe}"
del "%~f0"
"""
        with open(bat_path, 'w', encoding='utf-8') as f:
            f.write(bat_content)

        # Stap 3: Start bat en return True (caller doet sys.exit)
        subprocess.Popen(
            ['cmd', '/c', str(bat_path)],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return True

    except Exception as e:
        log.error("Self-update mislukt: %s", e)
        # Cleanup bij falen
        try:
            new_exe.unlink(missing_ok=True)
            bat_path.unlink(missing_ok=True)
        except Exception:
            pass
        return False


def show_update_dialog(current_version: str, remote_version: str, parent=None) -> bool:
    """Toon een CTk-gestylde update-dialoog.

    Args:
        current_version: Huidige versie van de tool (bv. '1.2.0')
        remote_version:  Beschikbare versie op de share (bv. '1.3.0')
        parent:          Optioneel CTk parent window

    Returns True als de gebruiker op "Updaten" klikt, False bij "Later" of sluiten.
    """
    import customtkinter as ctk  # Lazy import, net als show_settings_dialog

    CLR_SUCCESS = "#16A34A"
    CLR_SUCCESS_HOVER = "#15803D"
    CLR_NEUTRAL = "#6B7280"
    CLR_NEUTRAL_HOVER = "#4B5563"

    font_heading = ("Segoe UI", 16, "bold")
    font_label = ("Segoe UI", 12)
    font_version = ("Consolas", 12)

    clicked = [False]

    if parent:
        dialog = ctk.CTkToplevel(parent)
        dialog.transient(parent)
    else:
        dialog = ctk.CTkToplevel()

    dialog.title("Update beschikbaar")
    dialog.geometry("400x230")
    dialog.resizable(False, False)
    dialog.grab_set()  # Modal

    # Titel
    ctk.CTkLabel(
        dialog,
        text="Update beschikbaar",
        font=font_heading,
        text_color="#1E293B",
    ).pack(pady=(24, 12))

    # Versie informatie
    info_frame = ctk.CTkFrame(dialog, fg_color="#F1F5F9", corner_radius=8)
    info_frame.pack(padx=30, fill="x", pady=(0, 20))

    ctk.CTkLabel(
        info_frame,
        text=f"Huidige versie:   v{current_version}",
        font=font_version,
        text_color="#475569",
        anchor="w",
    ).pack(padx=16, pady=(12, 2), anchor="w")

    ctk.CTkLabel(
        info_frame,
        text=f"Nieuwe versie:    v{remote_version}",
        font=font_version,
        text_color=CLR_SUCCESS,
        anchor="w",
    ).pack(padx=16, pady=(2, 12), anchor="w")

    # Knoppen
    btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    btn_frame.pack(padx=30, fill="x")

    def _update():
        clicked[0] = True
        dialog.destroy()

    def _later():
        dialog.destroy()

    ctk.CTkButton(
        btn_frame,
        text="Updaten",
        font=("Segoe UI", 13, "bold"),
        fg_color=CLR_SUCCESS,
        hover_color=CLR_SUCCESS_HOVER,
        height=36,
        width=120,
        command=_update,
    ).pack(side="right", padx=(10, 0))

    ctk.CTkButton(
        btn_frame,
        text="Later",
        font=font_label,
        fg_color=CLR_NEUTRAL,
        hover_color=CLR_NEUTRAL_HOVER,
        height=36,
        width=100,
        command=_later,
    ).pack(side="right")

    dialog.wait_window()
    return clicked[0]


# =============================================================================
# SETTINGS DIALOOG
# =============================================================================

def show_settings_dialog(parent=None, on_save=None) -> bool:
    """Toon een instellingen-dialoog.

    Args:
        parent: Optioneel parent window (CTk of Tk)
        on_save: Callback na opslaan (ontvangt config dict)

    Returns True als er opgeslagen is, False als geannuleerd.
    """
    import customtkinter as ctk
    import tkinter as tk
    from tkinter import messagebox, filedialog

    config = load_config()
    saved = [False]

    # Dialoog aanmaken
    if parent:
        dialog = ctk.CTkToplevel(parent)
        dialog.transient(parent)
    else:
        dialog = ctk.CTkToplevel()

    dialog.title("Instellingen")
    dialog.geometry("550x580")
    dialog.minsize(500, 520)
    dialog.resizable(True, True)
    dialog.grab_set()  # Modal

    # Fonts
    font_label = ("Segoe UI", 12)
    font_entry = ("Consolas", 12)
    font_heading = ("Segoe UI", 14, "bold")

    # Scrollable content
    scroll = ctk.CTkScrollableFrame(dialog, fg_color="#FFFFFF")
    scroll.pack(fill="both", expand=True, padx=15, pady=(15, 5))

    # --- SQL Server sectie ---
    ctk.CTkLabel(scroll, text="SQL Server", font=font_heading,
                 text_color="#1E293B").pack(anchor="w", pady=(5, 8))

    def _field(parent, label, value, show=None, width=350):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=2)
        ctk.CTkLabel(frame, text=label, font=font_label,
                     text_color="#475569", width=140, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(frame, font=font_entry, width=width)
        if show:
            entry.configure(show=show)
        entry.insert(0, value or '')
        entry.pack(side="left", fill="x", expand=True, padx=(5, 0))
        return entry

    e_server = _field(scroll, "Server:", config.get('sql_server', ''))

    # Auth methode
    auth_frame = ctk.CTkFrame(scroll, fg_color="transparent")
    auth_frame.pack(fill="x", pady=2)
    ctk.CTkLabel(auth_frame, text="Authenticatie:", font=font_label,
                 text_color="#475569", width=140, anchor="w").pack(side="left")
    auth_var = ctk.StringVar(value=config.get('sql_auth', 'sql'))
    for val, txt in [('sql', 'SQL Login'), ('windows', 'Windows'), ('auto', 'Auto')]:
        ctk.CTkRadioButton(
            auth_frame, text=txt, variable=auth_var, value=val,
            font=font_label,
        ).pack(side="left", padx=(5, 15))

    e_user = _field(scroll, "Gebruikersnaam:", config.get('sql_user', ''))
    e_pass = _field(scroll, "Wachtwoord:", config.get('sql_password', ''), show='*')

    # --- Databases sectie ---
    ctk.CTkLabel(scroll, text="Databases", font=font_heading,
                 text_color="#1E293B").pack(anchor="w", pady=(15, 8))

    dbs = config.get('databases', {})
    e_db_speel = _field(scroll, "Speelomgeving:", dbs.get('speel', ''))
    e_db_live = _field(scroll, "Live (productie):", dbs.get('live', ''))

    # --- Paden sectie ---
    ctk.CTkLabel(scroll, text="Paden", font=font_heading,
                 text_color="#1E293B").pack(anchor="w", pady=(15, 8))

    # Output basis met browse knop
    out_frame = ctk.CTkFrame(scroll, fg_color="transparent")
    out_frame.pack(fill="x", pady=2)
    ctk.CTkLabel(out_frame, text="Output basis:", font=font_label,
                 text_color="#475569", width=140, anchor="w").pack(side="left")
    e_output = ctk.CTkEntry(out_frame, font=font_entry)
    e_output.insert(0, config.get('output_basis', '.'))
    e_output.pack(side="left", fill="x", expand=True, padx=(5, 5))

    def _browse_output():
        path = filedialog.askdirectory(title="Kies output map")
        if path:
            e_output.delete(0, "end")
            e_output.insert(0, path)

    ctk.CTkButton(out_frame, text="...", width=35, height=28,
                  command=_browse_output).pack(side="left")

    e_share = _field(scroll, "Update share:", config.get('update_share', ''))

    # --- Actieknoppen ---
    btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    btn_frame.pack(fill="x", padx=15, pady=10)

    def _test_connection():
        """Test de SQL-verbinding met de ingevulde instellingen."""
        test_config = _collect_config()
        for omg in ['speel', 'live']:
            db = test_config['databases'].get(omg)
            if not db:
                continue
            conn, info = get_connection(omg, config=test_config)
            if conn:
                conn.close()
                messagebox.showinfo(
                    "Verbinding OK",
                    f"Verbonden met {omg}: {info}",
                    parent=dialog,
                )
                return
            else:
                messagebox.showerror(
                    "Verbinding mislukt",
                    f"Kan niet verbinden ({omg}):\n\n{info}",
                    parent=dialog,
                )
                return
        messagebox.showwarning("Geen database", "Vul minstens 1 database in.",
                               parent=dialog)

    def _collect_config() -> dict:
        return {
            'sql_server': e_server.get().strip(),
            'sql_auth': auth_var.get(),
            'sql_user': e_user.get().strip(),
            'sql_password': e_pass.get(),
            'databases': {
                'speel': e_db_speel.get().strip(),
                'live': e_db_live.get().strip(),
            },
            'output_basis': e_output.get().strip() or '.',
            'update_share': e_share.get().strip(),
        }

    def _save():
        new_config = _collect_config()
        save_config(new_config)
        saved[0] = True
        if on_save:
            on_save(new_config)
        dialog.destroy()

    def _cancel():
        dialog.destroy()

    ctk.CTkButton(
        btn_frame, text="Test verbinding",
        font=("Segoe UI", 12), fg_color="#6B7280", hover_color="#4B5563",
        height=36, width=140,
        command=_test_connection,
    ).pack(side="left", padx=(0, 10))

    ctk.CTkButton(
        btn_frame, text="Opslaan",
        font=("Segoe UI", 13, "bold"), fg_color="#16A34A", hover_color="#15803D",
        height=36, width=120,
        command=_save,
    ).pack(side="right", padx=(10, 0))

    ctk.CTkButton(
        btn_frame, text="Annuleren",
        font=("Segoe UI", 12), fg_color="#6B7280", hover_color="#4B5563",
        height=36, width=100,
        command=_cancel,
    ).pack(side="right")

    dialog.wait_window()
    return saved[0]
