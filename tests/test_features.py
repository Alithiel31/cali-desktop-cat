"""Tests des ajouts : sauvegarde robuste, récompenses, session de concentration persistante,
plusieurs écrans, bulles « miaou », clic simple / double, fermeture du panneau.

    python -m unittest discover -s tests -v
"""
import json
import os
import random
import sys
import tempfile
import unittest
from unittest import mock

if sys.platform != "win32":
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PySide6.QtCore import QEvent, QPoint, QPointF, QRect, Qt
from PySide6.QtGui import QCloseEvent, QColor, QMouseEvent, QPalette
from PySide6.QtWidgets import QApplication

from desktopcat import pet as pet_module, phrases, winapi
from desktopcat.game import MAX_TICK_S, MIN_REWARD_MIN, Game
from desktopcat.panel import Panel
from desktopcat.pet import Pet
from desktopcat.screens import ScreenInfo
from desktopcat.store import Store
from desktopcat.widgets import Bubble, FxLayer, GiftBox
from test_logic import GameTestCase

APP = QApplication.instance() or QApplication([])

ALL_MEOWS = {m for pool in phrases.MEOWS.values() for m in pool}


class FixedCursor:
    """Fausse souris à une abscisse donnée : sans elle, les tests dépendent de l'endroit où se trouve ta vraie souris."""

    def __init__(self, x: int):
        self.x = x

    def pos(self):
        return QPoint(self.x, 400)


def screen(l, t, r, b, dpr=1.0, work_bottom=None):
    return ScreenInfo((l, t, r, b), (l, t, r, work_bottom if work_bottom is not None else b), dpr)


# ─────────────────────────────────────────────────────────── sauvegarde


class StoreRobustnessTest(unittest.TestCase):
    def write(self, tmp, obj):
        path = os.path.join(tmp, "save.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f)
        return path

    def test_hostile_save_file_loads_with_sane_values(self):
        hostile = {
            "name": 123, "fur": ["x"], "fish": "beaucoup", "gift_progress": -5, "gift_pending": "oui",
            "equipped": "chapeau_fantome", "hats": {"crown": 2, "halo": "x", "bow": 0, "cap": 1.9},
            "days": {"2026-01-01": "oups", "2026-01-02": {"active": "x", "apps": {"a.exe": -1, "b.exe": 5}}},
            "focus": {"ends_at": "demain", "total_min": 25},
        }
        with tempfile.TemporaryDirectory() as tmp:
            st = Store(self.write(tmp, hostile))
        d = st.data
        self.assertEqual(d["name"], "Miso")
        self.assertEqual(d["fur"], "ecaille")
        self.assertEqual((d["fish"], d["gift_progress"], d["gift_pending"]), (0, 0, False))
        self.assertIsNone(d["equipped"])                            # on ne porte pas un chapeau qu'on n'a pas
        self.assertEqual(d["hats"], {"crown": 2, "cap": 1})
        self.assertEqual(d["days"]["2026-01-01"], {"active": 0, "focus": 0, "gifts": 0, "apps": {}})
        self.assertEqual(d["days"]["2026-01-02"]["apps"], {"b.exe": 5})
        self.assertIsNone(d["focus"])

    def test_game_runs_on_a_hostile_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            st = Store(self.write(tmp, {"days": {"x": []}, "fish": None, "equipped": 4}))
            game = Game(st)
            with mock.patch.object(winapi, "idle_seconds", lambda: 0.0), \
                    mock.patch.object(winapi, "foreground", lambda: None):
                game.tick()
            self.assertEqual(st.day()["active"], 1)

    def test_valid_data_survives_a_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "save.json")
            st = Store(path)
            st.data.update(name="Pixel", hats={"crown": 1}, equipped="crown", fish=42,
                           focus={"ends_at": 1234.5, "total_min": 25})
            st.data["settings"]["meows"] = False
            st.save()
            back = Store(path).data
        self.assertEqual((back["name"], back["equipped"], back["fish"]), ("Pixel", "crown", 42))
        self.assertEqual(back["focus"], {"ends_at": 1234.5, "total_min": 25})
        self.assertFalse(back["settings"]["meows"])

    def test_name_is_trimmed_and_limited(self):
        with tempfile.TemporaryDirectory() as tmp:
            st = Store(self.write(tmp, {"name": "  " + "x" * 50 + "  "}))
        self.assertEqual(st.data["name"], "x" * 20)


# ─────────────────────────────────────────────────────────── jeu


