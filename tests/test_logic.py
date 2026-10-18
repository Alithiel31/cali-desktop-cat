"""Tests : python -m unittest discover -s tests -v

Tournent aussi hors Windows : Qt en mode « offscreen » et de fausses fenêtres à la place de l'API Windows.
"""
import glob
import os
import random
import sys
import tempfile
import unittest
from unittest import mock

if sys.platform != "win32":
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PySide6.QtCore import QPoint, QRect
from PySide6.QtWidgets import QApplication

from desktopcat import hats, winapi
from desktopcat import pet as pet_module
from desktopcat.game import Game
from desktopcat.pet import Pet
from desktopcat.screens import ScreenInfo
from desktopcat.store import Store
from desktopcat.surfaces import LWin, compute_surfaces, subtract
from desktopcat.widgets import Bubble, FxLayer, GiftBox

APP = QApplication.instance() or QApplication([])


class HatsTest(unittest.TestCase):
    def test_sprites_are_well_formed(self):
        for h in hats.HATS:
            for row in h.px:
                self.assertEqual(len(row), 10, f"{h.id}: ligne de {len(row)} colonnes")
                for ch in row:
                    self.assertTrue(ch in ".RS" or ch in h.pal, f"{h.id}: lettre {ch!r} sans couleur")
            self.assertIn(h.rarity, hats.RARITIES)
        self.assertEqual(len({h.id for h in hats.HATS}), len(hats.HATS))

    def test_every_rarity_has_a_hat(self):
        for r in hats.RARITIES:
            self.assertTrue([h for h in hats.HATS if h.rarity == r], r)

    def test_roll_distribution(self):
        rng, n, counts = random.Random(42), 100000, {}
        for _ in range(n):
            r = hats.roll_hat(rng).rarity
            counts[r] = counts.get(r, 0) + 1
        for key, info in hats.RARITIES.items():
            self.assertAlmostEqual(counts[key] / n * 100, info["weight"], delta=max(0.4, info["weight"] * 0.1), msg=key)


class SurfacesTest(unittest.TestCase):
    def test_subtract(self):
        self.assertEqual(subtract([(0, 100)], 40, 60), [(0, 40), (60, 100)])
        self.assertEqual(subtract([(0, 100)], -10, 200), [])
        self.assertEqual(subtract([(0, 100)], 100, 200), [(0, 100)])

    def test_occlusion_and_filters(self):
        work = (0, 0, 1000, 800)
        front = LWin(1, "devant", 300, 300, 600, 700)           # recouvre le milieu du bord haut de « derrière »
        back = LWin(2, "derrière", 100, 350, 900, 700)
        tiny_room = LWin(3, "trop haut", 100, 50, 900, 700)     # pas la place d'un chat de 140 px au-dessus
        maxed = LWin(4, "maximisée", 0, 0, 1000, 800, zoomed=True)
        s = compute_surfaces([front, back, tiny_room], work, headroom=140, min_width=100)
        by = {(x.hwnd, round(x.x0), round(x.x1)) for x in s}
        self.assertIn((1, 300, 600), by)
        self.assertIn((2, 100, 300), by)                         # bord de « derrière » coupé en deux par « devant »
        self.assertIn((2, 600, 900), by)
        self.assertNotIn(3, {x.hwnd for x in s})
        self.assertEqual(compute_surfaces([maxed], work, 140, 100), [])
        # une fenêtre maximisée au premier plan masque tout ce qui est dessous
        covered = compute_surfaces([LWin(9, "max", 0, 300, 1000, 800, zoomed=True), back], work, 140, 100)
        self.assertEqual(covered, [])


