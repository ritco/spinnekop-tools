"""BOM Import Tool — GUI
Spinnekop BV

Desktop applicatie voor het valideren en importeren van SolidWorks BOM
exports naar RidderIQ ERP.

Architectuur:
  StartFrame    → bestand openen, omgeving kiezen, recente imports
  AnalysisFrame → validatieresultaten, goedkeuring, CSV genereren
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from datetime import datetime

import customtkinter as ctk

from bom_converter import (
    parse_bom, print_summary, collect_parent_numbers,
    generate_artikelen, generate_stuklijst_headers,
    generate_stuklijstregels, generate_substuklijsten,
    generate_bewerkingen, generate_kmb_artikel_bewerking,
    generate_kmb_substuklijst_bewerking,
    STAP_VOLGORDE, STAP_BESTANDEN, STAP_GENERATORS,
    archive_existing,
)
from validation_engine import (
    validate_all, has_errors, count_by_severity, ValidationResult,
    DEFAULT_RULES,
)
from sql_validator import get_sql_rules
from history import log_import, get_recent_display
from main import __version__


# =============================================================================
# CONFIGURATIE
# =============================================================================

APP_TITLE = "BOM Import Tool — Spinnekop"
APP_VERSION = __version__
DEFAULT_BASIS = r'C:\import'

# Kleuren (uit analyse/design)
CLR_PRIMARY = "#1E40AF"       # Blauw
CLR_PRIMARY_HOVER = "#1E3A8A"
CLR_ERROR = "#DC2626"         # Rood
CLR_ERROR_BG = "#FEE2E2"
CLR_WARNING = "#F59E0B"       # Amber
CLR_WARNING_BG = "#FEF3C7"
CLR_SUCCESS = "#16A34A"       # Groen
CLR_SUCCESS_BG = "#F0FDF4"
CLR_INFO = "#6B7280"          # Grijs
CLR_INFO_BG = "#F3F4F6"
CLR_BG = "#FFFFFF"
CLR_SURFACE = "#F8FAFC"
CLR_TEXT = "#1E293B"
CLR_TEXT_MUTED = "#475569"
CLR_ACTIE = "#1D4ED8"           # Blauw voor actie-aanwijzingen

# Fonts — groter dan standaard voor leesbaarheid
FONT_HEADING = ("Segoe UI", 20, "bold")
FONT_SUBHEADING = ("Segoe UI", 15, "bold")
FONT_BODY = ("Segoe UI", 13)
FONT_BODY_BOLD = ("Segoe UI", 13, "bold")
FONT_DETAIL = ("Segoe UI", 12)
FONT_SMALL = ("Segoe UI", 11)
FONT_MONO = ("Consolas", 12)
FONT_MONO_SMALL = ("Consolas", 11)
FONT_ACTIE = ("Segoe UI", 12, "italic")


# =============================================================================
# STARTFRAME
# =============================================================================

class StartFrame(ctk.CTkFrame):
    """Startscherm: bestand openen, omgeving kiezen."""

    def __init__(self, master, on_file_selected, on_env_changed=None):
        super().__init__(master, fg_color=CLR_BG)
        self.on_file_selected = on_file_selected
        self.on_env_changed = on_env_changed

        # Header
        header = ctk.CTkFrame(self, fg_color=CLR_PRIMARY, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, text=APP_TITLE,
            font=FONT_HEADING, text_color="white",
        ).pack(pady=20)
        ctk.CTkLabel(
            header, text=f"v{APP_VERSION}",
            font=FONT_SMALL, text_color="#93C5FD",
        ).pack(pady=(0, 15))

        # Main content
        content = ctk.CTkFrame(self, fg_color=CLR_BG)
        content.pack(expand=True, fill="both", padx=40, pady=30)

        # Omgeving keuze
        env_frame = ctk.CTkFrame(content, fg_color=CLR_SURFACE, corner_radius=8)
        env_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(
            env_frame, text="Omgeving",
            font=FONT_SUBHEADING, text_color=CLR_TEXT,
        ).pack(anchor="w", padx=15, pady=(15, 5))

        self.omgeving_var = ctk.StringVar(value="speel")
        if on_env_changed:
            self.omgeving_var.trace_add("write", lambda *_: on_env_changed(self.omgeving_var.get()))
        radio_frame = ctk.CTkFrame(env_frame, fg_color="transparent")
        radio_frame.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkRadioButton(
            radio_frame, text="Speelomgeving",
            variable=self.omgeving_var, value="speel",
            font=FONT_BODY, text_color=CLR_TEXT,
            fg_color=CLR_PRIMARY, hover_color=CLR_PRIMARY_HOVER,
        ).pack(side="left", padx=(0, 30))
        ctk.CTkRadioButton(
            radio_frame, text="Live (productie)",
            variable=self.omgeving_var, value="live",
            font=FONT_BODY, text_color=CLR_TEXT,
            fg_color=CLR_ERROR, hover_color="#B91C1C",
        ).pack(side="left")

        # Open bestand knop
        ctk.CTkButton(
            content, text="Open BOM Excel",
            font=("Segoe UI", 16, "bold"),
            fg_color=CLR_PRIMARY, hover_color=CLR_PRIMARY_HOVER,
            height=50, corner_radius=8,
            command=self._open_file,
        ).pack(fill="x", pady=(10, 0))

        # Drag & drop hint
        ctk.CTkLabel(
            content,
            text="Ondersteunde formaten: .xls (V2) en .xlsx (V1)",
            font=FONT_SMALL, text_color=CLR_TEXT_MUTED,
        ).pack(pady=(10, 0))

        # Recente imports placeholder
        recent_frame = ctk.CTkFrame(content, fg_color=CLR_SURFACE, corner_radius=8)
        recent_frame.pack(fill="both", expand=True, pady=(20, 0))
        ctk.CTkLabel(
            recent_frame, text="Recente imports",
            font=FONT_SUBHEADING, text_color=CLR_TEXT,
        ).pack(anchor="w", padx=15, pady=(15, 5))
        self.recent_list = ctk.CTkLabel(
            recent_frame,
            text="Nog geen imports uitgevoerd",
            font=FONT_SMALL, text_color=CLR_TEXT_MUTED,
        )
        self.recent_list.pack(padx=15, pady=(0, 15))

        # Footer
        footer = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0)
        footer.pack(fill="x", side="bottom")
        user = os.getlogin()
        ctk.CTkLabel(
            footer,
            text=f"Gebruiker: {user}  |  Basis: {DEFAULT_BASIS}",
            font=FONT_SMALL, text_color=CLR_TEXT_MUTED,
        ).pack(pady=8)

    def _open_file(self):
        path = filedialog.askopenfilename(
            title="Selecteer SolidWorks BOM Excel",
            filetypes=[
                ("Excel bestanden", "*.xls *.xlsx"),
                ("Alle bestanden", "*.*"),
            ],
        )
        if path:
            self.on_file_selected(path, self.omgeving_var.get())

    def update_recent(self, history_items: list):
        """Update de lijst met recente imports."""
        if not history_items:
            self.recent_list.configure(text="Nog geen imports uitgevoerd")
            return

        lines = []
        for item in history_items[:8]:
            lines.append(
                f"{item.get('datum', '?')}  |  "
                f"{item.get('gebruiker', '?')}  |  "
                f"{item.get('bestand', '?')}  |  "
                f"{item.get('omgeving', '?')}  |  "
                f"{item.get('status', '?')}"
            )
        self.recent_list.configure(text="\n".join(lines))


# =============================================================================
# ANALYSISFRAME
# =============================================================================

class AnalysisFrame(ctk.CTkFrame):
    """Analysescherm: validatieresultaten, goedkeuring, CSV genereren."""

    def __init__(self, master, on_back, on_generate):
        super().__init__(master, fg_color=CLR_BG)
        self.on_back = on_back
        self.on_generate = on_generate
        self.results = []
        self.bom_rows = []
        self.excel_path = ""
        self.omgeving = ""

        # Header bar
        self.header_bar = ctk.CTkFrame(self, fg_color=CLR_PRIMARY, corner_radius=0)
        self.header_bar.pack(fill="x")

        header_content = ctk.CTkFrame(self.header_bar, fg_color="transparent")
        header_content.pack(fill="x", padx=20, pady=12)

        ctk.CTkButton(
            header_content, text="< Terug",
            font=FONT_BODY, text_color="white",
            fg_color="transparent", hover_color=CLR_PRIMARY_HOVER,
            width=80, command=on_back,
        ).pack(side="left")

        self.header_label = ctk.CTkLabel(
            header_content, text="Analyse",
            font=FONT_HEADING, text_color="white",
        )
        self.header_label.pack(side="left", padx=20)

        # Samenvatting kaarten
        self.summary_frame = ctk.CTkFrame(self, fg_color=CLR_SURFACE)
        self.summary_frame.pack(fill="x", padx=20, pady=(15, 0))

        self.summary_cards = ctk.CTkFrame(self.summary_frame, fg_color="transparent")
        self.summary_cards.pack(fill="x", padx=15, pady=12)

        self.card_artikelen = self._make_card(self.summary_cards, "Artikelen", "0")
        self.card_stuklijsten = self._make_card(self.summary_cards, "Stuklijsten", "0")
        self.card_zaagregels = self._make_card(self.summary_cards, "Zaagregels", "0")
        self.card_fouten = self._make_card(self.summary_cards, "Fouten", "0",
                                           accent=CLR_ERROR)
        self.card_warnings = self._make_card(self.summary_cards, "Waarsch.", "0",
                                             accent=CLR_WARNING)

        # Status indicatie
        self.status_bar = ctk.CTkFrame(self, fg_color=CLR_SUCCESS_BG, corner_radius=0)
        self.status_bar.pack(fill="x", padx=20, pady=(10, 0))
        self.status_label = ctk.CTkLabel(
            self.status_bar, text="",
            font=FONT_BODY, text_color=CLR_SUCCESS,
        )
        self.status_label.pack(pady=8)

        # Validatieresultaten lijst
        results_header = ctk.CTkFrame(self, fg_color="transparent")
        results_header.pack(fill="x", padx=20, pady=(10, 0))
        ctk.CTkLabel(
            results_header, text="Validatieresultaten",
            font=FONT_SUBHEADING, text_color=CLR_TEXT,
        ).pack(side="left")

        self.results_scroll = ctk.CTkScrollableFrame(
            self, fg_color=CLR_BG, corner_radius=0,
        )
        self.results_scroll.pack(fill="both", expand=True, padx=20, pady=(5, 0))

        # Actieknoppen onderaan
        action_frame = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=0)
        action_frame.pack(fill="x", side="bottom")

        btn_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
        btn_frame.pack(pady=12, padx=20)

        self.btn_generate = ctk.CTkButton(
            btn_frame, text="CSV Genereren",
            font=("Segoe UI", 14, "bold"),
            fg_color=CLR_SUCCESS, hover_color="#15803D",
            height=44, width=200, corner_radius=8,
            command=self._do_generate,
        )
        self.btn_generate.pack(side="left", padx=(0, 15))

        ctk.CTkButton(
            btn_frame, text="Annuleren",
            font=FONT_BODY,
            fg_color=CLR_INFO, hover_color="#4B5563",
            height=44, width=120, corner_radius=8,
            command=on_back,
        ).pack(side="left")

        self.generate_info = ctk.CTkLabel(
            action_frame, text="", font=FONT_SMALL,
            text_color=CLR_TEXT_MUTED,
        )
        self.generate_info.pack(pady=(0, 8))

    def _make_card(self, parent, label, value, accent=CLR_PRIMARY):
        """Maak een samenvattingskaart."""
        card = ctk.CTkFrame(parent, fg_color=CLR_BG, corner_radius=8,
                            border_width=1, border_color="#E2E8F0")
        card.pack(side="left", expand=True, fill="x", padx=4)

        val_label = ctk.CTkLabel(
            card, text=value, font=("Segoe UI", 22, "bold"),
            text_color=accent,
        )
        val_label.pack(pady=(10, 0))
        ctk.CTkLabel(
            card, text=label, font=FONT_SMALL,
            text_color=CLR_TEXT_MUTED,
        ).pack(pady=(0, 10))

        return val_label

    def show_results(self, excel_path, omgeving, bom_rows, results):
        """Toon de validatieresultaten voor een geladen Excel."""
        self.excel_path = excel_path
        self.omgeving = omgeving
        self.bom_rows = bom_rows
        self.results = results

        filename = Path(excel_path).name
        self.header_label.configure(text=f"Analyse: {filename}")

        # Samenvattingskaarten updaten
        n_artikel = sum(1 for r in bom_rows if r.row_type == 'artikel')
        n_zaag = sum(1 for r in bom_rows if r.row_type == 'zaagregel')
        parent_numbers = collect_parent_numbers(bom_rows)

        counts = count_by_severity(results)

        self.card_artikelen.configure(text=str(n_artikel))
        self.card_stuklijsten.configure(text=str(len(parent_numbers)))
        self.card_zaagregels.configure(text=str(n_zaag))
        self.card_fouten.configure(text=str(counts['error']))
        self.card_warnings.configure(text=str(counts['warning']))

        # Status bar
        if counts['error'] > 0:
            self.status_bar.configure(fg_color=CLR_ERROR_BG)
            self.status_label.configure(
                text=f"{counts['error']} fout(en) gevonden — "
                     f"CSV genereren is geblokkeerd. "
                     f"Los eerst de fouten op in de Excel.",
                text_color=CLR_ERROR,
            )
            self.btn_generate.configure(state="disabled", fg_color=CLR_INFO)
            self.generate_info.configure(
                text="Pas de Excel aan en open het bestand opnieuw"
            )
        elif counts['warning'] > 0:
            self.status_bar.configure(fg_color=CLR_WARNING_BG)
            self.status_label.configure(
                text=f"Geen fouten, maar {counts['warning']} "
                     f"waarschuwing(en). Bekijk de meldingen "
                     f"hieronder voor je verder gaat.",
                text_color="#92400E",
            )
            self.btn_generate.configure(
                state="normal", fg_color=CLR_SUCCESS,
                text=f"CSV Genereren ({counts['warning']} waarsch.)",
            )
            self.generate_info.configure(
                text=f"Omgeving: {omgeving.upper()} | "
                     f"Gebruiker: {os.getlogin()}"
            )
        else:
            self.status_bar.configure(fg_color=CLR_SUCCESS_BG)
            self.status_label.configure(
                text="Alles OK — geen fouten of waarschuwingen",
                text_color=CLR_SUCCESS,
            )
            self.btn_generate.configure(
                state="normal", fg_color=CLR_SUCCESS,
                text="CSV Genereren",
            )
            self.generate_info.configure(
                text=f"Omgeving: {omgeving.upper()} | "
                     f"Gebruiker: {os.getlogin()}"
            )

        # Validatieresultaten lijst opbouwen
        for widget in self.results_scroll.winfo_children():
            widget.destroy()

        # Sectiekoppen per fouttype
        RULE_LABELS = {
            'DuplicateArticleConflictRule': 'Dubbele artikelcodes',
            'EmptyArticleCodeRule': 'Ontbrekende artikelcodes',
            'InvalidQuantityRule': 'Ongeldige hoeveelheden',
            'UnknownPPRule': 'Onbekende productieprocessen',
            'StructureErrorRule': 'Structuurfouten',
            'UndeterminedRowRule': 'Onbepaalde rijen',
            'UnknownFinishRule': 'Onbekende afwerkingen',
            'HighQuantityRule': 'Opvallende hoeveelheden',
            'SummaryRule': 'Samenvatting',
            # SQL validatieregels
            'SqlConnectionInfoRule': 'Database verbinding',
            'ArticleExistsRule': 'Artikelen in RidderIQ',
            'BomExistsRule': 'Stuklijsten in RidderIQ',
        }

        current_section = None
        for r in results:
            section_key = (r.severity, r.rule)
            if section_key != current_section:
                current_section = section_key
                label = RULE_LABELS.get(r.rule, r.rule)
                self._add_section_header(label)
            self._add_result_row(r)

    def _add_section_header(self, text: str):
        """Voeg een sectiekop toe (fouttype groepering)."""
        header = ctk.CTkFrame(self.results_scroll, fg_color="transparent")
        header.pack(fill="x", pady=(12, 4))
        ctk.CTkLabel(
            header, text=text,
            font=FONT_SUBHEADING, text_color=CLR_TEXT,
        ).pack(anchor="w", padx=4)

    def _add_result_row(self, result: ValidationResult):
        """Voeg een validatieresultaat toe aan de scrolllijst."""
        if result.severity == 'error':
            bg, accent, prefix = CLR_ERROR_BG, CLR_ERROR, "FOUT"
            border_clr = "#F87171"  # Duidelijk rood randje
        elif result.severity == 'warning':
            bg, accent, prefix = CLR_WARNING_BG, CLR_WARNING, "LET OP"
            border_clr = "#FBBF24"  # Duidelijk amber randje
        else:
            bg, accent, prefix = CLR_INFO_BG, CLR_INFO, "INFO"
            border_clr = "#D1D5DB"  # Duidelijk grijs randje

        # Row frame met zichtbare rand via highlight
        row = tk.Frame(
            self.results_scroll, bg=bg,
            highlightbackground=border_clr, highlightthickness=1,
            highlightcolor=border_clr,
        )
        row.pack(fill="x", pady=(0, 3), padx=2)

        # Gekleurde accent-balk links (breed genoeg om te zien)
        accent_bar = tk.Frame(row, bg=accent, width=5)
        accent_bar.pack(side="left", fill="y")
        accent_bar.pack_propagate(False)

        # Linkerkant: badge + rijnummer
        left = tk.Frame(row, bg=bg)
        left.pack(side="left", anchor="n", padx=(8, 0), pady=(5, 5))

        badge = tk.Label(
            left, text=f" {prefix} ",
            font=("Segoe UI", 11, "bold"), fg="white",
            bg=accent, padx=6, pady=2,
        )
        badge.pack(anchor="w")

        if result.excel_rij:
            tk.Label(
                left, text=f"Rij {result.excel_rij}",
                font=("Consolas", 11), fg=CLR_TEXT_MUTED,
                bg=bg,
            ).pack(anchor="w", pady=(2, 0))

        # Rechterkant: melding + detail + actie
        text_frame = tk.Frame(row, bg=bg)
        text_frame.pack(side="left", fill="x", expand=True,
                        padx=(4, 8), pady=(4, 4))

        # Hoofdmelding
        tk.Label(
            text_frame, text=result.message,
            font=FONT_BODY_BOLD, fg=CLR_TEXT, bg=bg,
            anchor="w", wraplength=650, justify="left",
        ).pack(anchor="w")

        # Detail (uitleg)
        if result.detail:
            tk.Label(
                text_frame, text=result.detail,
                font=FONT_DETAIL, fg=CLR_TEXT_MUTED, bg=bg,
                anchor="w", wraplength=650, justify="left",
            ).pack(anchor="w")

        # Actie (wat te doen)
        if result.actie:
            tk.Label(
                text_frame, text=f"\u2192 {result.actie}",
                font=FONT_ACTIE, fg=CLR_ACTIE, bg=bg,
                anchor="w", wraplength=650, justify="left",
            ).pack(anchor="w")

    def _do_generate(self):
        """CSV genereren na bevestiging."""
        counts = count_by_severity(self.results)

        if counts['warning'] > 0:
            ok = messagebox.askyesno(
                "Waarschuwingen",
                f"Er zijn {counts['warning']} waarschuwing(en).\n\n"
                f"Wil je toch CSV bestanden genereren?",
            )
            if not ok:
                return

        self.on_generate(self.excel_path, self.omgeving, self.bom_rows)


# =============================================================================
# APP (HOOFDVENSTER)
# =============================================================================

class App(ctk.CTk):
    """BOM Import Tool hoofdapplicatie."""

    def __init__(self):
        super().__init__()

        # Venster configuratie
        self.geometry("900x700")
        self.minsize(800, 600)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # Frames
        self.start_frame = StartFrame(
            self,
            on_file_selected=self._load_file,
            on_env_changed=self._update_title,
        )
        self.analysis_frame = AnalysisFrame(
            self,
            on_back=self._show_start,
            on_generate=self._generate_csvs,
        )

        # Titel instellen met versie en omgeving (dynamisch bijgewerkt)
        self._update_title("speel")  # standaard omgeving

        self._show_start()

    def _update_title(self, omgeving: str):
        """Update de title bar met versienummer en actieve omgeving."""
        omgeving_label = "Speelomgeving" if omgeving == "speel" else "Live (productie)"
        self.title(f"BOM Import Tool v{APP_VERSION} [{omgeving_label}]")

    def _show_start(self):
        """Toon het startscherm."""
        self.analysis_frame.pack_forget()
        self.start_frame.pack(fill="both", expand=True)
        # Titel herstellen op basis van geselecteerde omgeving
        try:
            self._update_title(self.start_frame.omgeving_var.get())
        except Exception:
            self._update_title("speel")
        # Recente imports laden
        try:
            recent = get_recent_display()
            self.start_frame.update_recent(recent)
        except Exception:
            pass  # Database niet beschikbaar (eerste keer)

    def _show_analysis(self):
        """Toon het analysescherm."""
        self.start_frame.pack_forget()
        self.analysis_frame.pack(fill="both", expand=True)

    def _load_file(self, excel_path: str, omgeving: str):
        """Laad en valideer een Excel bestand."""
        try:
            self.configure(cursor="wait")
            self.update()

            bom_rows = parse_bom(excel_path)

            # Combineer standaard + SQL validatieregels
            rules = list(DEFAULT_RULES)
            rules.extend(get_sql_rules(omgeving))
            results = validate_all(bom_rows, rules=rules)

            self.analysis_frame.show_results(
                excel_path, omgeving, bom_rows, results
            )
            self._show_analysis()
            self._update_title(omgeving)

        except Exception as e:
            messagebox.showerror(
                "Fout bij laden",
                f"Kan het bestand niet laden:\n\n{e}",
            )
        finally:
            self.configure(cursor="")

    def _generate_csvs(self, excel_path: str, omgeving: str,
                       bom_rows: list):
        """Genereer CSV bestanden en log in history."""
        try:
            user = os.getlogin()
            output_dir = Path(DEFAULT_BASIS) / omgeving / user
            output_dir.mkdir(parents=True, exist_ok=True)

            # Archiveer bestaande bestanden
            for stap in STAP_VOLGORDE:
                archive_existing(output_dir, STAP_BESTANDEN[stap])

            # Genereer alle CSV's
            totals = {}
            for stap in STAP_VOLGORDE:
                generator = STAP_GENERATORS[stap]
                n = generator(bom_rows, output_dir)
                totals[stap] = n

            total_rows = sum(totals.values())

            # Statistieken voor history
            n_artikel = sum(1 for r in bom_rows if r.row_type == 'artikel')
            n_zaag = sum(1 for r in bom_rows if r.row_type == 'zaagregel')
            n_onbepaald = sum(1 for r in bom_rows if r.row_type == 'onbepaald')
            parent_numbers = collect_parent_numbers(bom_rows)
            counts = count_by_severity(
                self.analysis_frame.results
            )

            # Log naar history database
            try:
                warning_msgs = [
                    r.message for r in self.analysis_frame.results
                    if r.is_warning
                ]
                log_import(
                    user=user,
                    filename=excel_path,
                    environment=omgeving,
                    status=f"OK ({counts['warning']} waarsch.)"
                           if counts['warning'] > 0 else "OK",
                    articles_count=n_artikel,
                    boms_count=len(parent_numbers),
                    sawlines_count=n_zaag,
                    undetermined_count=n_onbepaald,
                    errors_count=counts['error'],
                    warnings_count=counts['warning'],
                    csv_rows_total=total_rows,
                    output_dir=str(output_dir),
                    warnings=warning_msgs,
                )
            except Exception:
                pass  # History logging mag niet de export blokkeren

            messagebox.showinfo(
                "CSV Genereren",
                f"CSV bestanden succesvol gegenereerd!\n\n"
                f"Output: {output_dir}\n"
                f"Bestanden: {len(STAP_VOLGORDE)}\n"
                f"Totaal regels: {total_rows}\n\n"
                f"Details:\n" +
                "\n".join(f"  {STAP_BESTANDEN[s]}: {totals[s]} regels"
                          for s in STAP_VOLGORDE)
            )

            self._show_start()

        except Exception as e:
            # Log mislukte import
            try:
                log_import(
                    user=os.getlogin(),
                    filename=excel_path,
                    environment=omgeving,
                    status=f"FOUT: {e}",
                )
            except Exception:
                pass

            messagebox.showerror(
                "Fout bij genereren",
                f"Er ging iets mis bij het genereren:\n\n{e}",
            )


# =============================================================================
# MAIN
# =============================================================================

def main():
    app = App()
    app.mainloop()


if __name__ == '__main__':
    main()