class RewardsAndFocusTest(GameTestCase):
    def test_short_sessions_give_no_reward(self):
        done, notes = [], []
        self.game.focus_finished.connect(done.append)
        self.game.notice.connect(lambda t, m: notes.append(m))
        for minutes in (1, MIN_REWARD_MIN - 1):
            self.game.start_focus(minutes)
            self.now += minutes * 60 + 1
            self.game.tick()
        self.assertEqual(done, [1, MIN_REWARD_MIN - 1])
        self.assertEqual(self.game.data["fish"], 0)
        self.assertFalse(self.game.data["gift_pending"])
        self.assertEqual(len(notes), 2)

    def test_gift_farming_with_one_minute_sessions_is_closed(self):
        for _ in range(20):
            self.game.start_focus(1)
            self.now += 61
            self.game.tick()
        self.assertFalse(self.game.data["gift_pending"])
        self.assertEqual(self.game.data["fish"], 0)

    def test_minimum_session_is_rewarded(self):
        self.game.start_focus(MIN_REWARD_MIN)
        self.work(MIN_REWARD_MIN)
        self.assertTrue(self.game.data["gift_pending"])
        self.assertEqual(self.game.data["fish"], 10 + MIN_REWARD_MIN)

    def test_session_spent_away_from_the_computer_gives_no_reward(self):
        done, notes = [], []
        self.game.focus_finished.connect(done.append)
        self.game.notice.connect(lambda t, m: notes.append(m))
        self.idle = 400                                          # personne devant l'écran pendant toute la session
        self.game.start_focus(25)
        self.work(25)
        self.assertIsNone(self.game.focus)
        self.assertEqual(done, [])                               # ni « bravo » ni cadeau
        self.assertFalse(self.game.data["gift_pending"])
        self.assertEqual(self.game.data["fish"], 0)
        self.assertEqual(len(notes), 1)

    def test_session_suspended_by_sleep_gives_no_reward(self):
        self.game.start_focus(25)
        self.now += 25 * 60 + 1                                  # le PC dort 25 min : l'horloge avance, pas le jeu
        self.game.tick()
        self.assertIsNone(self.game.focus)
        self.assertFalse(self.game.data["gift_pending"])
        self.assertEqual(self.game.data["fish"], 0)

    def test_half_presence_is_enough(self):
        self.game.start_focus(20)
        self.idle = 400
        self.work(10)                                            # absent la première moitié
        self.idle = 0
        self.work(10)
        self.assertTrue(self.game.data["gift_pending"])

    def test_presence_is_kept_across_an_app_restart(self):
        self.game.start_focus(20)
        self.work(12)
        again = self.new_game_on_same_save()
        again._restore_focus()
        self.assertGreaterEqual(again.focus["active"], 12 * 60 - 1)

    def test_old_save_without_presence_gets_the_benefit_of_the_doubt(self):
        self.game.start_focus(20)
        self.now += 5 * 60
        del self.game.data["focus"]["active"]
        self.game.save()
        again = self.new_game_on_same_save()
        again._restore_focus()
        self.assertAlmostEqual(again.focus["active"], 5 * 60, delta=1)


    def new_game_on_same_save(self):
        return Game(Store(self.store.path), clock=lambda: self.now)

    def test_session_survives_an_app_restart(self):
        self.game.start_focus(25)
        self.now += 5 * 60
        again = self.new_game_on_same_save()
        seen = []
        again.focus_changed.connect(seen.append)
        again._restore_focus()
        self.assertEqual(again.focus["total_min"], 25)
        self.assertEqual(seen[0]["total_min"], 25)
        self.assertAlmostEqual(again.focus["ends_at"] - self.now, 20 * 60, delta=1)

    def test_session_ended_during_absence_is_dropped_without_reward(self):
        self.game.start_focus(25)
        self.now += 26 * 60
        again = self.new_game_on_same_save()
        again._restore_focus()
        self.assertIsNone(again.focus)
        self.assertIsNone(again.data["focus"])
        self.assertEqual(again.data["fish"], 0)
        self.assertFalse(again.data["gift_pending"])

    def test_stopping_a_session_forgets_it(self):
        self.game.start_focus(25)
        self.game.stop_focus(False)
        self.assertIsNone(Store(self.store.path).data["focus"])

    def test_finished_session_is_not_restored(self):
        self.game.start_focus(25)
        self.now += 25 * 60 + 1
        self.game.tick()
        again = self.new_game_on_same_save()
        again._restore_focus()
        self.assertIsNone(again.focus)

    def test_meows_setting(self):
        self.assertTrue(self.game.settings["meows"])
        self.assertTrue(self.game.set_setting("meows", False))
        self.assertFalse(Store(self.store.path).data["settings"]["meows"])


