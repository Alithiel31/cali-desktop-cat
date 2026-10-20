"""Raccourci clavier global (actif même quand une autre application a le focus).

Windows envoie WM_HOTKEY à la file de messages du fil qui a appelé RegisterHotKey (sans fenêtre : hwnd NULL).
Qt fait passer chaque message de cette file par les filtres d'événements natifs : on y repère le nôtre.
Hors Windows, `register` renvoie False et rien ne se passe.
"""
from __future__ import annotations

import ctypes
import logging
import sys

from PySide6.QtCore import QAbstractNativeEventFilter, QCoreApplication, QObject, Signal

log = logging.getLogger("desktopcat.hotkey")

IS_WIN = sys.platform == "win32"
WM_HOTKEY = 0x0312
MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_NOREPEAT = 0x1, 0x2, 0x4, 0x4000
HOTKEY_ID = 0xCA7                       # identifiant propre à l'appli (0x0000 à 0xBFFF)
DEFAULT = (MOD_CONTROL | MOD_ALT, ord("C"))
LABEL = "Ctrl+Alt+C"


class _Filter(QAbstractNativeEventFilter):
    def __init__(self, owner: GlobalHotkey):
        super().__init__()
        self.owner = owner

    def nativeEventFilter(self, event_type, message):
        if IS_WIN and bytes(event_type) == b"windows_generic_MSG":
            from ctypes import wintypes
            msg = wintypes.MSG.from_address(int(message))
            if self.owner.handle(msg.message, msg.wParam):
                return True, 0
        return False, 0


class GlobalHotkey(QObject):
    activated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.registered = False
        self._filter: _Filter | None = None

    def handle(self, message: int, wparam: int) -> bool:
        """Traite un message Windows ; vrai s'il s'agissait de notre raccourci."""
        if self.registered and message == WM_HOTKEY and wparam == HOTKEY_ID:
            self.activated.emit()
            return True
        return False

    def set_enabled(self, enabled: bool) -> bool:
        """Active ou désactive le raccourci. Renvoie l'état obtenu (False si Windows l'a refusé)."""
        if enabled and not self.registered:
            self.register()
        elif not enabled and self.registered:
            self.unregister()
        return self.registered

    def register(self, mods: int = DEFAULT[0], vk: int = DEFAULT[1]) -> bool:
        if not IS_WIN or self.registered:
            return self.registered
        if self._filter is None:
            self._filter = _Filter(self)
            QCoreApplication.instance().installNativeEventFilter(self._filter)
        if not ctypes.windll.user32.RegisterHotKey(None, HOTKEY_ID, mods | MOD_NOREPEAT, vk):
            log.warning("Raccourci %s indisponible (déjà pris par une autre application ?)", LABEL)
            return False
        self.registered = True
        log.info("Raccourci %s actif", LABEL)
        return True

    def unregister(self) -> None:
        if IS_WIN and self.registered:
            ctypes.windll.user32.UnregisterHotKey(None, HOTKEY_ID)
        self.registered = False
