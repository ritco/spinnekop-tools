"""ePlan Import Tool — GUI
Spinnekop BV

Desktop applicatie voor het valideren en importeren van ePlan stuklijst-exports
naar RidderIQ ERP.

Architectuur:
  StartFrame    → bestand openen, omgeving kiezen, recente imports
  AnalysisFrame → analysesamenvatting, goedkeuring, CSV genereren
"""

import json
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from datetime import datetime

import customtkinter as ctk

from eplan_converter import convert, ConversionResult
from history import log_import, get_recent_display
from app_config import get_output_basis, show_settings_dialog, config_exists, load_config

try:
    from eplan_main import __version__
except ImportError:
    __version__ = '0.0.0'

APP_TITLE = "ePlan Import Tool — Spinnekop"
APP_VERSION = __version__
DEFAULT_BASIS = str(get_output_basis())

# Kleuren (identiek aan gui.py)
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
            content, text="Open ePlan Excel",
            font=("Segoe UI", 16, "bold"),
            fg_color=CLR_PRIMARY, hover_color=CLR_PRIMARY_HOVER,
            height=50, corner_radius=8,
            command=self._open_file,
        ).pack(fill="x", pady=(10, 0))

        # Hint label
        ctk.CTkLabel(
            content,
            text="Ondersteunde formaten: .xlsx",
            font=FONT_SMALL, text_color=CLR_TEXT_MUTED,
        ).pack(pady=(10, 0))

        # Recente imports
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
        self.footer_label = ctk.CTkLabel(
            footer,
            text=f"Gebruiker: {user}  |  Basis: {DEFAULT_BASIS}",
            font=FONT_SMALL, text_color=CLR_TEXT_MUTED,
        )
        self.footer_label.pack(side="left", padx=15, pady=8)
        ctk.CTkButton(
            footer, text="\u2699 Instellingen",
            font=FONT_SMALL, fg_color="#6B7280",
            hover_color="#4B5563", width=110, height=26,
            command=self._open_settings,
        ).pack(side="right", padx=15, pady=8)

    def _open_settings(self):
        """Open het instellingen-dialoog."""
        def _on_save(config):
            global DEFAULT_BASIS
            DEFAULT_BASIS = str(get_output_basis())
            user = os.getlogin()
            self.footer_label.configure(
                text=f"Gebruiker: {user}  |  Basis: {DEFAULT_BASIS}"
            )
        show_settings_dialog(parent=self.winfo_toplevel(), on_save=_on_save)

    def _open_file(self):
        path = filedialog.askopenfilename(
            title="Selecteer ePlan Excel",
            filetypes=[
                ("Excel bestanden", "*.xlsx"),
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
    """Analysescherm: samenvatting, fouten/waarschuwingen, output genereren."""

    def __init__(self, master, on_back, on_generate):
        super().__init__(master, fg_color=CLR_BG)
        self.on_back = on_back
        self.on_generate = on_generate
        self._result = None
        self._excel_path = ''
        self._omgeving = ''

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

        self.card_matched = self._make_card(self.summary_cards, "Matched", "0",
                                            accent=CLR_PRIMARY)
        self.card_nieuw = self._make_card(self.summary_cards, "Nieuw", "0",
                                          accent=CLR_WARNING)
        self.card_overgeslagen = self._make_card(self.summary_cards, "Overgesl.", "0",
                                                 accent=CLR_INFO)
        self.card_fouten = self._make_card(self.summary_cards, "Fouten", "0",
                                           accent=CLR_ERROR)
        self.card_warnings = self._make_card(self.summary_cards, "Waarsch.", "0",
                                             accent=CLR_WARNING)

        # Status bar
        self.status_bar = ctk.CTkFrame(self, fg_color=CLR_SUCCESS_BG, corner_radius=0)
        self.status_bar.pack(fill="x", padx=20, pady=(10, 0))
        self.status_label = ctk.CTkLabel(
            self.status_bar, text="",
            font=FONT_BODY, text_color=CLR_SUCCESS,
        )
        self.status_label.pack(pady=8)

        # Resultatenlijst header
        results_header = ctk.CTkFrame(self, fg_color="transparent")
        results_header.pack(fill="x", padx=20, pady=(10, 0))
        ctk.CTkLabel(
            results_header, text="Meldingen",
            font=FONT_SUBHEADING, text_color=CLR_TEXT,
        ).pack(side="left")

        # Scrollable resultatenlijst
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
            btn_frame, text="Genereer output",
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

    def _make_card(self, parent, label, value, accent=None):
        """Maak een samenvattingskaart."""
        if accent is None:
            accent = CLR_PRIMARY
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

    def show_results(self, excel_path: str, omgeving: str, result: ConversionResult):
        """Toon de analyseresultaten voor een geladen Excel."""
        self._excel_path = excel_path
        self._omgeving = omgeving
        self._result = result

        filename = Path(excel_path).name
        self.header_label.configure(text=f"Analyse: {filename}")

        # Samenvattingskaarten updaten
        self.card_matched.configure(text=str(len(result.matched)))
        self.card_nieuw.configure(text=str(len(result.new_items)))
        self.card_overgeslagen.configure(text=str(len(result.skipped)))
        self.card_fouten.configure(text=str(len(result.errors)))
        self.card_warnings.configure(text=str(len(result.warnings)))

        has_blockers = result.has_blockers

        # Status bar
        if has_blockers:
            self.status_bar.configure(fg_color=CLR_ERROR_BG)
            self.status_label.configure(
                text=f"{len(result.errors)} fout(en) gevonden — "
                     f"output genereren is geblokkeerd. "
                     f"Los eerst de fouten op in de Excel.",
                text_color=CLR_ERROR,
            )
            self.btn_generate.configure(state="disabled", fg_color=CLR_INFO)
            self.generate_info.configure(
                text="Pas de Excel aan en open het bestand opnieuw"
            )
        elif result.warnings:
            self.status_bar.configure(fg_color=CLR_WARNING_BG)
            self.status_label.configure(
                text=f"Geen fouten, maar {len(result.warnings)} "
                     f"waarschuwing(en). Bekijk de meldingen "
                     f"hieronder voor je verder gaat.",
                text_color="#92400E",
            )
            self.btn_generate.configure(
                state="normal", fg_color=CLR_SUCCESS,
                text=f"Genereer output ({len(result.warnings)} waarsch.)",
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
                text="Genereer output",
            )
            self.generate_info.configure(
                text=f"Omgeving: {omgeving.upper()} | "
                     f"Gebruiker: {os.getlogin()}"
            )

        # Resultatenlijst opbouwen
        for widget in self.results_scroll.winfo_children():
            widget.destroy()

        # Fouten tonen
        for fout in result.errors:
            self._add_result_row(fout, severity='error')

        # Waarschuwingen tonen
        for waarsch in result.warnings:
            self._add_result_row(waarsch, severity='warning')

    def _add_result_row(self, message: str, severity: str = 'error'):
        """Voeg een melding toe aan de scrolllijst."""
        if severity == 'error':
            bg, accent, prefix = CLR_ERROR_BG, CLR_ERROR, "FOUT"
            border_clr = "#F87171"
        elif severity == 'warning':
            bg, accent, prefix = CLR_WARNING_BG, CLR_WARNING, "LET OP"
            border_clr = "#FBBF24"
        else:
            bg, accent, prefix = CLR_INFO_BG, CLR_INFO, "INFO"
            border_clr = "#D1D5DB"

        row = tk.Frame(
            self.results_scroll, bg=bg,
            highlightbackground=border_clr, highlightthickness=1,
            highlightcolor=border_clr,
        )
        row.pack(fill="x", pady=(0, 3), padx=2)

        # Gekleurde accent-balk links
        accent_bar = tk.Frame(row, bg=accent, width=5)
        accent_bar.pack(side="left", fill="y")
        accent_bar.pack_propagate(False)

        # Linkerkant: badge
        left = tk.Frame(row, bg=bg)
        left.pack(side="left", anchor="n", padx=(8, 0), pady=(5, 5))

        tk.Label(
            left, text=f" {prefix} ",
            font=("Segoe UI", 11, "bold"), fg="white",
            bg=accent, padx=6, pady=2,
        ).pack(anchor="w")

        # Rechterkant: melding
        text_frame = tk.Frame(row, bg=bg)
        text_frame.pack(side="left", fill="x", expand=True,
                        padx=(4, 8), pady=(4, 4))

        tk.Label(
            text_frame, text=message,
            font=FONT_BODY_BOLD, fg=CLR_TEXT, bg=bg,
            anchor="w", wraplength=650, justify="left",
        ).pack(anchor="w")

    def _do_generate(self):
        """Output genereren na bevestiging bij waarschuwingen."""
        if self._result and self._result.warnings:
            ok = messagebox.askyesno(
                "Waarschuwingen",
                f"Er zijn {len(self._result.warnings)} waarschuwing(en).\n\n"
                f"Wil je toch de output bestanden genereren?",
            )
            if not ok:
                return

        self.on_generate(self._excel_path, self._omgeving, self._result)


# =============================================================================
# EPLANAPP (HOOFDVENSTER)
# =============================================================================

class EplanApp(ctk.CTk):
    """ePlan Import Tool hoofdapplicatie."""

    def __init__(self):
        super().__init__()

        # Venster configuratie
        self.geometry("900x700")
        self.minsize(800, 600)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # Eerste keer? Toon settings dialoog
        if not config_exists():
            self.after(100, lambda: show_settings_dialog(
                parent=self,
                on_save=lambda cfg: self._refresh_basis(),
            ))

        # Frames
        self.start_frame = StartFrame(
            self,
            on_file_selected=self._load_file,
            on_env_changed=self._update_title,
        )
        self.analysis_frame = AnalysisFrame(
            self,
            on_back=self._show_start,
            on_generate=self._generate_output,
        )

        # Titel instellen
        self._update_title("speel")

        self._show_start()

    def _refresh_basis(self):
        """Herlaad output basis na settings-wijziging."""
        global DEFAULT_BASIS
        DEFAULT_BASIS = str(get_output_basis())

    def _update_title(self, omgeving: str):
        """Update de title bar met versienummer en actieve omgeving."""
        omgeving_label = "Speelomgeving" if omgeving == "speel" else "Live (productie)"
        self.title(f"ePlan Import Tool v{APP_VERSION} [{omgeving_label}]")

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
        """Laad en analyseer een ePlan Excel bestand (dry_run=True)."""
        try:
            self.configure(cursor="wait")
            self.update()

            result = convert(excel_path, omgeving, dry_run=True)

            self.analysis_frame.show_results(excel_path, omgeving, result)
            self._show_analysis()
            self._update_title(omgeving)

        except Exception as e:
            messagebox.showerror(
                "Fout bij laden",
                f"Kan het bestand niet laden:\n\n{e}",
            )
        finally:
            self.configure(cursor="")

    def _generate_output(self, excel_path: str, omgeving: str,
                         result: ConversionResult):
        """Genereer output bestanden (dry_run=False) en log naar history."""
        try:
            self.configure(cursor="wait")
            self.update()

            result2 = convert(excel_path, omgeving, dry_run=False)

            if result2.has_blockers:
                messagebox.showerror(
                    "Fout bij genereren",
                    f"Output geblokkeerd door {len(result2.errors)} fout(en):\n\n" +
                    "\n".join(f"  - {e}" for e in result2.errors[:10]),
                )
                return

            # Bepaal output map
            output_dir = get_output_basis() / omgeving

            # Bepaal welke bestanden aangemaakt zijn
            stappen = []
            if result2.new_items:
                stappen.append("01-nieuwe-artikelen-eplan.csv")
            stappen.append("02-stuklijst-header.csv")
            stappen.append("03-stuklijstregels.csv")

            # Log naar history
            try:
                log_import(
                    user=os.getlogin(),
                    filename=excel_path,
                    environment=omgeving,
                    status="OK" if not result2.warnings else f"OK ({len(result2.warnings)} waarsch.)",
                    articles_count=len(result2.matched) + len(result2.new_items),
                    boms_count=1,
                    sawlines_count=0,
                    undetermined_count=len(result2.skipped),
                    errors_count=len(result2.errors),
                    warnings_count=len(result2.warnings),
                    csv_rows_total=len(result2.matched) + len(result2.new_items),
                    output_dir=str(output_dir),
                )
            except Exception:
                pass  # History mag niet de export blokkeren

            # Importinstructies bouwen
            instructies = (
                f"Output bestanden aangemaakt!\n\n"
                f"Locatie: {output_dir}\n\n"
                f"Importeer in RidderIQ:\n"
            )
            stap_nr = 1
            if result2.new_items:
                instructies += (
                    f"Stap {stap_nr}: Importeer 01-nieuwe-artikelen-eplan.csv\n"
                    f"         (alleen als aanwezig — nieuwe artikelen)\n"
                )
                stap_nr += 1
            instructies += f"Stap {stap_nr}: Importeer 02-stuklijst-header.csv\n"
            stap_nr += 1
            instructies += f"Stap {stap_nr}: Importeer 03-stuklijstregels.csv\n"
            instructies += (
                f"\n"
                f"Matched: {len(result2.matched)}  Nieuw: {len(result2.new_items)}"
            )

            messagebox.showinfo("Output aangemaakt", instructies)

            self._show_start()

        except Exception as e:
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
        finally:
            self.configure(cursor="")


# =============================================================================
# MAIN
# =============================================================================

def main():
    app = EplanApp()
    app.mainloop()


if __name__ == '__main__':
    main()
