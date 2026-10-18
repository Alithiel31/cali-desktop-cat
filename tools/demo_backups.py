"""Joue le scénario « sauvegarde abîmée » dans un dossier temporaire (ta vraie sauvegarde n'est pas touchée).

    python tools/demo_backups.py
"""
import os
import sys
import tempfile
from unittest import mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from desktopcat import store as store_module  # noqa: E402
from desktopcat.store import Store  # noqa: E402


def show(title: str, folder: str) -> None:
    print(f"\n{title}")
    for root, _dirs, files in sorted(os.walk(folder)):
        for name in sorted(files):
            print("   ", os.path.relpath(os.path.join(root, name), folder))


with tempfile.TemporaryDirectory() as tmp:
    path = os.path.join(tmp, "save.json")
    day = ["2026-10-01"]
    with mock.patch.object(store_module, "_today", lambda: day[0]):
        st = Store(path)
        st.data["fish"] = 120
        st.save()
        print("1. Première partie : 120 croquettes, sauvegardées.")

        day[0] = "2026-10-02"
        st = Store(path)                       # lancement du lendemain : copie quotidienne de la veille
        st.data["fish"] = 150
        st.save()
        print("2. Lendemain : 150 croquettes. Une copie de la veille a été faite.")

        with open(path, "w") as f:
            f.write("{fichier abîmé")
        print("3. On abîme le fichier de sauvegarde...")

        st = Store(path)
        print(f"4. Relance : {st.data['fish']} croquettes (restaurées depuis {os.path.basename(st.recovered_from)}).")
        show("Fichiers :", tmp)