class TickTimingTest(GameTestCase):
    def test_tick_counts_the_elapsed_time(self):
        self.game.tick(3.0)
        self.assertEqual(self.store.day()["active"], 3)

    def test_fractions_of_a_second_are_carried_over(self):
        for _ in range(5):
            self.game.tick(0.6)                                   # 3,0 s au total
        self.assertEqual(self.store.day()["active"], 3)

    def test_timer_caps_a_long_stall(self):
        t = [100.0]
        game = Game(self.store, clock=lambda: self.now, mono=lambda: t[0])
        game._on_timer()                                          # premier passage : une seconde
        t[0] += 3600                                              # l'ordinateur a dormi une heure
        game._on_timer()
        self.assertEqual(self.store.day()["active"], 1 + int(MAX_TICK_S))

    def test_timer_never_goes_backwards(self):
        t = [100.0]
        game = Game(self.store, clock=lambda: self.now, mono=lambda: t[0])
        game._on_timer()
        t[0] -= 50
        game._on_timer()
        self.assertEqual(self.store.day()["active"], 1)


class FullscreenPerMonitorTest(GameTestCase):
    def fg_covering(self, rect):
        return winapi.Foreground(9, 1, "jeu.exe", "Jeu", rect, "UnityWndClass")

    def test_fullscreen_reports_which_monitor(self):
        self.game.set_monitors([(0, 0, 1920, 1080), (1920, 0, 3840, 1080)])
        events = []
        self.game.fullscreen_changed.connect(events.append)
        self.fg = self.fg_covering((1920, 0, 3840, 1080))
        self.game.tick()
        self.assertEqual(self.game.fullscreen_monitor, 1)
        self.assertTrue(self.game.fullscreen)
        self.fg = self.fg_covering((0, 0, 1920, 1080))          # la même appli passe sur l'autre écran
        self.game.tick()
        self.assertEqual(self.game.fullscreen_monitor, 0)
        self.fg = None
        self.game.tick()
        self.assertIsNone(self.game.fullscreen_monitor)
        self.assertEqual(events, [True, True, False])

    def test_a_window_on_one_monitor_is_not_fullscreen_on_the_other(self):
        self.assertIsNone(winapi.fullscreen_monitor(self.fg_covering((0, 0, 1920, 1000)),
                                                    [(0, 0, 1920, 1080), (1920, 0, 3840, 1080)]))


# ─────────────────────────────────────────────────────────── chat sur plusieurs écrans


class PetCase(GameTestCase):
    def make_pet(self, screens, seed=1):
        self.screens = list(screens)
        self.bubble, self.gift = Bubble(), GiftBox(4)
        self.fxl = FxLayer(QRect(0, 0, 100, 100))
        pet = Pet(self.game, self.bubble, self.gift, self.fxl, rng=random.Random(seed), screens=lambda: self.screens)
        pet.loop.stop()
        pet.anim.stop()
        self.addCleanup(lambda: [w.close() for w in (pet, self.bubble, self.gift, self.fxl)])
        self.pet = pet
        return pet

    def run_steps(self, n=120, dt=1 / 60):
        for _ in range(n):
            self.pet.step(dt)

    def run_until(self, cond, n=900, dt=1 / 60):
        for _ in range(n):
            if cond():
                return
            self.pet.step(dt)
        self.fail("condition jamais atteinte")

    def place(self, cx, fy, state="idle", floor_idx=0):
        p = self.pet
        p.fx, p.fy, p.stand, p.vy = cx - p.CW / 2, fy, None, 0.0
        p.floor_idx, p.state, p.timer = floor_idx, state, 999.0


