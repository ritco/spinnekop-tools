"""Productiestructuur — Productiebonnen instellen
Spinnekop BV

Standalone tool om phantom-vlaggen in te stellen op substuklijsten
in RidderIQ. Haalt de boomstructuur op uit SQL Server en toont
een visuele TreeView waar de gebruiker per substuklijst kan
aanduiden of er een productiebon komt.

Phantom AAN  = geen aparte productiebon (onderdelen gaan naar parent)
Phantom UIT  = eigen productiebon (apart produceerbaar)

Gebruik:
  python phantom_tool.py
  productiestructuur.exe
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

import customtkinter as ctk

from app_config import (
    get_connection, load_config, config_exists, show_settings_dialog,
    check_for_update, do_self_update, show_update_dialog,
)


# =============================================================================
# VERSIE
# =============================================================================

__version__ = '1.0.0'


# =============================================================================
# CONFIGURATIE
# =============================================================================

APP_TITLE = "Productiestructuur"

# Kleuren
CLR_PRIMARY = "#1E40AF"
CLR_PRIMARY_HOVER = "#1E3A8A"
CLR_ERROR = "#DC2626"
CLR_SUCCESS = "#16A34A"
CLR_WARNING = "#F59E0B"
CLR_BG = "#FFFFFF"
CLR_SURFACE = "#F8FAFC"
CLR_TEXT = "#1E293B"
CLR_TEXT_MUTED = "#475569"
CLR_PHANTOM = "#94A3B8"       # Grijs: phantom (geen bon)
CLR_PRODUCTIEBON = "#2563EB"  # Blauw: productiebon (niet phantom)
CLR_LEAF = "#6B7280"          # Grijs: leaf items (niet klikbaar)

# Fonts
FONT_HEADING = ("Segoe UI", 18, "bold")
FONT_SUBHEADING = ("Segoe UI", 14, "bold")
FONT_BODY = ("Segoe UI", 12)
FONT_BODY_BOLD = ("Segoe UI", 12, "bold")
FONT_TREE = ("Consolas", 12)
FONT_SMALL = ("Segoe UI", 11)
FONT_MONO = ("Consolas", 11)


# =============================================================================
# BOM TREE OPHALEN UIT SQL
# =============================================================================

def fetch_bom_tree(conn, root_code: str) -> dict | None:
    """Haal de volledige BOM-boom op vanuit een eindproduct.

    Returns een nested dict:
    {
        'code': '000-313-120',
        'description': 'Chassis samenstelling',
        'pk': 12345,
        'level': 0,
        'children_sub': [  # substuklijsten (phantom togglebaar)
            {
                'code': '000-313-118',
                'description': 'Las samenstelling',
                'pk': 12346,
                'pk_detail_sub': 789,  # PK van de substuklijstregel
                'quantity': 1,
                'phantom': True,       # huidige phantom status
                'children_sub': [...],
                'children_art': [...],
            },
        ],
        'children_art': [  # artikelen (leaf, niet togglebaar)
            {'code': '000-400-917', 'description': 'Bout M10', 'quantity': 4},
        ],
    }
    """
    cursor = conn.cursor()

    # Check of root bestaat
    cursor.execute(
        "SELECT PK_R_ASSEMBLY, CODE, DESCRIPTION "
        "FROM R_ASSEMBLY WHERE CODE = ?",
        (root_code,),
    )
    root_row = cursor.fetchone()
    if not root_row:
        return None

    root = {
        'code': root_row.CODE,
        'description': root_row.DESCRIPTION or '',
        'pk': root_row.PK_R_ASSEMBLY,
        'level': 0,
        'children_sub': [],
        'children_art': [],
    }

    _fetch_children(cursor, root, level=0, max_depth=10)
    return root


def _fetch_children(cursor, node: dict, level: int, max_depth: int):
    """Recursief kinderen ophalen voor een assembly node."""
    if level >= max_depth:
        return

    pk = node['pk']

    # Substuklijsten ophalen
    cursor.execute(
        "SELECT "
        "  ds.PK_R_ASSEMBLYDETAILSUBASSEMBLY, "
        "  ds.FK_SUBASSEMBLY, "
        "  ds.QUANTITY, "
        "  ds.PHANTOM, "
        "  sub_a.CODE, "
        "  sub_a.DESCRIPTION, "
        "  sub_a.PK_R_ASSEMBLY "
        "FROM R_ASSEMBLYDETAILSUBASSEMBLY ds "
        "JOIN R_ASSEMBLY sub_a ON ds.FK_SUBASSEMBLY = sub_a.PK_R_ASSEMBLY "
        "WHERE ds.FK_ASSEMBLY = ? "
        "ORDER BY ds.POSITION, sub_a.CODE",
        (pk,),
    )

    for row in cursor.fetchall():
        child = {
            'code': row.CODE,
            'description': row.DESCRIPTION or '',
            'pk': row.PK_R_ASSEMBLY,
            'pk_detail_sub': row.PK_R_ASSEMBLYDETAILSUBASSEMBLY,
            'quantity': row.QUANTITY or 1,
            'phantom': bool(row.PHANTOM),
            'level': level + 1,
            'children_sub': [],
            'children_art': [],
        }
        node['children_sub'].append(child)
        _fetch_children(cursor, child, level + 1, max_depth)

    # Artikelen (leaf items) ophalen
    cursor.execute(
        "SELECT "
        "  i.CODE, "
        "  i.DESCRIPTION, "
        "  di.QUANTITY "
        "FROM R_ASSEMBLYDETAILITEM di "
        "JOIN R_ITEM i ON di.FK_ITEM = i.PK_R_ITEM "
        "WHERE di.FK_ASSEMBLY = ? "
        "ORDER BY i.CODE",
        (pk,),
    )

    for row in cursor.fetchall():
        node['children_art'].append({
            'code': row.CODE,
            'description': row.DESCRIPTION or '',
            'quantity': row.QUANTITY or 1,
        })


# =============================================================================
# PHANTOM SCHRIJVEN NAAR SQL
# =============================================================================

def apply_phantom_changes(conn, changes: list[dict]) -> dict:
    """Schrijf phantom-wijzigingen naar de database.

    changes: lijst van {'pk_detail_sub': int, 'phantom': bool}

    Returns: {'n_updated': int, 'fouten': list[str]}

    """
    cursor = conn.cursor()
    n_updated = 0
    fouten = []

    PHANTOM_COLUMN = 'PHANTOM'

    for change in changes:
        pk = change['pk_detail_sub']
        phantom_val = 1 if change['phantom'] else 0
        try:
            cursor.execute(
                f"UPDATE R_ASSEMBLYDETAILSUBASSEMBLY "
                f"SET {PHANTOM_COLUMN} = ?, "
                f"    DATECHANGED = GETDATE(), "
                f"    USERCHANGED = 'Productiestructuur' "
                f"WHERE PK_R_ASSEMBLYDETAILSUBASSEMBLY = ?",
                (phantom_val, pk),
            )
            n_updated += 1
        except Exception as e:
            fouten.append(f"PK {pk}: {e}")

    if fouten:
        conn.rollback()
    else:
        conn.commit()

    return {'n_updated': n_updated, 'fouten': fouten}


# =============================================================================
# TREE STATISTIEKEN
# =============================================================================

def count_tree_stats(tree: dict) -> dict:
    """Tel statistieken van de boom."""
    stats = {
        'n_assemblies': 0,
        'n_articles': 0,
        'n_phantom': 0,
        'n_productiebon': 0,
        'depth': 0,
    }
    _count_recursive(tree, stats, 0)
    return stats


def _count_recursive(node: dict, stats: dict, depth: int):
    """Recursief tellen."""
    stats['n_assemblies'] += 1
    stats['depth'] = max(stats['depth'], depth)
    stats['n_articles'] += len(node.get('children_art', []))

    for child in node.get('children_sub', []):
        if child.get('phantom', True):
            stats['n_phantom'] += 1
        else:
            stats['n_productiebon'] += 1
        _count_recursive(child, stats, depth + 1)


# =============================================================================
# GUI — TREEVIEW FRAME
# =============================================================================

class BomTreeView(ctk.CTkFrame):
    """Boomstructuur met phantom-toggles."""

    def __init__(self, master, on_change=None):
        super().__init__(master, fg_color=CLR_BG)
        self.on_change = on_change
        self.tree_data = None
        self.node_map = {}  # tree_id -> node dict

        # Treeview met ttk (customtkinter heeft geen TreeView)
        style = ttk.Style()
        style.configure(
            "Bom.Treeview",
            font=FONT_TREE,
            rowheight=28,
        )
        style.configure(
            "Bom.Treeview.Heading",
            font=FONT_BODY_BOLD,
        )

        # Frame voor tree + scrollbar
        tree_frame = ctk.CTkFrame(self, fg_color=CLR_BG)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        # TreeView
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("type", "qty", "status"),
            style="Bom.Treeview",
            selectmode="browse",
            yscrollcommand=scrollbar.set,
        )
        scrollbar.config(command=self.tree.yview)

        self.tree.heading("#0", text="Artikel / Stuklijst", anchor="w")
        self.tree.heading("type", text="Type", anchor="w")
        self.tree.heading("qty", text="Aantal", anchor="e")
        self.tree.heading("status", text="Status", anchor="w")

        self.tree.column("#0", width=400, minwidth=250)
        self.tree.column("type", width=80, minwidth=60)
        self.tree.column("qty", width=60, minwidth=40, anchor="e")
        self.tree.column("status", width=140, minwidth=100)

        self.tree.pack(fill="both", expand=True)

        # Tags voor kleuren
        self.tree.tag_configure("phantom",
                                foreground=CLR_PHANTOM)
        self.tree.tag_configure("productiebon",
                                foreground=CLR_PRODUCTIEBON,
                                font=("Consolas", 12, "bold"))
        self.tree.tag_configure("leaf",
                                foreground=CLR_LEAF)
        self.tree.tag_configure("root",
                                font=("Consolas", 13, "bold"))

        # Klik op status-kolom om phantom te togglen
        self.tree.bind("<ButtonRelease-1>", self._on_click)
        # Spatiebalk ook
        self.tree.bind("<space>", self._on_space)

    def load_tree(self, tree_data: dict):
        """Laad een BOM-boom in de TreeView."""
        self.tree_data = tree_data
        self.node_map.clear()

        # Bestaande items verwijderen
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Root toevoegen
        root_text = f"{tree_data['code']}  —  {tree_data['description']}"
        root_id = self.tree.insert(
            "", "end",
            text=root_text,
            values=("EIND", "", "Eindproduct"),
            tags=("root",),
            open=True,
        )
        self.node_map[root_id] = tree_data

        # Kinderen recursief toevoegen
        self._add_children(root_id, tree_data)

    def _add_children(self, parent_id: str, node: dict):
        """Recursief kinderen toevoegen aan de tree."""
        # Eerst substuklijsten (togglebaar)
        for child in node.get('children_sub', []):
            phantom = child.get('phantom', True)
            status = "Phantom (geen bon)" if phantom else "PRODUCTIEBON"
            tag = "phantom" if phantom else "productiebon"

            qty_str = str(int(child['quantity'])) if child['quantity'] == int(child['quantity']) else str(child['quantity'])
            text = f"{child['code']}  —  {child['description']}"

            child_id = self.tree.insert(
                parent_id, "end",
                text=text,
                values=("SUB", qty_str, status),
                tags=(tag,),
                open=True,  # Alles open voor overzicht
            )
            self.node_map[child_id] = child
            self._add_children(child_id, child)

        # Dan artikelen (leaf, niet togglebaar)
        for art in node.get('children_art', []):
            qty_str = str(int(art['quantity'])) if art['quantity'] == int(art['quantity']) else str(art['quantity'])
            text = f"{art['code']}  —  {art['description']}"

            art_id = self.tree.insert(
                parent_id, "end",
                text=text,
                values=("ART", qty_str, ""),
                tags=("leaf",),
            )

    def _on_click(self, event):
        """Toggle phantom bij klik op de status-kolom."""
        region = self.tree.identify_region(event.x, event.y)
        column = self.tree.identify_column(event.x)
        if region == "cell" and column == "#3":  # status kolom
            self._toggle_selected()

    def _on_space(self, event):
        """Toggle phantom bij spatiebalk."""
        self._toggle_selected()

    def _toggle_selected(self):
        """Toggle phantom status van geselecteerd item."""
        selection = self.tree.selection()
        if not selection:
            return

        item_id = selection[0]
        node = self.node_map.get(item_id)
        if not node or 'phantom' not in node:
            return  # Geen substuklijst, niet togglebaar

        # Toggle
        node['phantom'] = not node['phantom']

        # UI bijwerken
        phantom = node['phantom']
        status = "Phantom (geen bon)" if phantom else "PRODUCTIEBON"
        tag = "phantom" if phantom else "productiebon"

        self.tree.item(item_id, values=(
            self.tree.item(item_id, "values")[0],
            self.tree.item(item_id, "values")[1],
            status,
        ), tags=(tag,))

        if self.on_change:
            self.on_change()


# =============================================================================
# GUI — HOOFDVENSTER
# =============================================================================

class PhantomApp(ctk.CTk):
    """Phantom Tool hoofdapplicatie."""

    def __init__(self):
        super().__init__()

        self.geometry("1100x750")
        self.minsize(900, 600)
        self.title(f"{APP_TITLE} v{__version__}")

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.conn = None
        self.conn_info = ""
        self.tree_data = None
        self.original_states = {}  # pk_detail_sub -> phantom (oorspronkelijk)

        self._build_ui()

        # Eerste keer? Toon settings dialoog
        if not config_exists():
            self.after(100, lambda: show_settings_dialog(parent=self))

    def _build_ui(self):
        """Bouw de UI op."""
        # Header
        header = ctk.CTkFrame(self, fg_color=CLR_PRIMARY, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, text=APP_TITLE,
            font=FONT_HEADING, text_color="white",
        ).pack(pady=(15, 3))
        ctk.CTkLabel(
            header, text=f"v{__version__}  |  Klik op status of spatiebalk om productiebon te togglen",
            font=FONT_SMALL, text_color="#93C5FD",
        ).pack(pady=(0, 12))

        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color=CLR_SURFACE)
        toolbar.pack(fill="x", padx=15, pady=(10, 0))

        # Omgeving
        ctk.CTkLabel(
            toolbar, text="Omgeving:",
            font=FONT_BODY, text_color=CLR_TEXT,
        ).pack(side="left", padx=(10, 5), pady=8)

        self.omgeving_var = ctk.StringVar(value="speel")
        ctk.CTkRadioButton(
            toolbar, text="Speel", variable=self.omgeving_var, value="speel",
            font=FONT_BODY, fg_color=CLR_PRIMARY,
        ).pack(side="left", padx=(0, 10), pady=8)
        ctk.CTkRadioButton(
            toolbar, text="Live", variable=self.omgeving_var, value="live",
            font=FONT_BODY, fg_color=CLR_ERROR,
        ).pack(side="left", padx=(0, 20), pady=8)

        # Artikelcode invoer
        ctk.CTkLabel(
            toolbar, text="Eindproduct:",
            font=FONT_BODY, text_color=CLR_TEXT,
        ).pack(side="left", padx=(10, 5), pady=8)

        self.code_entry = ctk.CTkEntry(
            toolbar, width=200, font=FONT_MONO,
            placeholder_text="bv. 000-313-120",
        )
        self.code_entry.pack(side="left", padx=(0, 10), pady=8)
        self.code_entry.bind("<Return>", lambda e: self._load_tree())

        ctk.CTkButton(
            toolbar, text="Ophalen",
            font=FONT_BODY_BOLD,
            fg_color=CLR_PRIMARY, hover_color=CLR_PRIMARY_HOVER,
            width=100, height=32,
            command=self._load_tree,
        ).pack(side="left", padx=(0, 10), pady=8)

        # Snelknoppen
        sep = ctk.CTkFrame(toolbar, fg_color="#CBD5E1", width=1)
        sep.pack(side="left", fill="y", padx=10, pady=6)

        ctk.CTkButton(
            toolbar, text="Alles phantom",
            font=FONT_SMALL, fg_color=CLR_PHANTOM,
            hover_color="#64748B", width=110, height=28,
            command=self._set_all_phantom,
        ).pack(side="left", padx=(0, 5), pady=8)

        ctk.CTkButton(
            toolbar, text="Alles productiebon",
            font=FONT_SMALL, fg_color=CLR_PRODUCTIEBON,
            hover_color="#1D4ED8", width=130, height=28,
            command=self._set_all_productiebon,
        ).pack(side="left", padx=(0, 10), pady=8)

        # Instellingen knop
        ctk.CTkButton(
            toolbar, text="\u2699",
            font=("Segoe UI", 16), fg_color="#6B7280",
            hover_color="#4B5563", width=32, height=28,
            command=self._open_settings,
        ).pack(side="right", padx=(0, 10), pady=8)

        # Connectiestatus
        self.conn_label = ctk.CTkLabel(
            toolbar, text="Niet verbonden",
            font=FONT_SMALL, text_color=CLR_TEXT_MUTED,
        )
        self.conn_label.pack(side="right", padx=10, pady=8)

        # Statistieken balk
        self.stats_frame = ctk.CTkFrame(self, fg_color=CLR_SURFACE)
        self.stats_frame.pack(fill="x", padx=15, pady=(5, 0))

        self.stats_label = ctk.CTkLabel(
            self.stats_frame, text="Laad een eindproduct om te beginnen",
            font=FONT_BODY, text_color=CLR_TEXT_MUTED,
        )
        self.stats_label.pack(side="left", padx=10, pady=6)

        self.changes_label = ctk.CTkLabel(
            self.stats_frame, text="",
            font=FONT_BODY_BOLD, text_color=CLR_WARNING,
        )
        self.changes_label.pack(side="right", padx=10, pady=6)

        # TreeView
        self.bom_tree = BomTreeView(self, on_change=self._update_stats)
        self.bom_tree.pack(fill="both", expand=True, padx=15, pady=5)

        # Actieknoppen onderaan
        action_frame = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0)
        action_frame.pack(fill="x", side="bottom")

        btn_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
        btn_frame.pack(pady=10, padx=20)

        self.btn_apply = ctk.CTkButton(
            btn_frame, text="Wijzigingen toepassen",
            font=("Segoe UI", 14, "bold"),
            fg_color=CLR_SUCCESS, hover_color="#15803D",
            height=42, width=220, corner_radius=8,
            state="disabled",
            command=self._apply_changes,
        )
        self.btn_apply.pack(side="left", padx=(0, 15))

        ctk.CTkButton(
            btn_frame, text="Sluiten",
            font=FONT_BODY,
            fg_color="#6B7280", hover_color="#4B5563",
            height=42, width=100, corner_radius=8,
            command=self.destroy,
        ).pack(side="left")

        # Footer
        footer = ctk.CTkFrame(self, fg_color=CLR_BG, corner_radius=0)
        footer.pack(fill="x", side="bottom")
        user = os.getlogin()
        ctk.CTkLabel(
            footer,
            text=f"Gebruiker: {user}",
            font=FONT_SMALL, text_color=CLR_TEXT_MUTED,
        ).pack(pady=4)

    # ----- Acties -----

    def _open_settings(self):
        """Open het instellingen-dialoog."""
        def _on_save(config):
            # Reset connectie zodat nieuwe instellingen gebruikt worden
            self.conn = None
            self.conn_info = ""
            self.conn_label.configure(
                text="Instellingen gewijzigd — herverbind",
                text_color=CLR_WARNING,
            )
        show_settings_dialog(parent=self, on_save=_on_save)

    def _ensure_connection(self) -> bool:
        """Zorg voor een actieve SQL-verbinding."""
        if self.conn:
            try:
                # Test of connectie nog leeft
                self.conn.cursor().execute("SELECT 1")
                return True
            except Exception:
                self.conn = None

        omgeving = self.omgeving_var.get()
        self.conn, self.conn_info = get_connection(omgeving)
        if self.conn:
            self.conn_label.configure(
                text=f"Verbonden: {self.conn_info}",
                text_color=CLR_SUCCESS,
            )
            return True
        else:
            self.conn_label.configure(
                text=f"Fout: {self.conn_info}",
                text_color=CLR_ERROR,
            )
            messagebox.showerror(
                "Geen verbinding",
                f"Kan niet verbinden met RidderIQ:\n\n{self.conn_info}",
            )
            return False

    def _load_tree(self):
        """Laad de boomstructuur vanuit SQL."""
        code = self.code_entry.get().strip()
        if not code:
            messagebox.showwarning("Invoer", "Vul een artikelcode in.")
            return

        if not self._ensure_connection():
            return

        self.configure(cursor="wait")
        self.update()

        try:
            self.tree_data = fetch_bom_tree(self.conn, code)

            if not self.tree_data:
                messagebox.showwarning(
                    "Niet gevonden",
                    f"Stuklijst '{code}' niet gevonden in de database.\n\n"
                    f"Controleer de artikelcode en de gekozen omgeving.",
                )
                return

            # Originele states opslaan (voor change detection)
            self.original_states.clear()
            self._save_original_states(self.tree_data)

            # TreeView laden
            self.bom_tree.load_tree(self.tree_data)
            self._update_stats()

            self.title(
                f"{APP_TITLE} v{__version__} — {code}"
            )

        except Exception as e:
            messagebox.showerror("Fout", f"Fout bij ophalen:\n\n{e}")
        finally:
            self.configure(cursor="")

    def _save_original_states(self, node: dict):
        """Bewaar originele phantom-states voor change detection."""
        for child in node.get('children_sub', []):
            pk = child.get('pk_detail_sub')
            if pk:
                self.original_states[pk] = child.get('phantom', True)
            self._save_original_states(child)

    def _get_changes(self) -> list[dict]:
        """Vind alle gewijzigde phantom-states."""
        changes = []
        if self.tree_data:
            self._collect_changes(self.tree_data, changes)
        return changes

    def _collect_changes(self, node: dict, changes: list):
        """Recursief wijzigingen verzamelen."""
        for child in node.get('children_sub', []):
            pk = child.get('pk_detail_sub')
            if pk and pk in self.original_states:
                original = self.original_states[pk]
                current = child.get('phantom', True)
                if original != current:
                    changes.append({
                        'pk_detail_sub': pk,
                        'phantom': current,
                        'code': child['code'],
                    })
            self._collect_changes(child, changes)

    def _update_stats(self):
        """Update statistieken na wijziging."""
        if not self.tree_data:
            return

        stats = count_tree_stats(self.tree_data)
        changes = self._get_changes()

        self.stats_label.configure(
            text=(
                f"Assemblies: {stats['n_assemblies']}  |  "
                f"Artikelen: {stats['n_articles']}  |  "
                f"Phantom: {stats['n_phantom']}  |  "
                f"Productiebonnen: {stats['n_productiebon']}  |  "
                f"Diepte: {stats['depth']}"
            ),
            text_color=CLR_TEXT,
        )

        if changes:
            self.changes_label.configure(
                text=f"{len(changes)} wijziging(en) nog niet opgeslagen",
            )
            self.btn_apply.configure(state="normal")
        else:
            self.changes_label.configure(text="")
            self.btn_apply.configure(state="disabled")

    def _set_all_phantom(self):
        """Zet alle substuklijsten op phantom."""
        if self.tree_data:
            self._set_phantom_recursive(self.tree_data, True)
            self.bom_tree.load_tree(self.tree_data)
            self._update_stats()

    def _set_all_productiebon(self):
        """Zet alle substuklijsten op productiebon (niet phantom)."""
        if self.tree_data:
            self._set_phantom_recursive(self.tree_data, False)
            self.bom_tree.load_tree(self.tree_data)
            self._update_stats()

    def _set_phantom_recursive(self, node: dict, phantom: bool):
        """Recursief phantom zetten."""
        for child in node.get('children_sub', []):
            child['phantom'] = phantom
            self._set_phantom_recursive(child, phantom)

    def _apply_changes(self):
        """Pas phantom-wijzigingen toe in de database."""
        changes = self._get_changes()
        if not changes:
            return

        # Bevestiging
        lines = []
        for c in changes[:15]:
            status = "phantom" if c['phantom'] else "PRODUCTIEBON"
            lines.append(f"  {c['code']} → {status}")
        if len(changes) > 15:
            lines.append(f"  ... en {len(changes) - 15} meer")

        ok = messagebox.askyesno(
            "Wijzigingen toepassen",
            f"{len(changes)} wijziging(en) doorvoeren?\n\n"
            + "\n".join(lines)
            + "\n\nDit past de phantom-vlaggen aan in de database.",
        )
        if not ok:
            return

        if not self._ensure_connection():
            return

        result = apply_phantom_changes(self.conn, changes)

        if result['fouten']:
            messagebox.showerror(
                "Fouten bij toepassen",
                f"{result['n_updated']} gelukt, "
                f"{len(result['fouten'])} fout(en):\n\n"
                + "\n".join(result['fouten'][:10]),
            )
        else:
            messagebox.showinfo(
                "Gelukt",
                f"{result['n_updated']} phantom-vlaggen bijgewerkt.",
            )
            # Originele states bijwerken
            self.original_states.clear()
            self._save_original_states(self.tree_data)
            self._update_stats()


# =============================================================================
# MAIN
# =============================================================================

def _check_update_before_gui() -> dict | None:
    """Check voor updates op de network share (voor de GUI start).
    Returns update info dict als er een update is, None anders.
    """
    try:
        update = check_for_update('productiestructuur', __version__)
        if update:
            return update
        return None
    except Exception:
        return None


def _show_update_after_gui(app, remote_version, resolved_share):
    """Toon update dialog met de App als parent (na mainloop start)."""
    try:
        ok = show_update_dialog(__version__, remote_version, parent=app)
        if ok and do_self_update('productiestructuur', 'productiestructuur.exe',
                                 share_override=resolved_share):
            app.destroy()
            sys.exit(0)
    except Exception:
        pass


def main():
    update_info = _check_update_before_gui()
    app = PhantomApp()
    if update_info:
        try:
            app.after(100, lambda: _show_update_after_gui(
                app, update_info['remote_version'], update_info['update_share']))
        except Exception:
            pass
    app.mainloop()


if __name__ == '__main__':
    main()
