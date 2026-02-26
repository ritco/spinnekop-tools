"""BOM Import Tool — Entry Point
Spinnekop BV

Start de GUI applicatie of voer CLI-mode uit voor backward compatibility.

Gebruik:
  GUI:  python main.py
  CLI:  python main.py --cli --stap alles --omgeving speel --excel bom.xls
"""

__version__ = '1.2.1'

import sys
from pathlib import Path

# Zorg dat scripts/ in het pad staat
script_dir = Path(__file__).parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))


def _check_update_before_gui() -> bool:
    """Check voor updates op de network share (voor de GUI start).

    Returns True als de update gestart is (caller moet sys.exit doen),
    False als er geen update is of als de check faalt.
    """
    try:
        from app_config import check_for_update
        update = check_for_update('bom-import-tool', __version__)
        if update:
            return update
        return None
    except Exception:
        return None  # Update check mag nooit de app blokkeren


def main():
    # CLI mode als --cli flag aanwezig is (backward compatibility)
    if '--cli' in sys.argv:
        sys.argv.remove('--cli')
        from bom_converter import main as cli_main
        cli_main()
        return

    # Check of er een update beschikbaar is (netwerk-check, geen GUI)
    update_info = _check_update_before_gui()

    # GUI mode (standaard)
    from gui import App
    app = App()

    # Toon update dialog NA de App root is aangemaakt
    if update_info:
        try:
            from app_config import show_update_dialog, do_self_update
            app.after(100, lambda: _show_update_after_gui(
                app, update_info['remote_version'], update_info['update_share']))
        except Exception:
            pass

    app.mainloop()


def _show_update_after_gui(app, remote_version, resolved_share):
    """Toon update dialog met de App als parent (na mainloop start)."""
    try:
        from app_config import show_update_dialog, do_self_update
        ok = show_update_dialog(__version__, remote_version, parent=app)
        if ok and do_self_update('bom-import-tool', 'bom-import-tool.exe',
                                 share_override=resolved_share):
            app.destroy()
            sys.exit(0)
    except Exception:
        pass


if __name__ == '__main__':
    main()
