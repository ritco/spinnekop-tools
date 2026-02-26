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


def _check_update():
    """Check voor updates op de network share en bied self-update aan via CTk dialog."""
    try:
        from app_config import check_for_update, do_self_update, show_update_dialog
        update = check_for_update('bom-import-tool', __version__)
        if not update:
            return

        # CTkToplevel vereist een actieve CTk root. We maken een verborgen root
        # aan die we na de dialog weer opruimen.
        import customtkinter as ctk
        _root = ctk.CTk()
        _root.withdraw()

        ok = show_update_dialog(__version__, update['remote_version'], parent=_root)
        _root.destroy()

        if ok and do_self_update('bom-import-tool', 'bom-import-tool.exe'):
            sys.exit(0)

    except Exception:
        pass  # Update check mag nooit de app blokkeren


def main():
    # CLI mode als --cli flag aanwezig is (backward compatibility)
    if '--cli' in sys.argv:
        sys.argv.remove('--cli')
        from bom_converter import main as cli_main
        cli_main()
        return

    # Update check (alleen in GUI mode)
    _check_update()

    # GUI mode (standaard)
    from gui import App
    app = App()
    app.mainloop()


if __name__ == '__main__':
    main()