class MultiScreenTest(PetCase):
    SIDE_BY_SIDE = (screen(0, 0, 1000, 800), screen(1000, 0, 2000, 800))

    def test_monitors_are_given_to_the_game_in_physical_pixels(self):
        self.make_pet([screen(0, 0, 1000, 800), screen(1000, 0, 2000, 800, dpr=2.0)])
        self.assertEqual(self.game.monitor_rects, [(0, 0, 1000, 800), (1000, 0, 3000, 1600)])

    def test_walks_from_one_screen_to_the_next(self):
        pet = self.make_pet(self.SIDE_BY_SIDE)
        self.place(900, 800)
        pet._walk_to(1500)
        self.run_until(lambda: pet.cx >= 1400)
        self.assertIsNone(pet.stand)
        self.assertEqual(pet.floor_idx, 1)
        self.assertEqual(pet.fy, 800)

    def test_walks_all_the_way_back(self):
        pet = self.make_pet(self.SIDE_BY_SIDE)
        self.place(1500, 800, floor_idx=1)
        pet._walk_to(200)
        self.run_until(lambda: pet.state != "walk")
        self.assertAlmostEqual(pet.cx, 200, delta=2)
        self.assertEqual(pet.floor_idx, 0)

    def test_climbs_the_taskbar_step_between_screens(self):
        # l'écran principal a une barre des tâches (sol à 760), le second non (sol à 800)
        pet = self.make_pet([screen(0, 0, 1000, 800, work_bottom=760), screen(1000, 0, 2000, 800)])
        self.place(900, 760)
        pet._walk_to(1500)
        self.run_until(lambda: pet.state != "walk")
        self.assertEqual(pet.floor_idx, 1)
        self.run_steps(30)
        self.assertEqual(pet.fy, 800)
        pet._walk_to(200)
        self.run_until(lambda: pet.state != "walk")
        self.run_steps(30)
        self.assertEqual(pet.fy, 760)

    def test_never_walks_off_the_desktop(self):
        pet = self.make_pet(self.SIDE_BY_SIDE)
        self.place(1900, 800, floor_idx=1)
        pet._walk_to(5000)
        self.run_steps(300)
        self.assertLessEqual(pet.cx, 2000)
        pet._walk_to(-5000)
        self.run_steps(1500)
        self.assertGreaterEqual(pet.cx, 0)

    def test_cannot_walk_across_a_cliff_but_can_jump(self):
        pet = self.make_pet([screen(0, 0, 1000, 800), screen(1000, 0, 2000, 400)])
        self.place(900, 800)
        pet._walk_to(1500)
        self.run_steps(400)
        self.assertLessEqual(pet.cx, 1000)                        # bloqué au bord de son écran
        self.assertEqual(pet.floor_idx, 0)
        self.place(960, 800)
        self.assertTrue(pet._jump_somewhere(reach_up=600))
        self.run_until(lambda: pet.state != "jump")
        self.assertEqual((pet.floor_idx, pet.fy), (1, 400))

    def test_falls_onto_the_lower_screen(self):
        pet = self.make_pet([screen(0, 0, 1000, 800), screen(1000, 0, 2000, 400)])
        self.place(1500, 50, state="fall")
        self.run_until(lambda: pet.state != "fall")
        self.assertEqual((pet.floor_idx, pet.fy), (1, 400))

    def test_dropped_in_the_void_between_screens_lands_on_the_nearest_floor(self):
        pet = self.make_pet([screen(0, 0, 1000, 800), screen(1100, 0, 2000, 800)])
        self.place(1050, 100, state="fall")
        self.run_until(lambda: pet.state != "fall")
        self.assertTrue(0 <= pet.cx <= 1000 or 1100 <= pet.cx <= 2000, pet.cx)
        self.assertEqual(pet.fy, 800)

    def test_perches_on_a_window_of_a_high_dpi_second_screen(self):
        pet = self.make_pet([screen(0, 0, 1000, 800), screen(1000, 0, 2000, 800, dpr=2.0)])
        # fenêtre en pixels physiques sur l'écran B : à l'écran, son bord haut est à y = 300, de x = 1200 à 1700
        self.desk.put(77, (1400, 600, 2400, 1400))
        self.place(1450, 100, state="fall")
        self.run_until(lambda: pet.state != "fall")
        self.assertEqual(pet.stand, 77)
        self.assertAlmostEqual(pet.fy, 300, delta=0.5)

    def test_does_not_perch_on_a_window_of_another_screen_at_the_wrong_place(self):
        pet = self.make_pet(self.SIDE_BY_SIDE)
        self.desk.put(5, (1200, 400, 1900, 700))
        self.place(300, 100, state="fall")                          # tombe sur l'écran A, loin de la fenêtre
        self.run_until(lambda: pet.state != "fall")
        self.assertIsNone(pet.stand)
        self.assertEqual((pet.floor_idx, pet.fy), (0, 800))

    def test_window_half_off_the_desktop_keeps_the_cat_on_screen(self):
        pet = self.make_pet([screen(0, 0, 1000, 800)])
        self.desk.put(5, (-400, 400, 600, 700))
        self.place(100, 100, state="fall")
        self.run_until(lambda: pet.state != "fall")
        self.assertEqual(pet.stand, 5)
        pet._walk_to(-300)
        self.run_steps(400)
        self.assertGreaterEqual(pet.cx, 0)

    def test_unplugging_a_screen_brings_the_cat_back(self):
        pet = self.make_pet(self.SIDE_BY_SIDE)
        self.place(1500, 800, floor_idx=1)
        self.screens = [self.SIDE_BY_SIDE[0]]
        self.run_steps(40)
        self.assertEqual(len(pet.floors), 1)
        self.assertLessEqual(pet.cx, 1000)
        self.assertEqual((pet.floor_idx, pet.fy), (0, 800))
        self.assertEqual(self.game.monitor_rects, [(0, 0, 1000, 800)])

    def test_plugging_a_screen_makes_it_walkable(self):
        pet = self.make_pet([self.SIDE_BY_SIDE[0]])
        self.screens = list(self.SIDE_BY_SIDE)
        self.run_steps(30)
        self.assertEqual(len(pet.floors), 2)
        self.place(900, 800)
        pet._walk_to(1500)
        self.run_until(lambda: pet.cx >= 1400)

    def test_taskbar_change_moves_the_floor(self):
        pet = self.make_pet([screen(0, 0, 1000, 800)])
        self.place(500, 800, state="nap")
        self.screens = [screen(0, 0, 1000, 800, work_bottom=750)]   # barre des tâches qui apparaît
        self.run_steps(60)
        self.assertEqual(pet.fy, 750)

    def test_fullscreen_only_hides_the_cat_on_that_screen(self):
        pet = self.make_pet(self.SIDE_BY_SIDE)
        self.place(300, 800)                                          # le chat est sur A
        cover = lambda r: winapi.Foreground(9, 1, "jeu.exe", "Jeu", r, "UnityWndClass")
        self.fg = cover((1000, 0, 2000, 800))                         # appli plein écran sur B
        self.game.tick()
        self.assertFalse(pet.hidden)
        self.fg = cover((0, 0, 1000, 800))                            # elle passe sur A
        self.game.tick()
        self.assertTrue(pet.hidden)
        self.assertFalse(pet.isVisible())
        self.fg = cover((1000, 0, 2000, 800))                         # puis retourne sur B
        self.game.tick()
        self.assertFalse(pet.hidden)
        self.assertTrue(pet.isVisible())

    def test_walking_onto_a_fullscreen_screen_hides_the_cat(self):
        pet = self.make_pet(self.SIDE_BY_SIDE)
        self.place(900, 800)
        self.fg = winapi.Foreground(9, 1, "jeu.exe", "Jeu", (1000, 0, 2000, 800), "UnityWndClass")
        self.game.tick()
        self.assertFalse(pet.hidden)
        pet._walk_to(1500)
        self.run_until(lambda: pet.hidden)
        self.assertGreaterEqual(pet.cx, 1000)

    def test_bubble_stays_on_the_screen_of_the_cat(self):
        pet = self.make_pet(self.SIDE_BY_SIDE)
        self.place(1990, 800, floor_idx=1)
        pet.say("Un texte assez long pour dépasser", 3000)
        self.run_steps(2)
        self.assertLessEqual(self.bubble.x() + self.bubble.width(), 2000)

    def test_bubble_tail_points_at_the_cat_even_when_the_bubble_is_shifted(self):
        pet = self.make_pet(self.SIDE_BY_SIDE)
        self.place(1920, 800, floor_idx=1)                       # près du bord droit : la bulle est décalée
        pet.say("Un texte assez long pour dépasser", 3000)
        self.run_steps(2)
        self.assertLessEqual(self.bubble.x() + self.bubble.width(), 2000)
        head_x = pet.fx + pet.CW * (0.62 if pet.dir > 0 else 0.38)
        self.assertGreater(self.bubble.tail_x, self.bubble.width() / 2)               # décalée vers le chat
        self.assertAlmostEqual(self.bubble.x() + self.bubble.tail_x, head_x,
                               delta=self.bubble.RADIUS + self.bubble.TAIL)           # sauf si les coins l'en empêchent

    def test_bubble_tail_is_centered_when_there_is_room(self):
        pet = self.make_pet(self.SIDE_BY_SIDE)
        self.place(500, 800)
        pet.say("Miaou", 3000)
        self.run_steps(2)
        self.assertAlmostEqual(self.bubble.tail_x, self.bubble.width() / 2, delta=self.bubble.width() * 0.2)

    def test_window_moved_during_a_jump_does_not_teleport_the_cat(self):
        """Régression : il atterrissait sur l'ancienne position de la fenêtre, puis la « suivait » d'un seul bond."""
        pet = self.make_pet(self.SIDE_BY_SIDE)
        self.desk.put(111, (100, 400, 700, 560))
        self.place(300, pet.floor_y)
        self.run_steps(3)
        self.assertTrue(pet._jump_somewhere(prefer_hwnd=111, reach_up=600))
        self.run_steps(3)
        self.desk.put(111, (1300, 400, 1900, 560))                # la fenêtre part sur l'autre écran, en plein saut
        xs = [pet.cx]
        for _ in range(240):
            pet.step(1 / 60)
            xs.append(pet.cx)
            if pet.state in ("idle", "walk") and pet.stand is None:
                break
        biggest_step = max(abs(b - a) for a, b in zip(xs, xs[1:]))
        self.assertLess(biggest_step, 40)                         # un saut fait ~10 px par pas ; une téléportation, des centaines
        self.assertIsNone(pet.stand)                              # il n'est pas resté « sur » une fenêtre absente
        self.assertEqual(pet.fy, pet.floor_y)

    def test_a_window_that_stayed_put_is_still_a_perch(self):
        pet = self.make_pet(self.SIDE_BY_SIDE)
        self.desk.put(111, (100, 400, 700, 560))
        self.place(300, pet.floor_y)
        self.run_steps(3)
        self.assertTrue(pet._jump_somewhere(prefer_hwnd=111, reach_up=600))
        self.run_until(lambda: pet.state != "jump")
        self.assertEqual(pet.stand, 111)
        self.assertAlmostEqual(pet.fy, 400, delta=0.5)

    def test_long_life_on_three_screens_never_leaves_the_desktop(self):
        # Le chat va parfois « voir la souris » : sa position fait partie du hasard, on en essaie plusieurs
        # (462 reproduisait un bug réel : atterrissage sur une fenêtre déplacée pendant le saut).
        for cursor_x in (0, 462, 1500, 2900):
            with self.subTest(cursor_x=cursor_x), mock.patch.object(pet_module, "QCursor", FixedCursor(cursor_x)):
                self.long_life()

    def long_life(self):
        self.desk.wins.clear()
        pet = self.make_pet([screen(0, 0, 1000, 800), screen(1000, 0, 2000, 800, work_bottom=760, dpr=1.5),
                             screen(2000, 200, 3000, 900)], seed=11)
        rng = random.Random(5)
        for i in range(30 * 150):
            if i % 60 == 0:
                hwnd = rng.randint(1, 5)
                if rng.random() < 0.3 and hwnd in self.desk.wins:
                    del self.desk.wins[hwnd]
                else:
                    x, y = rng.randint(0, 3200), rng.randint(300, 1200)
                    self.desk.put(hwnd, (x, y, x + rng.randint(300, 700), y + 250))
            pet.step(1 / 30)
            self.assertTrue(-50 <= pet.cx <= 3050 and 0 <= pet.fy <= 1000, (i, pet.cx, pet.fy, pet.state))


