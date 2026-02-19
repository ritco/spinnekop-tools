"""BOM Import Tool — Entry Point
Spinnekop BV

Start de GUI applicatie of voer CLI-mode uit voor backward compatibility.

Gebruik:
  GUI:  python main.py
  CLI:  python main.py --cli --stap alles --omgeving speel --excel bom.xls
"""

__version__ = '1.0.0'

import sys
from pathlib import Path

# Zorg dat scripts/ in het pad staat
script_dir = Path(__file__).parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))


def main():
    # CLI mode als --cli flag aanwezig is (backward compatibility)
    if '--cli' in sys.argv:
        sys.argv.remove('--cli')
        from bom_converter import main as cli_main
        cli_main()
        return

    # GUI mode (standaard)
    from gui import App
    app = App()
    app.mainloop()


if __name__ == '__main__':
    main()
