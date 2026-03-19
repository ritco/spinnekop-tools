"""ePlan Import Tool — Entry Point
Spinnekop BV

Start de GUI applicatie voor het importeren van ePlan stuklijsten in RidderIQ.

Gebruik:
  GUI:  python eplan_main.py
"""

__version__ = '1.0.1'

import sys
from pathlib import Path

# Zorg dat scripts/ in het pad staat
script_dir = Path(__file__).parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))


def main():
    from eplan_gui import EplanApp
    app = EplanApp()

    import threading

    def _bg_update_check():
        import traceback
        from pathlib import Path
        log_path = (
            Path(sys.executable).parent / 'eplan-update-debug.log'
            if getattr(sys, 'frozen', False)
            else Path(__file__).parent / 'eplan-update-debug.log'
        )
        def _log(msg):
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    from datetime import datetime
                    f.write(f"{datetime.now():%H:%M:%S} {msg}\n")
            except Exception:
                pass
        try:
            _log(f"Update check gestart (huidige versie: {__version__})")
            from app_config import check_for_update, load_config, _config_path
            _log(f"Config pad: {_config_path()}")
            cfg = load_config()
            _log(f"Config: repo={cfg.get('update_github_repo')} channel={cfg.get('update_channel')}")
            update = check_for_update('eplan-import-tool', __version__)
            _log(f"check_for_update resultaat: {update}")
            if update:
                _log(f"Update gevonden: {update['remote_version']} — dialog tonen")
                app.after(0, lambda: _show_update_after_gui(
                    app, update['remote_version'], update))
            else:
                _log("Geen update gevonden")
        except Exception as e:
            _log(f"FOUT: {e}\n{traceback.format_exc()}")

    threading.Thread(target=_bg_update_check, daemon=True).start()

    app.mainloop()


def _show_update_after_gui(app, remote_version, update_info):
    """Toon update dialog met de App als parent (na mainloop start)."""
    try:
        from app_config import show_update_dialog, do_self_update
        ok = show_update_dialog(__version__, remote_version, parent=app)
        if ok and do_self_update(
            'eplan-import-tool', 'eplan-import-tool.exe',
            share_override=update_info.get('update_share'),
            download_url=update_info.get('download_url'),
        ):
            app.destroy()
            sys.exit(0)
    except Exception:
        pass


if __name__ == '__main__':
    main()