# ─────────────────────────────────────────────────────────── miaou


class MeowTest(PetCase):
    def setUp(self):
        super().setUp()
        self.pet = self.make_pet([screen(0, 0, 1000, 800)])
        self.place(500, 800)

    def test_a_meow_appears_in_a_bubble(self):
        self.pet.next_meow = 0
        self.run_steps(2)
        self.assertIn(self.bubble.text(), ALL_MEOWS)
        self.assertTrue(self.bubble.isVisible())

    def test_it_disappears_after_a_moment_and_the_next_one_is_later(self):
        self.pet.next_meow = 0
        self.run_steps(2)
        self.assertGreaterEqual(self.pet.next_meow - self.pet.t, phrases.MEOW_MIN_MS - 100)
        self.pet.state, self.pet.timer = "idle", 999
        self.run_steps(int(2.5 * 60))
        self.assertFalse(self.bubble.isVisible())

    def test_can_be_turned_off(self):
        self.game.set_setting("meows", False)
        self.pet.next_meow = 0
        self.run_steps(120)
        self.assertFalse(self.bubble.isVisible())

    def test_no_meow_while_sleeping_or_napping(self):
        for state in ("nap", "sleep"):
            self.pet.state = state
            self.pet.sys_sleep = state == "sleep"
            self.pet.next_meow = 0
            self.pet.step(1 / 60)
            self.assertFalse(self.bubble.isVisible(), state)
            self.assertGreater(self.pet.next_meow, self.pet.t)         # il réessaiera plus tard

    def test_no_meow_on_top_of_another_message(self):
        self.pet.say("Message important", 5000)
        self.pet.next_meow = 0
        self.pet.state, self.pet.timer = "idle", 999
        self.run_steps(3)
        self.assertEqual(self.bubble.text(), "Message important")

    def test_no_meow_while_a_gift_waits(self):
        self.game.data["gift_pending"] = True
        self.run_steps(5)
        self.assertTrue(self.pet.gift_visible)
        before = self.bubble.text()
        self.pet.next_meow = 0
        self.run_steps(3)
        self.assertEqual(self.bubble.text(), before)

    def test_during_focus_the_timer_comes_back_after_the_meow(self):
        self.game.start_focus(25)
        self.run_until(lambda: self.pet.state == "work")
        self.pet._temp = False
        self.pet.next_meow = 0
        self.run_steps(2)
        self.assertIn(self.bubble.text(), phrases.MEOWS["work"])
        self.run_steps(int(3 * 60))
        self.assertIn("⏱", self.bubble.text())

    def test_petting_can_make_him_purr(self):
        class Always:
            def random(self):
                return 0.1

            def uniform(self, a, b):
                return a
        self.pet.rng = Always()
        self.pet._pet()
        self.assertIn(self.bubble.text(), phrases.MEOWS["petted"])

    def test_petting_stays_silent_when_meows_are_off(self):
        self.game.set_setting("meows", False)
        self.pet.rng = mock.Mock(random=lambda: 0.1)
        self.pet._pet()
        self.assertFalse(self.bubble.isVisible())

    def test_frequency_over_half_an_hour(self):
        said = []
        original = self.pet.say
        self.pet.say = lambda *a, **k: (said.append(a[0]), original(*a, **k))[1]
        for _ in range(30 * 60 * 30):                                  # 30 min simulées à 30 Hz
            self.pet.step(1 / 30)
        meows = [s for s in said if s in ALL_MEOWS]
        self.assertTrue(8 <= len(meows) <= 40, len(meows))


