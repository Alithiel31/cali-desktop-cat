"""Desktop Cat : point d'entrée.   python main.py"""
import os
import sys
import tempfile

from PySide6.QtCore import QLockFile, QUrl
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from desktopcat import __version__, log
from desktopcat import hotkey as hotkey_module
from desktopcat.game import FEED_COST, Game
from desktopcat.panel import Panel
from desktopcat.pet import Pet
from desktopcat.sprite import render_pixmap
from desktopcat.store import Store
from desktopcat.widgets import Bubble, FxLayer, GiftBox


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Desktop Cat")
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(QIcon(render_pixmap(4, pose="sit", t=0)))     # panneau et boîtes de dialogue

    lock = QLockFile(os.path.join(tempfile.gettempdir(), "desktopcat.lock"))
    lock.setStaleLockTime(30_000)   # un verrou laissé par un plantage (processus disparu) est repris après 30 s
    if not lock.tryLock(100):
        print("Desktop Cat est déjà lancé.")
        return 0
    log_file = log.setup()              # après le verrou : une 2e instance n'écrit pas dans le journal de la 1re

    store = Store()
    game = Game(store)
    bubble = Bubble()
    gift = GiftBox(store.data["settings"]["scale"])
    fx = FxLayer(app.primaryScreen().availableGeometry())
    pet = Pet(game, bubble, gift, fx)

    panel = None

    # ───────── raccourci global : afficher / cacher le chat
    hotkey = hotkey_module.GlobalHotkey()
    hotkey.activated.connect(lambda: pet.set_user_hidden(not pet.user_hidden))
    hotkey.set_enabled(store.data["settings"]["hotkey"])
    game.changed.connect(lambda: hotkey.set_enabled(game.settings["hotkey"]))
    app.aboutToQuit.connect(hotkey.unregister)

    def open_panel(tab=None):
        nonlocal panel
        game.sync_autostart()           # la case du panneau montre l'état réel du registre
        if panel is None:
            panel = Panel(game)
        panel.show()
        panel.raise_()
        panel.activateWindow()
        if tab is not None:
            panel.show_tab(tab)

    # ───────── icône de la zone de notification
    tray = QSystemTrayIcon(QIcon(render_pixmap(2, pose="sit", fur=store.data["fur"], t=0)))
    tray.setToolTip(f"Desktop Cat {__version__}")
    menu = QMenu()

    def rebuild_menu():
        menu.clear()
        menu.addAction("Ouvrir le panneau", open_panel)
        if game.focus:
            menu.addAction("Arrêter la concentration", lambda: game.stop_focus(False))
        else:
            menu.addAction("Concentration 25 min", lambda: game.start_focus(25))
        if game.brk:
            menu.addAction("Passer la pause", game.skip_break)
        feed = menu.addAction(f"Donner des croquettes ({FEED_COST} 🐟)", game.feed)
        feed.setEnabled(game.can_feed())
        label = "Afficher le chat" if pet.user_hidden else "Cacher le chat"
        if hotkey.registered:
            label += f"\t{hotkey_module.LABEL}"
        menu.addAction(label, lambda: pet.set_user_hidden(not pet.user_hidden))
        menu.addSeparator()
        if log_file:
            menu.addAction("Ouvrir le journal", lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(log_file)))
        menu.addAction("Quitter", app.quit)

    menu.aboutToShow.connect(rebuild_menu)
    tray.setContextMenu(menu)
    tray.activated.connect(lambda reason: open_panel() if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
    tray.show()
    if store.recovered_from:        # fichier illisible : on prévient, car les dernières heures de progression manquent
        day = os.path.basename(store.recovered_from)[5:15]
        tray.showMessage("Sauvegarde restaurée", f"Ta sauvegarde était illisible : la copie du {day} a été restaurée.",
                         QSystemTrayIcon.MessageIcon.Warning, 10000)

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
    log.shutdown()
    return code


if __name__ == "__main__":
    sys.exit(main())
