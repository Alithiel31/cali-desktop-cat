"""Tests des outils de build : métadonnées Windows de l'exécutable.

    python -m unittest discover -s tests -v
"""
import importlib.util
import os
import sys
import tempfile
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, ROOT)


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, "tools", f"{name}.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mvf = _load("make_version_file")


class VersionFileTest(unittest.TestCase):
    def test_version_tuple(self):
        self.assertEqual(mvf.version_tuple("0.4.1"), (0, 4, 1, 0))
        self.assertEqual(mvf.version_tuple("1"), (1, 0, 0, 0))
        self.assertEqual(mvf.version_tuple("1.2.3.4"), (1, 2, 3, 4))
        for bad in ("1.2.3.4.5", "1.x", "70000.0", "1.-2"):
            with self.assertRaises(ValueError, msg=bad):
                mvf.version_tuple(bad)

    def test_content_follows_the_app_version(self):
        from desktopcat import __version__
        with tempfile.TemporaryDirectory() as tmp:
            with open(mvf.main(os.path.join(tmp, "v.txt")), encoding="utf-8") as f:
                text = f.read()
        v = mvf.version_tuple(__version__)
        self.assertIn(f"filevers={v}", text)
        self.assertIn(f"prodvers={v}", text)
        self.assertIn("StringStruct('ProductName', 'Desktop Cat')", text)
        self.assertIn(f"StringStruct('ProductVersion', '{__version__}')", text)
        self.assertIn("StringStruct('OriginalFilename', 'DesktopCat.exe')", text)

    def test_it_is_valid_python_syntax(self):
        """PyInstaller évalue ce fichier : il doit au moins être une expression Python valide."""
        compile(mvf.version_info("0.4.1"), "version_info.txt", "eval")


if __name__ == "__main__":
    unittest.main()