# ─────────────────────────────────────────────────────────── souris et panneau


def mouse(kind, button=Qt.MouseButton.LeftButton):
    return QMouseEvent(kind, QPointF(5, 5), QPointF(5, 5), button, Qt.MouseButton.NoButton,
                       Qt.KeyboardModifier.NoModifier)


class ClickTest(PetCase):
    def setUp(self):
        super().setUp()
        self.make_pet([screen(0, 0, 1000, 800)])

    def release_click(self):
        self.pet._press = {"g": QPoint(5, 5), "moved": False, "off": (5, 5)}
        self.pet.mouseReleaseEvent(mouse(QEvent.Type.MouseButtonRelease))

    def test_a_single_click_pets_after_the_double_click_delay(self):
        self.release_click()
        self.assertTrue(self.pet._pet_timer.isActive())

    def test_a_double_click_opens_the_panel_without_petting(self):
        opened = []
        self.pet.open_panel.connect(lambda: opened.append(1))
        self.release_click()
        self.pet.mouseDoubleClickEvent(mouse(QEvent.Type.MouseButtonDblClick))
        self.assertFalse(self.pet._pet_timer.isActive())
        self.assertEqual(opened, [1])

    def test_dragging_does_not_pet(self):
        self.pet._press = {"g": QPoint(5, 5), "moved": True, "off": (5, 5)}
        self.pet.mouseReleaseEvent(mouse(QEvent.Type.MouseButtonRelease))
        self.assertFalse(self.pet._pet_timer.isActive())
        self.assertEqual(self.pet.state, "fall")

    def test_dragging_keeps_the_cat_on_a_screen(self):
        pet = self.pet
        pet.mousePressEvent(mouse(QEvent.Type.MouseButtonPress))
        for x, y in ((400, 400), (-500, 3000), (6000, -50)):
            ev = QMouseEvent(QEvent.Type.MouseMove, QPointF(5, 5), QPointF(x, y), Qt.MouseButton.NoButton,
                             Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
            pet.mouseMoveEvent(ev)
            self.assertTrue(0 <= pet.cx <= 1000 and pet.FOOT <= pet.fy <= 800, (x, y, pet.cx, pet.fy))
        pet.mouseReleaseEvent(mouse(QEvent.Type.MouseButtonRelease))


class PanelTest(GameTestCase):
    def test_closing_hides_the_panel_but_not_when_the_session_ends(self):
        panel = Panel(self.game)
        self.addCleanup(panel.deleteLater)
        panel.show()
        ev = QCloseEvent()
        panel.closeEvent(ev)
        self.assertFalse(ev.isAccepted())
        self.assertFalse(panel.isVisible())
        with mock.patch.object(Panel, "_session_ending", staticmethod(lambda: True)):
            ev = QCloseEvent()
            panel.closeEvent(ev)
            self.assertTrue(ev.isAccepted())
        panel._quitting = True
        ev = QCloseEvent()
        panel.closeEvent(ev)
        self.assertTrue(ev.isAccepted())

    def test_meows_checkbox_is_wired_to_the_setting(self):
        panel = Panel(self.game)
        self.addCleanup(panel.deleteLater)
        self.assertTrue(panel.checks["meows"].isChecked())
        panel.checks["meows"].setChecked(False)
        self.assertFalse(self.game.settings["meows"])


class BubbleLookTest(unittest.TestCase):
    """La bulle doit dessiner son propre fond : sans lui, le texte sombre est illisible devant une fenêtre sombre."""

    def make(self, scale=4, html="Miaou !"):
        b = Bubble(scale)
        self.addCleanup(b.close)
        b.show_html(html)
        APP.processEvents()
        return b

    def test_background_is_painted_behind_the_text(self):
        b = self.make()
        img = b.grab().toImage()
        inside = img.pixelColor(b.PAD_X // 2 + b.BORDER + 2, (b.height() - b.TAIL) // 2)
        self.assertEqual(inside.alpha(), 255)                    # fond opaque, pas transparent
        self.assertGreater(inside.lightness(), 200)              # clair : le texte sombre se détache

    def test_text_stays_dark_in_a_dark_windows_theme(self):
        """En mode sombre, Windows fournit un texte blanc : il doit rester sombre sur le fond crème de la bulle."""
        old = APP.palette()
        dark = QPalette(old)
        for role in (QPalette.ColorRole.Text, QPalette.ColorRole.WindowText, QPalette.ColorRole.ButtonText):
            dark.setColor(role, QColor("#ffffff"))
        dark.setColor(QPalette.ColorRole.Window, QColor("#202020"))
        APP.setPalette(dark)
        self.addCleanup(APP.setPalette, old)
        b = self.make(4, "Miaou, un long texte bien visible")
        img = b.grab().toImage()
        darkest = min(img.pixelColor(x, y).lightness()
                      for x in range(b.BORDER + b.PAD_X, b.width() - b.PAD_X)
                      for y in range(b.BORDER + b.PAD_Y, b.height() - b.TAIL - b.PAD_Y))
        self.assertLess(darkest, 90)                             # il y a des pixels de texte foncés

    def test_tail_never_goes_into_the_rounded_corners(self):
        b = self.make()
        b.set_tail_x(-500)
        self.assertGreaterEqual(b.tail_x, b.BORDER + b.RADIUS + b.TAIL)
        b.set_tail_x(5000)
        self.assertLessEqual(b.tail_x, b.width() - b.BORDER - b.RADIUS - b.TAIL)

    def test_text_grows_with_the_cat(self):
        small, big = self.make(3), self.make(6)
        self.assertLess(small.font_px, big.font_px)
        self.assertGreaterEqual(self.make(4).font_px, 15)        # plus lisible que les anciens 13 px
        self.assertGreater(big.width(), small.width())

    def test_changing_the_scale_resizes_the_open_bubble(self):
        b = self.make(3)
        before = b.width()
        b.set_scale(6)
        self.assertGreater(b.width(), before)
        self.assertEqual(b.text(), "Miaou !")

    def test_long_text_wraps_instead_of_growing_forever(self):
        b = self.make(4, "mot " * 60)
        self.assertLessEqual(b.width(), 24 * b.font_px)
        self.assertGreater(b.height(), self.make(4).height())

    def test_click_closes_the_bubble(self):
        b = self.make()
        clicked = []
        b.clicked.connect(lambda: clicked.append(1))
        b.mousePressEvent(None)
        self.assertFalse(b.isVisible())
        self.assertEqual(clicked, [1])


if __name__ == "__main__":
    unittest.main()
