"""Journal d'erreurs : `%APPDATA%/DesktopCat/desktopcat.log`.

Lancée avec `pythonw` ou en exécutable sans console, l'appli n'a nulle part où afficher ses erreurs. Ce module les
écrit dans un fichier : exceptions non gérées (y compris dans les slots Qt), messages d'avertissement de Qt, et
plantages fatals de l'interpréteur (`<journal>.crash`, via faulthandler).

Un journal ne doit jamais empêcher l'appli de démarrer : si le fichier est inaccessible, `setup` renvoie None.
"""
from __future__ import annotations

import faulthandler
import logging
import logging.handlers
import os
import platform
import sys
import threading

from PySide6 import __version__ as PYSIDE_VERSION
from PySide6.QtCore import QtMsgType, qInstallMessageHandler

from .store import default_path

NAME = "desktopcat"
MAX_BYTES = 1_000_000
BACKUPS = 2

_state: dict = {}


def log_path() -> str:
    return os.path.join(os.path.dirname(default_path()), "desktopcat.log")


def _qt_level(kind) -> int:
    return {QtMsgType.QtDebugMsg: logging.DEBUG, QtMsgType.QtInfoMsg: logging.INFO,
            QtMsgType.QtWarningMsg: logging.WARNING, QtMsgType.QtCriticalMsg: logging.ERROR,
            QtMsgType.QtFatalMsg: logging.CRITICAL}.get(kind, logging.WARNING)


def setup(path: str | None = None, level: int = logging.INFO) -> str | None:
    """Active le journal. Renvoie le chemin du fichier, ou None s'il est impossible de l'écrire. Idempotent."""
    if _state:
        return _state["path"]
    path = path or log_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        handler = logging.handlers.RotatingFileHandler(path, maxBytes=MAX_BYTES, backupCount=BACKUPS, encoding="utf-8")
        crash = open(path + ".crash", "a", encoding="utf-8")
    except OSError:
        return None
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger = logging.getLogger(NAME)
    logger.setLevel(level)
    logger.addHandler(handler)

    old_hook, old_thread_hook = sys.excepthook, threading.excepthook

    def on_exception(exc_type, exc, tb):
        if not issubclass(exc_type, KeyboardInterrupt):
            logger.critical("Exception non gérée", exc_info=(exc_type, exc, tb))
        old_hook(exc_type, exc, tb)

    def on_thread_exception(args):
        logger.critical("Exception non gérée dans le fil « %s »",
                        getattr(args.thread, "name", "?"), exc_info=(args.exc_type, args.exc_value, args.exc_traceback))
        old_thread_hook(args)

    def on_qt_message(kind, _context, message):
        logger.log(_qt_level(kind), "Qt : %s", message)

    sys.excepthook, threading.excepthook = on_exception, on_thread_exception
    qInstallMessageHandler(on_qt_message)
    faulthandler.enable(file=crash, all_threads=True)
    _state.update(path=path, handler=handler, crash=crash, hooks=(old_hook, old_thread_hook), logger=logger)

    logger.info("Démarrage : Python %s, PySide6 %s, %s%s", platform.python_version(), PYSIDE_VERSION,
                platform.platform(), " (exécutable)" if getattr(sys, "frozen", False) else "")
    return path


def shutdown() -> None:
    """Désactive le journal et remet les crochets d'origine (utile aux tests)."""
    if not _state:
        return
    logger, handler = _state["logger"], _state["handler"]
    logger.info("Arrêt")
    sys.excepthook, threading.excepthook = _state["hooks"]
    qInstallMessageHandler(None)
    faulthandler.disable()
    logger.removeHandler(handler)
    handler.close()
    _state["crash"].close()
    _state.clear()
