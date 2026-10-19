"""Tests du gameplay : chapeaux saisonniers, humeur et croquettes, pauses (Pomodoro), chasse au curseur,
raccourci clavier global.

    python -m unittest discover -s tests -v
"""
import json
import os
import random
import sys
import tempfile
import unittest
from datetime import date, datetime
from unittest import mock

if sys.platform != "win32":
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PySide6.QtCore import QPoint, QRect
from PySide6.QtWidgets import QApplication

from desktopcat import hats, hotkey, hunt, phrases
from desktopcat import pet as pet_module
from desktopcat.game import (FEED_COST, FEED_GAIN, MIN_REWARD_MIN, MOOD_DECAY_S, MOOD_FULL, MOOD_HAPPY,
                             MOOD_HUNGRY, PET_MOOD_CAP)
from desktopcat.panel import Panel
from desktopcat.pet import Pet
from desktopcat.store import Store
from desktopcat.widgets import Bubble, FxLayer, GiftBox
from test_logic import DEFAULT_SCREENS, GameTestCase

APP = QApplication.instance() or QApplication([])


def ts(y, m, d):
    return datetime(y, m, d, 12).timestamp()


# ─────────────────────────────────────────────────────────── chapeaux saisonniers


class SeasonalHatTest(unittest.TestCase):
    def test_halloween_bounds(self):
        self.assertFalse(hats.in_season("halloween", date(2026, 10, 24)))
        self.assertTrue(hats.in_season("halloween", date(2026, 10, 25)))
        self.assertTrue(hats.in_season("halloween", date(2026, 10, 31)))
        self.assertTrue(hats.in_season("halloween", date(2026, 11, 2)))
        self.assertFalse(hats.in_season("halloween", date(2026, 11, 3)))

    def test_season_across_new_year(self):
        with mock.patch.dict(hats.SEASONS, {"hiver": ("Hiver", (12, 20), (1, 5))}):
            self.assertTrue(hats.in_season("hiver", date(2026, 12, 31)))
            self.assertTrue(hats.in_season("hiver", date(2027, 1, 3)))
            self.assertFalse(hats.in_season("hiver", date(2027, 1, 6)))

    def test_never_out_of_season(self):
        rng = random.Random(3)
        for today in (None, date(2026, 7, 14), date(2026, 11, 3)):
            for _ in range(5000):
                self.assertIsNone(hats.roll_hat(rng, today).season, today)

    def test_one_gift_in_five_during_the_season(self):
        rng, n = random.Random(5), 20000
        got = sum(hats.roll_hat(rng, date(2026, 10, 31)).id == "pumpkin" for _ in range(n))
        self.assertAlmostEqual(got / n, hats.SEASON_CHANCE, delta=0.02)

    def test_seasonal_hat_has_a_label(self):
        self.assertEqual(hats.season_label(hats.BY_ID["pumpkin"]), "Halloween")
        self.assertEqual(hats.season_label(hats.BY_ID["cap"]), "")


class SeasonalGiftTest(GameTestCase):
    def test_the_game_uses_its_own_clock_for_the_season(self):
        self.game.data["gifts_pending"] = 1
        self.now = ts(2026, 10, 31)
        with mock.patch.object(hats.random, "random", return_value=0.05):        # tirage « saisonnier »
            self.assertEqual(self.game.claim_gift()["hat"].id, "pumpkin")
        self.game.data["gifts_pending"] = 1
        self.now = ts(2026, 12, 15)
        with mock.patch.object(hats.random, "random", return_value=0.05):
            self.assertNotEqual(self.game.claim_gift()["hat"].id, "pumpkin")

    def test_wardrobe_shows_the_season_of_a_hat_not_found_yet(self):
        panel = Panel(self.game)
        self.addCleanup(panel.deleteLater)
        texts = [w.text() for w in panel.grid_host.findChildren(type(panel.title))]
        self.assertTrue(any("Halloween" in t for t in texts))


# ─────────────────────────────────────────────────────────── humeur et croquettes


