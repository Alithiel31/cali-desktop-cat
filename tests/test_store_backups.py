"""Tests des protections de la sauvegarde : copies horodatées, copie quotidienne, restauration, migrations.

    python -m unittest discover -s tests -v
"""
import glob
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from desktopcat import store as store_module
from desktopcat.store import KEEP_CORRUPT, KEEP_DAILY, Store


class BackupTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, "save.json")
        self.day = ["2026-10-01"]
        self.stamp = [0]
        for name, fake in (("_today", lambda: self.day[0]), ("_stamp", self.next_stamp)):
            p = mock.patch.object(store_module, name, fake)
            p.start()
            self.addCleanup(p.stop)

    def next_stamp(self):
        self.stamp[0] += 1
        return f"2026-10-01_10-00-{self.stamp[0]:02d}"

    def write(self, obj, path=None):
        with open(path or self.path, "w", encoding="utf-8") as f:
            if isinstance(obj, str):
                f.write(obj)
            else:
                json.dump(obj, f)

    def read(self, path=None):
        with open(path or self.path, encoding="utf-8") as f:
            return json.load(f)

    def corrupt(self):
        self.write("{pas du json")

    def daily(self):
        return sorted(os.path.basename(p) for p in glob.glob(os.path.join(self.tmp.name, "backups", "*.json")))

    def aside(self):
        return sorted(glob.glob(self.path + ".????-??-??_??-??-??.bak"))


class CorruptFileTest(BackupTestCase):
    def test_unreadable_file_is_set_aside_under_a_timestamped_name(self):
        self.corrupt()
        st = Store(self.path)
        self.assertEqual(st.data["fish"], 0)                     # repart de zéro : rien à restaurer
        self.assertIsNone(st.recovered_from)
        self.assertFalse(os.path.exists(self.path))
        self.assertEqual(self.aside(), [self.path + ".2026-10-01_10-00-01.bak"])
        with open(self.aside()[0], encoding="utf-8") as f:
            self.assertEqual(f.read(), "{pas du json")           # le contenu est intact, récupérable à la main

    def test_only_the_latest_copies_are_kept(self):
        for _ in range(KEEP_CORRUPT + 2):
            self.corrupt()
            Store(self.path)
        kept = self.aside()
        self.assertEqual(len(kept), KEEP_CORRUPT)
        self.assertTrue(kept[-1].endswith(f"{KEEP_CORRUPT + 2:02d}.bak"))      # les plus récentes
        self.assertFalse(any(p.endswith("01.bak") for p in kept))

    def test_json_that_is_not_an_object_counts_as_corrupt(self):
        self.write("[1, 2, 3]")
        Store(self.path)
        self.assertEqual(len(self.aside()), 1)

    def test_no_file_means_a_fresh_start_without_any_backup(self):
        st = Store(self.path)
        self.assertEqual(st.data["fish"], 0)
        self.assertEqual(self.aside(), [])
        self.assertFalse(os.path.exists(os.path.join(self.tmp.name, "backups")))


class DailyBackupTest(BackupTestCase):
    def test_first_launch_of_the_day_copies_the_file(self):
        self.write({"fish": 12})
        Store(self.path)
        self.assertEqual(self.daily(), ["save-2026-10-01.json"])
        self.assertEqual(self.read(os.path.join(self.tmp.name, "backups", "save-2026-10-01.json"))["fish"], 12)

    def test_second_launch_the_same_day_keeps_the_first_copy(self):
        """La copie du jour est l'état de la veille au soir : elle ne doit pas suivre les modifications du jour."""
        self.write({"fish": 12})
        Store(self.path)
        self.write({"fish": 99})
        Store(self.path)
        self.assertEqual(self.read(os.path.join(self.tmp.name, "backups", "save-2026-10-01.json"))["fish"], 12)

    def test_only_the_latest_days_are_kept(self):
        self.write({"fish": 1})
        for d in range(1, KEEP_DAILY + 4):
            self.day[0] = f"2026-10-{d:02d}"
            Store(self.path)
        names = self.daily()
        self.assertEqual(len(names), KEEP_DAILY)
        self.assertEqual(names[-1], f"save-2026-10-{KEEP_DAILY + 3:02d}.json")
        self.assertNotIn("save-2026-10-01.json", names)

    def test_unwritable_backup_folder_does_not_stop_the_app(self):
        open(os.path.join(self.tmp.name, "backups"), "w").close()                # un fichier à la place du dossier
        self.write({"fish": 5})
        self.assertEqual(Store(self.path).data["fish"], 5)


