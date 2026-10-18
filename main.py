"""Desktop Cat : point d'entrée.   python main.py"""
import os
import sys
import tempfile

from PySide6.QtCore import QLockFile
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from desktopcat.game import Game
from desktopcat.panel import Panel
from desktopcat.pet import Pet
from desktopcat.sprite import render_pixmap
from desktopcat.store import Store
from desktopcat.widgets import Bubble, FxLayer, GiftBox


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Desktop Cat")
    app.setQuitOnLastWindowClosed(False)

    lock = QLockFile(os.path.join(tempfile.gettempdir(), "desktopcat.lock"))
    lock.setStaleLockTime(0)
    if not lock.tryLock(100):
        print("Desktop Cat est déjà lancé.")
        return 0

    store = Store()
    game = Game(store)
    bubble = Bubble()
    gift = GiftBox(store.data["settings"]["scale"])
    fx = FxLayer(app.primaryScreen().availableGeometry())
    pet = Pet(game, bubble, gift, fx)

    panel = None

    def open_panel(tab=None):
        nonlocal panel
        if panel is None:
            panel = Panel(game)
        panel.show()
        panel.raise_()
        panel.activateWindow()
        if tab is not None:
            panel.show_tab(tab)

    # ───────── icône de la zone de notification
    tray = QSystemTrayIcon(QIcon(render_pixmap(2, pose="sit", fur=store.data["fur"], t=0)))
    tray.setToolTip("Desktop Cat")
    menu = QMenu()

    def rebuild_menu():
        menu.clear()
        menu.addAction("Ouvrir le panneau", open_panel)
        if game.focus:
            menu.addAction("Arrêter la concentration", lambda: game.stop_focus(False))
        else:
            menu.addAction("Concentration 25 min", lambda: game.start_focus(25))
        menu.addAction("Afficher le chat" if pet.user_hidden else "Cacher le chat",
                       lambda: pet.set_user_hidden(not pet.user_hidden))
        menu.addSeparator()
        menu.addAction("Quitter", app.quit)

    menu.aboutToShow.connect(rebuild_menu)
    tray.setContextMenu(menu)
    tray.activated.connect(lambda reason: open_panel() if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
    tray.show()

    game.notice.connect(lambda title, msg: tray.showMessage(title, msg, QSystemTrayIcon.MessageIcon.NoIcon, 6000)
                        if game.settings["notifications"] else None)
    pet.open_panel.connect(open_panel)
    pet.quit_app.connect(app.quit)
    pet.start_focus.connect(game.start_focus)
    pet.stop_focus.connect(lambda: game.stop_focus(False))
    app.aboutToQuit.connect(game.save)

    game.start()
    code = app.exec()
    lock.unlock()
    return code


if __name__ == "__main__":
    sys.exit(main())
