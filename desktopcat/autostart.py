"""Lancement avec Windows (clé de registre de l'utilisateur, sans droits administrateur)."""
from __future__ import annotations

import logging
import os
import sys

log = logging.getLogger("desktopcat.autostart")

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "DesktopCat"


def _command() -> str:
    if getattr(sys, "frozen", False):                      # version empaquetée (.exe)
        return f'"{sys.executable}"'
    exe = sys.executable
    pythonw = os.path.join(os.path.dirname(exe), "pythonw.exe")   # pythonw : pas de fenêtre de console
    if os.path.exists(pythonw):
        exe = pythonw
    main = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))
    return f'"{exe}" "{main}"'


def set_enabled(enabled: bool) -> bool:
    if sys.platform != "win32":
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, _command())
            else:
                try:
                    winreg.DeleteValue(key, VALUE_NAME)
                except FileNotFoundError:
                    pass
        return True
    except OSError as e:
        log.error("Démarrage automatique impossible : %s", e)
        return False
