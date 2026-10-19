"""Tests du lancement avec Windows, sur un faux registre (le vrai n'est jamais touché, même sous Windows).

    python -m unittest discover -s tests -v
"""
import os
import sys
import tempfile
import unittest
from unittest import mock

if sys.platform != "win32":
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PySide6.QtWidgets import QApplication

from desktopcat import autostart
from desktopcat.game import Game
from desktopcat.store import Store

APP = QApplication.instance() or QApplication([])


class FakeWinreg:
    """Le strict nécessaire de `winreg`, en mémoire : {chemin de clé: {nom: valeur}}."""
    HKEY_CURRENT_USER = "HKCU"
    KEY_READ, KEY_SET_VALUE = 1, 2
    REG_SZ, REG_BINARY = 1, 3

    def __init__(self):
        self.keys: dict = {}
        self.fail = False

    class _Key:
        def __init__(self, store):
            self.store = store

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def _check(self):
        if self.fail:
            raise PermissionError("accès refusé")

    def CreateKey(self, root, path):
        self._check()
        return self._Key(self.keys.setdefault(path, {}))

    def OpenKey(self, root, path, reserved=0, access=0):
        self._check()
        if path not in self.keys:
            raise FileNotFoundError(path)
        return self._Key(self.keys[path])

    def QueryValueEx(self, key, name):
        if name not in key.store:
            raise FileNotFoundError(name)
        return key.store[name], 0

    def SetValueEx(self, key, name, reserved, kind, value):
        key.store[name] = value

    def DeleteValue(self, key, name):
        if name not in key.store:
            raise FileNotFoundError(name)
        del key.store[name]

    # raccourcis pour les tests
    def run(self):
        return self.keys.get(autostart.RUN_KEY, {}).get(autostart.VALUE_NAME)

    def approved(self):
        return self.keys.get(autostart.APPROVED_KEY, {}).get(autostart.VALUE_NAME)

    def disable_in_task_manager(self):
        self.keys.setdefault(autostart.APPROVED_KEY, {})[autostart.VALUE_NAME] = bytes([0x03]) + bytes(11)


class AutostartTest(unittest.TestCase):
    def setUp(self):
        self.reg = FakeWinreg()
        p = mock.patch.object(autostart, "_reg", lambda: self.reg)
        p.start()
        self.addCleanup(p.stop)

    def test_approved_bytes(self):
        self.assertTrue(autostart.approved(None))                         # pas de valeur : activé
        self.assertTrue(autostart.approved(bytes([0x02]) + bytes(11)))
        self.assertTrue(autostart.approved(bytes([0x06]) + bytes(11)))
        self.assertFalse(autostart.approved(bytes([0x03]) + bytes(11)))   # désactivé dans le Gestionnaire des tâches
        self.assertFalse(autostart.approved(bytes([0x07]) + bytes(11)))

    def test_enable_and_disable(self):
        self.assertFalse(autostart.is_enabled())
        self.assertTrue(autostart.set_enabled(True))
        self.assertEqual(self.reg.run(), autostart._command())
        self.assertTrue(autostart.is_enabled())
        self.assertTrue(autostart.set_enabled(False))
        self.assertIsNone(self.reg.run())
        self.assertFalse(autostart.is_enabled())
        self.assertTrue(autostart.set_enabled(False))                    # déjà désactivé : pas d'erreur

    def test_task_manager_disabling_is_seen(self):
        autostart.set_enabled(True)
        self.reg.disable_in_task_manager()
        self.assertFalse(autostart.is_enabled())                         # la valeur Run est toujours là, pourtant

    def test_ticking_the_box_again_reenables_it(self):
        autostart.set_enabled(True)
        self.reg.disable_in_task_manager()
        autostart.set_enabled(True)
        self.assertEqual(self.reg.approved(), autostart.APPROVED_ON)
        self.assertTrue(autostart.is_enabled())

    def test_disabling_cleans_both_values(self):
        autostart.set_enabled(True)
        self.reg.disable_in_task_manager()
        autostart.set_enabled(False)
        self.assertIsNone(self.reg.run())
        self.assertIsNone(self.reg.approved())

    def test_moved_exe_gets_its_new_path(self):
        self.reg.keys[autostart.RUN_KEY] = {autostart.VALUE_NAME: '"C:\\ancien\\DesktopCat.exe"'}
        self.assertTrue(autostart.refresh_path())
        self.assertEqual(self.reg.run(), autostart._command())
        self.assertFalse(autostart.refresh_path())                       # déjà à jour : rien à écrire

    def test_refresh_does_not_enable_nor_override_the_task_manager(self):
        self.assertFalse(autostart.refresh_path())
        self.assertIsNone(self.reg.run())
        self.reg.keys[autostart.RUN_KEY] = {autostart.VALUE_NAME: '"ailleurs.exe"'}
        self.reg.disable_in_task_manager()
        autostart.refresh_path()
        self.assertFalse(autostart.is_enabled())                         # toujours désactivé

    def test_registry_errors(self):
        self.reg.fail = True
        with self.assertLogs("desktopcat.autostart", "ERROR"):
            self.assertFalse(autostart.set_enabled(True))
        with self.assertLogs("desktopcat.autostart", "WARNING"):
            self.assertIsNone(autostart.is_enabled())

    def test_outside_windows(self):
        with mock.patch.object(autostart, "_reg", lambda: None):
            self.assertIsNone(autostart.is_enabled())
            self.assertFalse(autostart.set_enabled(True))
            self.assertFalse(autostart.refresh_path())


class GameSyncTest(unittest.TestCase):
    def setUp(self):
        self.reg = FakeWinreg()
        p = mock.patch.object(autostart, "_reg", lambda: self.reg)
        p.start()
        self.addCleanup(p.stop)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.game = Game(Store(os.path.join(self.tmp.name, "save.json")))

    def test_the_box_follows_the_registry(self):
        self.assertTrue(self.game.set_setting("launch_at_startup", True))
        self.reg.disable_in_task_manager()
        self.game.sync_autostart()
        self.assertFalse(self.game.settings["launch_at_startup"])        # la case ne ment plus
        self.assertTrue(self.game.set_setting("launch_at_startup", True))
        self.assertTrue(autostart.is_enabled())

    def test_start_refreshes_the_path(self):
        self.reg.keys[autostart.RUN_KEY] = {autostart.VALUE_NAME: '"C:\\ancien\\DesktopCat.exe"'}
        self.game.start()
        self.game._timer.stop()
        self.assertEqual(self.reg.run(), autostart._command())
        self.assertTrue(self.game.settings["launch_at_startup"])          # activé ailleurs : la case suit

    def test_unreadable_registry_changes_nothing(self):
        self.game.settings["launch_at_startup"] = True
        with mock.patch.object(autostart, "_reg", lambda: None):
            self.game.sync_autostart()
        self.assertTrue(self.game.settings["launch_at_startup"])


if __name__ == "__main__":
    unittest.main()