class StoreTest(unittest.TestCase):
    def test_roundtrip_and_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "s", "save.json")
            st = Store(path)
            st.data["hats"]["crown"] = 2
            st.data["settings"]["scale"] = 5
            st.add_app_seconds("firefox.exe", 7)
            self.assertTrue(st.save())
            again = Store(path)
            self.assertEqual(again.data["hats"], {"crown": 2})
            self.assertEqual(again.data["settings"]["scale"], 5)
            self.assertEqual(again.day()["apps"]["firefox.exe"], 7)
            with open(path, "w") as f:
                f.write("{pas du json")
            broken = Store(path)
            self.assertEqual(broken.data["hats"], {"crown": 2})      # restauré depuis la copie quotidienne
            self.assertIsNotNone(broken.recovered_from)
            self.assertEqual(len(glob.glob(path + ".*.bak")), 1)     # le fichier illisible est gardé, horodaté

    def test_unknown_or_badly_typed_settings_are_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "save.json")
            with open(path, "w") as f:
                f.write('{"settings": {"scale": "gros", "inconnu": 1, "perch_windows": false}, "hats": {"a": 0, "b": 3}}')
            st = Store(path)
            self.assertEqual(st.data["settings"]["scale"], 4)
            self.assertFalse(st.data["settings"]["perch_windows"])
            self.assertNotIn("inconnu", st.data["settings"])
            self.assertEqual(st.data["hats"], {"b": 3})


class FakeDesk:
    """Un faux bureau : une liste de fenêtres modifiable à la main."""

    def __init__(self):
        self.wins = {}

    def put(self, hwnd, rect, title="Fenêtre", zoomed=False):
        self.wins[hwnd] = (rect, title, zoomed)

    def list_windows(self, exclude=()):
        return [winapi.WinInfo(h, t, r, z) for h, (r, t, z) in self.wins.items()]

    def window_rect(self, hwnd):
        w = self.wins.get(hwnd)
        return None if w is None or w[2] else w[0]


class RealScreensTest(unittest.TestCase):
    """Le seul endroit où l'on regarde les vrais écrans : la fonction de production elle-même."""

    def test_qt_screens_describes_at_least_one_screen(self):
        screens = pet_module.qt_screens()
        self.assertGreaterEqual(len(screens), 1)
        for s in screens:
            self.assertGreater(s.geom[2] - s.geom[0], 0)
            self.assertGreater(s.dpr, 0)
            self.assertTrue(s.geom[0] <= s.work[0] and s.work[2] <= s.geom[2] + 1)     # zone utile dans l'écran


class FixedCursor:
    """Fausse souris à une abscisse donnée : sans elle, les tests dépendent de l'endroit où se trouve ta vraie souris."""

    def __init__(self, x: int = 960):
        self.x = x

    def pos(self):
        return QPoint(self.x, 400)


DEFAULT_SCREENS = (ScreenInfo((0, 0, 1920, 1080), (0, 0, 1920, 1040), 1.0),)     # un écran 1920 × 1080, barre des tâches 40 px


def _no_real_screens():
    raise AssertionError("Ce test lit les VRAIS écrans : crée le chat avec Pet(..., screens=lambda: [ScreenInfo(...)]) "
                         "(sinon il réussit ou échoue selon la machine).")


class GameTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(os.path.join(self.tmp.name, "save.json"))
        self.now = 1_000_000.0
        self.game = Game(self.store, clock=lambda: self.now)
        self.desk = FakeDesk()
        self.idle = 0.0
        self.fg = None
        patches = [
            mock.patch.object(winapi, "list_windows", self.desk.list_windows),
            mock.patch.object(winapi, "window_rect", self.desk.window_rect),
            mock.patch.object(winapi, "idle_seconds", lambda: self.idle),
            mock.patch.object(winapi, "foreground", lambda: self.fg),
            mock.patch.object(pet_module, "qt_screens", _no_real_screens),      # garde : jamais les vrais écrans en test
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(self.tmp.cleanup)

    def work(self, minutes: float) -> None:
        """Laisse passer `minutes` minutes devant l'ordinateur : un tick d'une seconde à la fois, horloge comprise."""
        for _ in range(int(minutes * 60)):
            self.now += 1
            self.game.tick()


class GameTest(GameTestCase):
    def test_gift_claim_and_sell(self):
        self.assertIsNone(self.game.claim_gift())
        self.game.data["gift_pending"] = True
        res = self.game.claim_gift()
        self.assertTrue(res["is_new"])
        self.assertEqual(self.game.data["equipped"], res["hat"].id)
        self.assertFalse(self.game.data["gift_pending"])
        hat_id = res["hat"].id
        self.assertFalse(self.game.sell(hat_id))                 # pas de doublon : rien à vendre
        self.game.data["hats"][hat_id] = 2
        self.assertTrue(self.game.sell(hat_id))
        self.assertEqual(self.game.data["hats"][hat_id], 1)
        self.assertEqual(self.game.data["fish"], hats.RARITIES[res["hat"].rarity]["sell"])
        self.assertFalse(self.game.equip("inconnu"))

    def test_tick_activity_gift_and_sleep(self):
        events = []
        self.game.gift_ready.connect(lambda: events.append("gift"))
        self.game.sleeping_changed.connect(lambda v: events.append("sleep" if v else "wake"))
        self.game.settings["gift_every_min"] = 5
        for _ in range(300):
            self.game.tick()
        self.assertEqual(self.store.day()["active"], 300)
        self.assertTrue(self.game.data["gift_pending"])
        self.assertEqual(events, ["gift"])
        self.idle = 400                                          # plus de 5 min sans rien toucher
        self.game.tick()
        self.assertTrue(self.game.sleeping)
        self.idle = 1
        self.game.tick()
        self.assertEqual(events, ["gift", "sleep", "wake"])
        self.assertEqual(self.store.day()["active"], 301)        # le temps d'absence ne compte pas

    def test_app_time_ignores_own_process(self):
        self.fg = winapi.Foreground(5, os.getpid(), "python.exe", "Desktop Cat", (0, 0, 10, 10), "X")
        self.game.tick()
        self.assertEqual(self.store.day()["apps"], {})
        self.fg = winapi.Foreground(6, 1, "firefox.exe", "Mozilla", (0, 0, 10, 10), "X")
        self.game.tick()
        self.assertEqual(self.store.day()["apps"], {"firefox.exe": 1})

    def test_focus_session(self):
        done = []
        self.game.focus_finished.connect(done.append)
        self.game.start_focus(25)
        self.assertEqual(self.game.focus["total_min"], 25)
        self.work(25)
        self.assertIsNone(self.game.focus)
        self.assertEqual(done, [25])
        self.assertTrue(self.game.data["gift_pending"])
        self.assertEqual(self.game.data["fish"], 35)
        self.game.start_focus(10)
        self.game.stop_focus(False)                              # abandon : pas de récompense
        self.assertEqual(self.game.data["fish"], 35)

    def test_settings_are_clamped(self):
        self.game.set_setting("scale", 99)
        self.assertEqual(self.game.settings["scale"], 6)
        self.assertFalse(self.game.set_setting("nimporte", 1))
        self.assertFalse(self.game.set_setting("scale", "abc"))
        self.game.set_name("   ")
        self.assertEqual(self.game.data["name"], "Miso")

    def test_fullscreen_detection(self):
        mon = (0, 0, 1920, 1080)
        game = winapi.Foreground(1, 1, "jeu.exe", "Jeu", (0, 0, 1920, 1080), "UnityWndClass")
        desktop = winapi.Foreground(2, 1, "explorer.exe", "", (0, 0, 1920, 1080), "Progman")
        maxed = winapi.Foreground(3, 1, "x.exe", "Max", (0, 0, 1920, 1032), "Win")
        self.assertTrue(winapi.is_fullscreen(game, mon))
        self.assertFalse(winapi.is_fullscreen(desktop, mon))
        self.assertFalse(winapi.is_fullscreen(maxed, mon))
        self.assertFalse(winapi.is_fullscreen(None, mon))


class PetTest(GameTestCase):
    def setUp(self):
        super().setUp()
        self.bubble, self.gift = Bubble(), GiftBox(4)
        self.fxl = FxLayer(QRect(0, 0, 800, 800))
        # Écrans et souris factices : le résultat ne dépend ni de ta configuration d'écrans ni de ta souris.
        cursor = mock.patch.object(pet_module, "QCursor", FixedCursor())
        cursor.start()
        self.addCleanup(cursor.stop)
        self.pet = Pet(self.game, self.bubble, self.gift, self.fxl, rng=random.Random(1),
                       screens=lambda: list(DEFAULT_SCREENS))
        self.pet.loop.stop()
        self.pet.anim.stop()
        self.addCleanup(lambda: [w.close() for w in (self.pet, self.bubble, self.gift, self.fxl)])
        self.floor = self.pet.floor_y

    def run_steps(self, n=120, dt=1 / 60):
        for _ in range(n):
            self.pet.step(dt)

    def run_until(self, cond, n=600, dt=1 / 60):
        """Avance jusqu'à ce que `cond()` soit vrai (échoue au bout de n pas) : évite de dépendre du hasard."""
        for _ in range(n):
            if cond():
                return
            self.pet.step(dt)
        self.fail("condition jamais atteinte")

    def put_cat(self, cx, fy, state="fall"):
        self.pet.fx = cx - self.pet.CW / 2
        self.pet.fy = fy
        self.pet.stand = None
        self.pet.state = state
        self.pet.vy = 0.0

    def test_starts_on_the_floor_and_renders(self):
        self.run_steps(30)
        self.assertIsNone(self.pet.stand)
        self.assertEqual(self.pet.fy, self.floor)
        self.assertFalse(self.pet.grab().isNull())

    def test_falls_and_lands_on_a_window(self):
        self.desk.put(111, (100, 400, 700, 700))
        self.put_cat(400, 100)
        self.run_steps(120)
        self.assertEqual(self.pet.stand, 111)
        self.assertAlmostEqual(self.pet.fy, 400, delta=0.5)

    def test_misses_a_window_and_lands_on_the_floor(self):
        self.desk.put(111, (100, 400, 700, 700))
        self.put_cat(750, 100)                                   # à droite de la fenêtre
        self.run_steps(120)
        self.assertIsNone(self.pet.stand)
        self.assertEqual(self.pet.fy, self.floor)

    def test_follows_a_moving_window(self):
        self.desk.put(111, (100, 400, 700, 700))
        self.put_cat(400, 100)
        self.run_steps(120)
        self.pet.state, self.pet.timer = "nap", 99               # il ne bouge plus tout seul
        x0 = self.pet.fx
        self.desk.put(111, (180, 380, 780, 700))                 # la fenêtre glisse de 80 px à droite et monte de 20
        self.run_steps(3)
        self.assertEqual(self.pet.stand, 111)
        self.assertAlmostEqual(self.pet.fx, x0 + 80, delta=0.5)
        self.assertAlmostEqual(self.pet.fy, 380, delta=0.5)

    def test_falls_when_the_window_drops_away_or_closes(self):
        self.desk.put(111, (100, 400, 700, 700))
        self.put_cat(400, 100)
        self.run_steps(120)
        self.pet.state, self.pet.timer = "nap", 99
        self.desk.put(111, (100, 600, 700, 760))                 # la fenêtre descend vite : le chat décroche
        self.run_steps(2)
        self.assertEqual(self.pet.state, "fall")
        self.run_steps(120)
        self.assertEqual(self.pet.stand, 111)                    # et se rattrape sur la fenêtre plus bas
        self.assertAlmostEqual(self.pet.fy, 600, delta=0.5)
        self.pet.state, self.pet.timer = "nap", 99
        del self.desk.wins[111]                                  # fenêtre fermée
        self.run_steps(120)
        self.assertIsNone(self.pet.stand)
        self.assertEqual(self.pet.fy, self.floor)

    def test_maximized_window_is_not_a_perch(self):
        self.desk.put(111, (0, 0, 800, 800), zoomed=True)
        self.put_cat(400, 50)
        self.run_steps(200)
        self.assertIsNone(self.pet.stand)

    def test_jump_to_another_window_and_back_down(self):
        self.desk.put(111, (100, 600, 700, 760))
        self.run_steps(30)
        self.assertTrue(self.pet._jump_somewhere(prefer_hwnd=111, reach_up=600))
        self.assertEqual(self.pet.state, "jump")
        self.run_until(lambda: self.pet.state != "jump")
        self.assertEqual(self.pet.stand, 111)
        self.assertAlmostEqual(self.pet.fy, 600, delta=0.5)
        self.pet.state = "idle"
        self.assertTrue(self.pet._jump_somewhere(reach_up=600))  # vers le sol
        self.run_until(lambda: self.pet.state != "jump")
        self.assertIsNone(self.pet.stand)

    def test_perching_can_be_disabled(self):
        self.desk.put(111, (100, 400, 700, 700))
        self.game.settings["perch_windows"] = False
        self.put_cat(400, 100)
        self.run_steps(120)
        self.assertIsNone(self.pet.stand)

    def test_dragging_then_dropping_above_a_window(self):
        self.desk.put(111, (100, 400, 700, 700))
        self.run_steps(10)
        self.pet.state = "drag"
        self.pet.fx, self.pet.fy = 300.0, 380.0
        self.run_steps(5)
        self.assertEqual(self.pet.state, "drag")
        self.pet.state = "fall"                                  # on lâche
        self.run_steps(60)
        self.assertEqual(self.pet.stand, 111)

    def test_gift_cycle(self):
        self.game.data["gift_pending"] = True
        self.run_steps(5)
        self.assertEqual(self.pet.state, "wait")
        self.assertTrue(self.pet.gift_visible)
        self.run_steps(60)
        self.assertEqual(self.pet.state, "wait")                 # il attend qu'on ouvre le cadeau
        self.pet._on_gift_clicked()
        self.assertFalse(self.pet.gift_visible)
        self.assertTrue(self.game.data["hats"])
        self.assertIn("Nouveau chapeau", self.bubble.text())
        self.assertFalse(self.game.data["gift_pending"])

    def test_focus_session_puts_the_cat_to_work(self):
        self.game.start_focus(5)
        # il rejoint le bord de son écran : la durée dépend de la taille des vrais écrans, donc on attend l'état
        self.run_until(lambda: self.pet.state == "work", n=6000)
        self.assertEqual(self.pet.state, "work")
        self.assertIn("⏱", self.bubble.text())
        self.assertFalse(self.pet.grab().isNull())
        self.game.stop_focus(False)
        self.run_steps(3)
        self.assertEqual(self.pet.state, "idle")

    def test_sleep_and_wake(self):
        self.game.sleeping_changed.emit(True)
        self.assertEqual(self.pet.state, "sleep")
        self.run_steps(200)
        self.assertEqual(self.pet.state, "sleep")
        self.game.sleeping_changed.emit(False)
        self.assertEqual(self.pet.state, "idle")

    def test_gift_waits_while_the_user_is_away(self):
        self.game.sleeping_changed.emit(True)
        self.game.data["gift_pending"] = True
        self.run_steps(60)
        self.assertFalse(self.pet.gift_visible)
        self.game.sleeping_changed.emit(False)
        self.run_steps(5)
        self.assertTrue(self.pet.gift_visible)

    def test_fullscreen_hides_everything(self):
        self.game.fullscreen_changed.emit(True)
        self.assertTrue(self.pet.hidden)
        self.assertFalse(self.pet.isVisible())
        self.game.fullscreen_changed.emit(False)
        self.assertTrue(self.pet.isVisible())

    def test_follow_active_window(self):
        self.desk.put(111, (100, 600, 700, 760))
        self.game.settings["follow_active"] = True
        self.run_steps(30)
        self.fg = winapi.Foreground(111, 7, "bloc.exe", "Fenêtre", (100, 600, 700, 760), "Notepad")
        self.run_steps(60)
        self.assertIn(self.pet.state, ("jump", "idle"))
        self.run_until(lambda: self.pet.stand == 111)

    def test_changing_scale_resizes_the_cat(self):
        old = self.pet.width()
        self.game.set_setting("scale", 6)
        self.assertGreater(self.pet.width(), old)
        self.assertEqual(self.gift.width(), 16 * 6)

    def test_long_random_life_never_crashes(self):
        """Une heure de vie simulée, avec des fenêtres qui apparaissent, bougent et disparaissent."""
        rng = random.Random(7)
        for i in range(60 * 60 * 2):                              # 2 minutes à 30 Hz
            if i % 90 == 0:
                hwnd = rng.randint(1, 4)
                if rng.random() < 0.3 and hwnd in self.desk.wins:
                    del self.desk.wins[hwnd]
                else:
                    x, y = rng.randint(0, 300), rng.randint(200, 600)
                    self.desk.put(hwnd, (x, y, x + rng.randint(300, 500), y + 200))
            if i % 400 == 0:
                self.game.data["gift_pending"] = True
            self.pet.step(1 / 30)
            cx = self.pet.cx
            self.assertTrue(-1000 < cx < 2000 and 0 <= self.pet.fy <= self.floor + 1, (i, cx, self.pet.fy))
        self.assertTrue(self.pet.isVisible())


if __name__ == "__main__":
    unittest.main()
