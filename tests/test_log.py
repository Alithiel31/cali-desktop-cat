"""Tests du journal d'erreurs : un plantage doit laisser une trace lisible.

    python -m unittest discover -s tests -v
"""
import logging
import os
import sys
import tempfile
import threading
import unittest

if sys.platform != "win32":
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PySide6.QtCore import QTimer, qWarning
from PySide6.QtWidgets import QApplication

from desktopcat import log
from desktopcat.store import Store

APP = QApplication.instance() or QApplication([])


class LogTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "sub", "desktopcat.log")      # le dossier n'existe pas encore
        self.hook_before = sys.excepthook
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(log.shutdown)

    def start(self):
        self.assertEqual(log.setup(self.path), self.path)

    @staticmethod
    def file_handlers():
        """Les handlers qui écrivent dans un fichier (le NullHandler du module est toujours là, lui)."""
        return [h for h in logging.getLogger(log.NAME).handlers if isinstance(h, logging.FileHandler)]

    def content(self):
        for h in self.file_handlers():
            h.flush()
        with open(self.path, encoding="utf-8") as f:
            return f.read()


class SetupTest(LogTestCase):
    def test_creates_the_file_and_records_the_startup(self):
        self.start()
        self.assertIn("Démarrage : Python", self.content())
        self.assertIn("PySide6", self.content())

    def test_setup_twice_does_not_duplicate_lines(self):
        self.start()
        self.start()
        self.assertEqual(self.content().count("Démarrage"), 1)
        self.assertEqual(len(self.file_handlers()), 1)

    def test_shutdown_restores_the_original_hooks(self):
        self.start()
        self.assertIsNot(sys.excepthook, self.hook_before)
        log.shutdown()
        self.assertIs(sys.excepthook, self.hook_before)
        self.assertEqual(self.file_handlers(), [])

    def test_unwritable_location_does_not_break_the_app(self):
        blocker = os.path.join(self.tmp.name, "fichier")
        open(blocker, "w").close()
        self.assertIsNone(log.setup(os.path.join(blocker, "desktopcat.log")))   # « dossier » qui est un fichier
        self.assertIs(sys.excepthook, self.hook_before)

    def test_default_path_is_next_to_the_save(self):
        from desktopcat.store import default_path
        self.assertEqual(os.path.dirname(log.log_path()), os.path.dirname(default_path()))


class CaptureTest(LogTestCase):
    def test_uncaught_exception_is_logged_with_its_traceback(self):
        self.start()
        try:
            raise ValueError("boum")
        except ValueError:
            with unittest_silenced_stderr():
                sys.excepthook(*sys.exc_info())
        text = self.content()
        self.assertIn("CRITICAL", text)
        self.assertIn("ValueError: boum", text)
        self.assertIn("Traceback", text)

    def test_error_inside_a_qt_slot_is_logged(self):
        self.start()
        QTimer.singleShot(0, lambda: 1 / 0)
        with unittest_silenced_stderr():
            for _ in range(5):
                APP.processEvents()
        self.assertIn("ZeroDivisionError", self.content())

    def test_error_in_a_thread_is_logged(self):
        self.start()

        def boom():
            raise RuntimeError("dans un fil")

        with unittest_silenced_stderr():
            t = threading.Thread(target=boom, name="essai")
            t.start()
            t.join()
        self.assertIn("RuntimeError: dans un fil", self.content())
        self.assertIn("essai", self.content())

    def test_qt_warnings_are_logged(self):
        self.start()
        qWarning("avertissement de test")
        self.assertIn("WARNING desktopcat: Qt : avertissement de test", self.content())

    def test_keyboard_interrupt_is_not_logged_as_a_crash(self):
        self.start()
        with unittest_silenced_stderr():
            sys.excepthook(KeyboardInterrupt, KeyboardInterrupt(), None)
        self.assertNotIn("CRITICAL", self.content())


class AppErrorsTest(LogTestCase):
    def test_failed_save_is_logged(self):
        self.start()
        blocker = os.path.join(self.tmp.name, "fichier")
        open(blocker, "w").close()
        store = Store(os.path.join(blocker, "save.json"))                      # impossible d'y écrire
        self.assertFalse(store.save())
        self.assertIn("Sauvegarde impossible", self.content())

    def test_corrupted_save_is_logged_and_set_aside(self):
        self.start()
        save = os.path.join(self.tmp.name, "save.json")
        with open(save, "w", encoding="utf-8") as f:
            f.write("{pas du json")
        Store(save)
        self.assertTrue(os.path.exists(save + ".bak"))
        self.assertIn("Sauvegarde illisible", self.content())


class unittest_silenced_stderr:
    """Les crochets d'origine écrivent la trace sur stderr : on la masque pour ne pas polluer la sortie des tests."""

    def __enter__(self):
        self._old = sys.stderr
        sys.stderr = open(os.devnull, "w")

    def __exit__(self, *exc):
        sys.stderr.close()
        sys.stderr = self._old


if __name__ == "__main__":
    unittest.main()
