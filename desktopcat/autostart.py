"""Lancement avec Windows (clé de registre de l'utilisateur, sans droits administrateur).

Deux endroits comptent :
- `HKCU\\...\\CurrentVersion\\Run`, valeur `DesktopCat` : la commande lancée à l'ouverture de session ;
- `HKCU\\...\\Explorer\\StartupApproved\\Run`, même nom : ce que le Gestionnaire des tâches (onglet Démarrage) modifie
  quand on y « désactive » une appli. Il ne supprime pas la valeur `Run` : il y écrit un octet impair.
C'est le registre qui fait foi, pas la sauvegarde : `is_enabled` dit si l'appli démarrera vraiment.
"""
from __future__ import annotations

import logging
import os
import sys

log = logging.getLogger("desktopcat.autostart")

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APPROVED_KEY = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"
VALUE_NAME = "DesktopCat"
APPROVED_ON = bytes([0x02]) + bytes(11)     # valeur « activé » telle que Windows l'écrit (12 octets)


def _reg():
    """Le module winreg, ou None hors Windows (remplacé par un faux registre dans les tests)."""
    if sys.platform != "win32":
        return None
    import winreg
    return winreg


def _command() -> str:
    if getattr(sys, "frozen", False):                      # version empaquetée (.exe)
        return f'"{sys.executable}"'
    exe = sys.executable
    pythonw = os.path.join(os.path.dirname(exe), "pythonw.exe")   # pythonw : pas de fenêtre de console
    if os.path.exists(pythonw):
        exe = pythonw
    main = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))
    return f'"{exe}" "{main}"'


def approved(data) -> bool:
    """Lit une valeur de StartupApproved : absente ou premier octet pair = activé ; impair = désactivé."""
    return not data or not (bytes(data)[0] & 1)


def _read(reg, key_path: str):
    try:
        with reg.OpenKey(reg.HKEY_CURRENT_USER, key_path, 0, reg.KEY_READ) as key:
            return reg.QueryValueEx(key, VALUE_NAME)[0]
    except FileNotFoundError:
        return None


def _delete(reg, key_path: str) -> None:
    try:
        with reg.OpenKey(reg.HKEY_CURRENT_USER, key_path, 0, reg.KEY_SET_VALUE) as key:
            reg.DeleteValue(key, VALUE_NAME)
    except FileNotFoundError:
        pass


def is_enabled():
    """True / False selon que l'appli démarrera avec Windows ; None hors Windows ou si le registre est illisible."""
    reg = _reg()
    if reg is None:
        return None
    try:
        return _read(reg, RUN_KEY) is not None and approved(_read(reg, APPROVED_KEY))
    except OSError as e:
        log.warning("Lecture du démarrage automatique impossible : %s", e)
        return None


def set_enabled(enabled: bool) -> bool:
    """Active (commande au chemin actuel, et réactivation si le Gestionnaire des tâches l'avait désactivée)
    ou désactive le lancement avec Windows. Renvoie False si le registre n'a pas pu être modifié."""
    reg = _reg()
    if reg is None:
        return False
    try:
        if enabled:
            with reg.CreateKey(reg.HKEY_CURRENT_USER, RUN_KEY) as key:
                reg.SetValueEx(key, VALUE_NAME, 0, reg.REG_SZ, _command())
            if not approved(_read(reg, APPROVED_KEY)):        # on vient de recocher la case : on le veut vraiment
                with reg.CreateKey(reg.HKEY_CURRENT_USER, APPROVED_KEY) as key:
                    reg.SetValueEx(key, VALUE_NAME, 0, reg.REG_BINARY, APPROVED_ON)
                log.info("Démarrage automatique réactivé (il était désactivé dans le Gestionnaire des tâches)")
        else:
            _delete(reg, RUN_KEY)
            _delete(reg, APPROVED_KEY)
        return True
    except OSError as e:
        log.error("Démarrage automatique impossible : %s", e)
        return False


def refresh_path() -> bool:
    """Au démarrage : si le lancement avec Windows est actif, réécrit la commande au chemin actuel (exe déplacé ou mis à
    jour). Ne touche pas à une désactivation faite dans le Gestionnaire des tâches."""
    reg = _reg()
    if reg is None:
        return False
    try:
        current = _read(reg, RUN_KEY)
        if current is None or current == _command():
            return False
        with reg.CreateKey(reg.HKEY_CURRENT_USER, RUN_KEY) as key:
            reg.SetValueEx(key, VALUE_NAME, 0, reg.REG_SZ, _command())
        log.info("Démarrage automatique : chemin mis à jour")
        return True
    except OSError as e:
        log.warning("Mise à jour du démarrage automatique impossible : %s", e)
        return False