class RestoreTest(BackupTestCase):
    def test_corrupt_file_is_restored_from_the_latest_daily_copy(self):
        self.write({"fish": 40, "hats": {"crown": 1}})
        Store(self.path)                                         # crée la copie du jour
        self.corrupt()
        st = Store(self.path)
        self.assertEqual(st.data["fish"], 40)
        self.assertEqual(st.data["hats"], {"crown": 1})
        self.assertTrue(st.recovered_from.endswith("save-2026-10-01.json"))
        self.assertEqual(len(self.aside()), 1)                   # l'illisible est gardé aussi
        self.assertTrue(st.save())                               # et la sauvegarde principale revient
        self.assertEqual(self.read()["fish"], 40)

    def test_the_newest_usable_copy_wins(self):
        self.write({"fish": 1})
        Store(self.path)
        self.day[0] = "2026-10-02"
        self.write({"fish": 2})
        Store(self.path)
        self.day[0] = "2026-10-03"
        self.corrupt()
        self.assertEqual(Store(self.path).data["fish"], 2)

    def test_a_damaged_copy_is_skipped_for_an_older_one(self):
        self.write({"fish": 1})
        Store(self.path)
        self.day[0] = "2026-10-02"
        self.write({"fish": 2})
        Store(self.path)
        self.write("{abîmée", os.path.join(self.tmp.name, "backups", "save-2026-10-02.json"))
        self.corrupt()
        st = Store(self.path)
        self.assertEqual(st.data["fish"], 1)
        self.assertTrue(st.recovered_from.endswith("save-2026-10-01.json"))

    def test_no_usable_copy_means_a_fresh_start(self):
        os.makedirs(os.path.join(self.tmp.name, "backups"))
        self.write("{abîmée", os.path.join(self.tmp.name, "backups", "save-2026-10-01.json"))
        self.corrupt()
        st = Store(self.path)
        self.assertEqual(st.data["fish"], 0)
        self.assertIsNone(st.recovered_from)


class MigrationTest(BackupTestCase):
    def patch_schema(self, version, migrations):
        for name, value in (("SCHEMA_VERSION", version), ("MIGRATIONS", migrations)):
            p = mock.patch.object(store_module, name, value)
            p.start()
            self.addCleanup(p.stop)

    def test_current_version_needs_no_migration_and_no_extra_copy(self):
        self.write({"version": 1, "fish": 3})
        Store(self.path)
        self.assertEqual(glob.glob(self.path + ".v*.bak"), [])

    def test_old_file_is_migrated_step_by_step(self):
        def v1_to_v2(d):
            d["fish"] = d.pop("croquettes")                     # renommage d'un champ
            return d

        def v2_to_v3(d):
            d["name"] = d["name"].upper()
            return d

        self.patch_schema(3, {1: v1_to_v2, 2: v2_to_v3})
        self.write({"version": 1, "croquettes": 7, "name": "miso"})
        st = Store(self.path)
        self.assertEqual((st.data["fish"], st.data["name"], st.data["version"]), (7, "MISO", 3))
        self.assertTrue(st.save())
        self.assertEqual(self.read()["version"], 3)

    def test_file_is_copied_before_it_is_migrated(self):
        self.patch_schema(2, {1: lambda d: d})
        self.write({"version": 1, "fish": 7})
        Store(self.path)
        self.assertEqual(self.read(self.path + ".v1.bak"), {"version": 1, "fish": 7})

    def test_pre_migration_copy_is_never_overwritten(self):
        self.patch_schema(2, {1: lambda d: d})
        self.write({"version": 1, "fish": 7})
        Store(self.path)
        self.write({"version": 1, "fish": 8})
        Store(self.path)
        self.assertEqual(self.read(self.path + ".v1.bak")["fish"], 7)

    def test_file_without_a_version_is_version_1(self):
        self.patch_schema(2, {1: lambda d: {**d, "fish": d["fish"] + 100}})
        self.write({"fish": 1})
        self.assertEqual(Store(self.path).data["fish"], 101)

    def test_nonsense_version_is_version_1(self):
        self.patch_schema(2, {1: lambda d: {**d, "fish": d["fish"] + 100}})
        for bad in ("abc", None, True, -4, 0, 1.5):
            self.write({"version": bad, "fish": 1})
            self.assertEqual(Store(self.path).data["fish"], 101, bad)

    def test_failing_migration_does_not_lose_the_save(self):
        def broken(_d):
            raise RuntimeError("bug de migration")

        self.patch_schema(2, {1: broken})
        self.write({"version": 1, "fish": 9})
        st = Store(self.path)
        self.assertEqual(st.data["fish"], 9)                     # chargée telle quelle, sans planter
        self.assertTrue(os.path.exists(self.path + ".v1.bak"))

    def test_missing_migration_step_does_not_crash(self):
        self.patch_schema(3, {2: lambda d: d})                  # rien pour passer de 1 à 2
        self.write({"version": 1, "fish": 9})
        self.assertEqual(Store(self.path).data["fish"], 9)

    def test_file_from_a_newer_app_is_preserved(self):
        self.write({"version": 99, "fish": 5, "champ_futur": {"x": 1}})
        st = Store(self.path)
        self.assertEqual(st.data["fish"], 5)
        self.assertTrue(st.save())                               # l'appli réécrit sans le champ qu'elle ne connaît pas...
        self.assertNotIn("champ_futur", self.read())
        self.assertEqual(self.read(self.path + ".v99.bak")["champ_futur"], {"x": 1})   # ...mais l'original est gardé

    def test_migration_also_applies_to_a_restored_copy(self):
        self.write({"version": 1, "fish": 4})
        Store(self.path)                                         # copie quotidienne en v1
        self.patch_schema(2, {1: lambda d: {**d, "fish": d["fish"] * 10}})
        self.corrupt()
        st = Store(self.path)
        self.assertEqual(st.data["fish"], 40)
        self.assertEqual(st.data["version"], 2)

    def test_saved_file_always_carries_the_current_version(self):
        st = Store(self.path)
        self.assertTrue(st.save())
        self.assertEqual(self.read()["version"], store_module.SCHEMA_VERSION)


if __name__ == "__main__":
    unittest.main()
