"""Génère des captures du panneau (une par onglet) sans afficher d'écran : tools/out/panel_*.png.

    python tools/preview_panel.py
"""
import os
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from PySide6.QtWidgets import QApplication  # noqa: E402

from desktopcat.game import Game  # noqa: E402
from desktopcat.panel import Panel  # noqa: E402
from desktopcat.store import Store  # noqa: E402

OUT = os.path.join(ROOT, "tools", "out")
TABS = ["hats", "focus", "stats", "settings"]


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    app = QApplication([])
    game = Game(Store(os.path.join(tempfile.mkdtemp(), "save.json")))
    for _ in range(6):                      # quelques chapeaux pour remplir la garde-robe
        game.data["gift_pending"] = True
        game.claim_gift()
    panel = Panel(game)
    panel.resize(560, 640)
    panel.show()
    app.processEvents()
    for i, name in enumerate(TABS):
        panel.show_tab(i)
        app.processEvents()
        panel.grab().save(os.path.join(OUT, f"panel_{name}.png"))
    print("Captures écrites dans", OUT)


if __name__ == "__main__":
    main()