class MoodTest(GameTestCase):
    def test_new_cat_is_neither_hungry_nor_full(self):
        self.assertEqual(self.game.mood, 50)
        self.assertEqual(self.game.mood_level(), "content")

    def test_mood_drops_only_while_the_user_is_there(self):
        self.work(30)
        self.assertEqual(self.game.mood, 50 - 30 * 60 // MOOD_DECAY_S)
        before = self.game.mood
        self.idle = 400
        self.work(30)
        self.assertEqual(self.game.mood, before)

    def test_mood_never_goes_below_zero(self):
        self.game.data["mood"] = 1
        self.work(60)
        self.assertEqual(self.game.mood, 0)
        self.assertEqual(self.game.mood_level(), "affamé")

    def test_feeding_costs_fish_and_raises_mood(self):
        seen = []
        self.game.fed.connect(lambda: seen.append(1))
        self.assertFalse(self.game.feed())                       # pas de croquettes
        self.game.data["fish"] = 12
        self.assertTrue(self.game.feed())
        self.assertEqual((self.game.data["fish"], self.game.mood), (12 - FEED_COST, 50 + FEED_GAIN))
        self.assertEqual(seen, [1])

    def test_a_full_cat_does_not_eat(self):
        self.game.data["fish"] = 100
        self.game.data["mood"] = MOOD_FULL
        self.assertFalse(self.game.can_feed())
        self.assertFalse(self.game.feed())
        self.assertEqual(self.game.data["fish"], 100)
        self.game.data["mood"] = MOOD_FULL - 1
        self.assertTrue(self.game.feed())
        self.assertEqual(self.game.mood, 100)                    # plafonné

    def test_petting_helps_a_little_but_not_beyond_its_cap(self):
        self.game.data["mood"] = PET_MOOD_CAP - 2
        for _ in range(10):
            self.game.petted()
        self.assertEqual(self.game.mood, PET_MOOD_CAP)
        self.game.data["mood"] = 90
        self.game.petted()
        self.assertEqual(self.game.mood, 90)

    def test_a_well_fed_cat_brings_gifts_faster(self):
        self.game.settings["gift_every_min"] = 5
        for mood, expected in ((50, 300), (90, 240)):              # 90 : il reste repu tout du long
            self.game.data.update(mood=mood, gifts_pending=0, gift_progress=0)
            self.game._bonus_acc = 0.0
            n = 0
            while not self.game.data["gifts_pending"]:
                self.game.tick()
                n += 1
            self.assertEqual(n, expected, mood)

    def test_mood_is_saved_and_cleaned(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "save.json")
            for raw, expected in ((None, 50), (-3, 50), ("x", 50), (250, 100), (72, 72)):
                with open(path, "w", encoding="utf-8") as f:
                    json.dump({"version": 2} if raw is None else {"version": 2, "mood": raw}, f)
                self.assertEqual(Store(path).data["mood"], expected, raw)


# ─────────────────────────────────────────────────────────── pauses (Pomodoro)


class BreakTest(GameTestCase):
    def setUp(self):
        super().setUp()
        self.events = []
        self.game.break_changed.connect(lambda b: self.events.append("start" if b else "stop"))
        self.game.break_finished.connect(lambda: self.events.append("finished"))
        self.notes = []
        self.game.notice.connect(lambda t, m: self.notes.append(m))

    def test_a_rewarded_session_is_followed_by_a_break(self):
        self.game.start_focus(25)
        self.work(25)
        self.assertEqual(self.game.brk["total_min"], 5)
        self.assertIn("Pause de 5 min", self.notes[-1])
        self.work(5)
        self.assertIsNone(self.game.brk)
        self.assertEqual(self.events, ["start", "stop", "finished"])
        self.assertIn("prêt", self.notes[-1])

    def test_break_length_is_a_setting(self):
        self.assertTrue(self.game.set_setting("break_min", 99))
        self.assertEqual(self.game.settings["break_min"], 30)
        self.game.set_setting("break_min", 10)
        self.game.start_focus(25)
        self.work(25)
        self.assertEqual(self.game.brk["total_min"], 10)

    def test_no_break_when_turned_off_or_not_earned(self):
        self.game.set_setting("focus_breaks", False)
        self.game.start_focus(25)
        self.work(25)
        self.assertIsNone(self.game.brk)
        self.game.set_setting("focus_breaks", True)
        self.game.start_focus(MIN_REWARD_MIN - 1)                # trop courte : ni cadeau ni pause
        self.work(MIN_REWARD_MIN - 1)
        self.assertIsNone(self.game.brk)
        self.idle = 400                                          # absent : il s'est déjà reposé
        self.game.start_focus(25)
        self.work(25)
        self.assertIsNone(self.game.brk)

    def test_starting_a_session_or_skipping_ends_the_break(self):
        self.game.start_focus(25)
        self.work(25)
        self.game.start_focus(25)
        self.assertIsNone(self.game.brk)
        self.game.focus = None
        self.game._start_break()
        self.game.skip_break()
        self.assertIsNone(self.game.brk)
        self.assertNotIn("finished", self.events)


# ─────────────────────────────────────────────────────────── le chat : repas, pause, chasse


class MovableCursor:
    def __init__(self, x=1500, y=300):
        self.x, self.y = x, y

    def pos(self):
        return QPoint(self.x, self.y)


class PetGameplayTest(GameTestCase):
    def setUp(self):
        super().setUp()
        self.cursor = MovableCursor()
        p = mock.patch.object(pet_module, "QCursor", self.cursor)
        p.start()
        self.addCleanup(p.stop)
        self.bubble, self.gift, self.fxl = Bubble(), GiftBox(4), FxLayer(QRect(0, 0, 800, 800))
        self.pet = Pet(self.game, self.bubble, self.gift, self.fxl, rng=random.Random(2),
                       screens=lambda: list(DEFAULT_SCREENS))
        self.pet.loop.stop()
        self.pet.anim.stop()
        self.addCleanup(lambda: [w.close() for w in (self.pet, self.bubble, self.gift, self.fxl)])
        self.floor = self.pet.floor_y
        self.place(500)

    def place(self, cx):
        p = self.pet
        p.fx, p.fy, p.stand, p.vy, p.state, p.timer = cx - p.CW / 2, self.floor, None, 0.0, "idle", 999.0

    def run_steps(self, n=60, dt=1 / 60):
        for _ in range(n):
            self.pet.step(dt)

    def run_until(self, cond, n=900):
        for _ in range(n):
            if cond():
                return
            self.pet.step(1 / 60)
        self.fail("condition jamais atteinte")

    # repas et humeur
    def test_feeding_makes_him_happy(self):
        self.game.data["fish"] = 10
        self.game.feed()
        self.assertIn("Miam", self.bubble.text())
        self.assertGreater(self.pet.happy_until, self.pet.t)

    def test_petting_raises_his_mood(self):
        self.pet._pet()
        self.assertEqual(self.game.mood, 51)

    def test_a_hungry_cat_asks_for_food(self):
        self.game.data["mood"] = MOOD_HUNGRY - 1
        self.pet.next_meow = 0
        self.run_steps(2)
        self.assertIn(self.bubble.text(), phrases.MEOWS["hungry"])

    # pause
    def test_break_timer_in_the_bubble(self):
        self.game.start_focus(25)
        self.now += 25 * 60
        self.game.focus["active"] = 25 * 60
        self.game.tick()
        self.assertIn("Pause de 5 min", self.bubble.text())
        self.game.data["gifts_pending"] = 0                      # cadeau de la session déjà ouvert
        self.pet._temp_until = 0
        self.run_steps(2)
        self.assertIn("☕", self.bubble.text())
        self.now += 5 * 60
        self.game.tick()
        self.assertIn("On s'y remet", self.bubble.text())

    # chasse
    def rest_cursor_at(self, x, y=None):
        """La souris bouge (le chat le voit), puis s'arrête en (x, y)."""
        self.run_steps(1)
        self.cursor.x, self.cursor.y = x, self.floor - 40 if y is None else y
        self.run_steps(1)

    def test_resting_cursor_within_reach_is_hunted(self):
        self.pet._hunt_cool = 0
        self.rest_cursor_at(800)
        self.pet.timer = 1.4                                     # il décidera après 1,4 s : souris au repos
        self.run_until(lambda: self.pet.state == "stalk")
        self.assertEqual(self.pet.dir, 1)
        self.run_until(lambda: self.pet.state == "jump", n=200)
        self.run_until(lambda: self.pet.state not in ("jump", "stalk"), n=200)
        self.assertAlmostEqual(self.pet.cx, 800, delta=2)
        self.assertEqual(self.pet.fy, self.floor)
        self.assertGreater(self.pet.happy_until, self.pet.t)
        self.assertGreater(self.pet._hunt_cool, self.pet.t + 20_000)   # il se repose avant la prochaine chasse

    def test_moving_the_cursor_during_the_stalk_saves_it(self):
        self.pet._hunt_cool = 0
        self.rest_cursor_at(800)
        self.pet.timer = 1.4
        self.run_until(lambda: self.pet.state == "stalk")
        self.cursor.x += 30
        self.run_steps(2)
        self.assertEqual(self.pet.state, "idle")
        self.run_steps(120)
        self.assertNotEqual(self.pet.state, "jump")

    def test_no_hunt_when_turned_off_too_far_or_cursor_never_moved(self):
        self.pet._hunt_cool = 0
        self.pet.timer = 1.4                                     # la souris n'a jamais bougé
        self.run_steps(120)
        self.assertNotEqual(self.pet.state, "stalk")
        for setup in (lambda: self.game.set_setting("hunt_cursor", False),
                      lambda: self.cursor.__setattr__("y", 200)):            # bien au-dessus de lui
            self.game.set_setting("hunt_cursor", True)
            self.place(500)
            self.rest_cursor_at(800)
            setup()
            self.pet.timer = 1.4
            self.run_steps(120)
            self.assertNotEqual(self.pet.state, "stalk")

    def test_no_hunt_during_focus(self):
        self.game.start_focus(25)
        self.place(500)
        self.pet._hunt_cool = 0
        self.rest_cursor_at(800)
        self.assertFalse(self.pet._try_hunt(0, 1920))


class HuntGeometryTest(unittest.TestCase):
    def test_resting(self):
        self.assertFalse(hunt.cursor_is_resting(10.0, None))
        self.assertFalse(hunt.cursor_is_resting(10.0, 9.5))      # vient de bouger
        self.assertTrue(hunt.cursor_is_resting(10.0, 8.0))
        self.assertFalse(hunt.cursor_is_resting(100.0, 8.0))     # oubliée là depuis longtemps

    def test_reach(self):
        args = dict(cat_cx=500, feet_y=1000, x0=0, x1=1920, cat_w=128, foot=140, scale=4)
        self.assertTrue(hunt.cursor_in_reach(800, 960, **args))
        self.assertFalse(hunt.cursor_in_reach(520, 960, **args))     # trop près : il l'a déjà sous le nez
        self.assertFalse(hunt.cursor_in_reach(1500, 960, **args))    # trop loin
        self.assertFalse(hunt.cursor_in_reach(800, 700, **args))     # trop haut
        self.assertFalse(hunt.cursor_in_reach(800, 1100, **args))    # sous la surface
        self.assertFalse(hunt.cursor_in_reach(800, 960, **{**args, "x1": 820}))   # hors de la surface


# ─────────────────────────────────────────────────────────── raccourci


class HotkeyTest(unittest.TestCase):
    def test_only_our_registered_hotkey_triggers(self):
        hk = hotkey.GlobalHotkey()
        seen = []
        hk.activated.connect(lambda: seen.append(1))
        self.assertFalse(hk.handle(hotkey.WM_HOTKEY, hotkey.HOTKEY_ID))     # pas enregistré
        hk.registered = True
        self.assertFalse(hk.handle(hotkey.WM_HOTKEY, 42))
        self.assertFalse(hk.handle(0x0100, hotkey.HOTKEY_ID))
        self.assertTrue(hk.handle(hotkey.WM_HOTKEY, hotkey.HOTKEY_ID))
        self.assertEqual(seen, [1])
        hk.unregister() if sys.platform != "win32" else setattr(hk, "registered", False)
        self.assertFalse(hk.registered)

    @unittest.skipIf(sys.platform == "win32", "hors Windows seulement")
    def test_unavailable_outside_windows(self):
        self.assertFalse(hotkey.GlobalHotkey().set_enabled(True))

    @unittest.skipUnless(sys.platform == "win32", "Windows seulement")
    def test_register_and_release_on_windows(self):
        hk = hotkey.GlobalHotkey()
        self.addCleanup(hk.unregister)
        if hk.set_enabled(True):                                 # peut être pris par une autre appli
            self.assertTrue(hk.registered)
            hk.set_enabled(False)
        self.assertFalse(hk.registered)


if __name__ == "__main__":
    unittest.main()
