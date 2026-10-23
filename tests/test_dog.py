"""Tests de Jazz, le chien qui rend visite à Cali (Qt offscreen, écrans et souris factices)."""
import os
import random
import sys
from unittest import mock

if sys.platform != "win32":
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PySide6.QtCore import QRect, Qt

from desktopcat import dog as dog_module
from desktopcat import pet as pet_module
from desktopcat import phrases
from desktopcat.dog_sprite import DOG_FOOT_ROW, DOG_H, DOG_W
from desktopcat.pet import Pet
from desktopcat.widgets import Bubble, FxLayer, GiftBox
from test_logic import DEFAULT_SCREENS, FixedCursor, GameTestCase


class FakeRng:
    """Hasard réglable : `random()` renvoie les valeurs données dans l'ordre (puis répète la dernière),
    `uniform(a, b)` renvoie toujours `a`."""

    def __init__(self, *values):
        self.values = list(values)

    def random(self):
        return self.values.pop(0) if len(self.values) > 1 else self.values[0]

    def uniform(self, a, b):
        return a


class DogTest(GameTestCase):
    def make_pet(self, dog_rng):
        self.bubble, self.gift = Bubble(), GiftBox(4)
        self.fxl = FxLayer(QRect(0, 0, 800, 800))
        cursor = mock.patch.object(pet_module, "QCursor", FixedCursor())
        cursor.start()
        self.addCleanup(cursor.stop)
        pet = Pet(self.game, self.bubble, self.gift, self.fxl, rng=random.Random(1),
                  screens=lambda: list(DEFAULT_SCREENS), dog_rng=dog_rng)
        pet.loop.stop()
        pet.anim.stop()
        pet.dog.voice = FakeRng(0.9)                # muet par défaut (0,9 > BARK_CHANCE) : les tests de voix le règlent
        self.addCleanup(lambda: [w.close() for w in (pet, pet.dog, self.bubble, self.gift, self.fxl)])
        return pet

    def run_dog(self, pet, seconds, dt=1 / 60):
        for _ in range(round(seconds / dt)):
            pet.dog.step(dt)

    def start_visit(self, pet):
        """Avance jusqu'à l'instant précis où Jazz apparaît (sans le laisser marcher)."""
        for _ in range(round((dog_module.FIRST_VISIT_S[1] + 1) * 60)):
            pet.dog.step(1 / 60)
            if pet.dog.active:
                return
        self.fail("Jazz n'est jamais venu")

    def test_jazz_visits_setting_is_on_by_default_and_boolean(self):
        self.assertTrue(self.game.settings["jazz_visits"])
        self.assertTrue(self.game.set_setting("jazz_visits", False))
        self.assertFalse(self.game.settings["jazz_visits"])

    def test_no_visit_before_the_first_delay_then_jazz_shows_up(self):
        pet = self.make_pet(FakeRng(0.9))
        self.run_dog(pet, dog_module.FIRST_VISIT_S[0] - 5)
        self.assertFalse(pet.dog.active)
        self.assertFalse(pet.dog.isVisible())
        self.run_dog(pet, 10)
        self.assertTrue(pet.dog.active)
        self.assertTrue(pet.dog.isVisible())

    def test_he_comes_in_from_an_edge_walks_across_and_leaves(self):
        pet = self.make_pet(FakeRng(0.0))                      # random() = 0 : vient de la gauche, avec une pause
        pet.state = "work"                                     # Cali est occupée : il ne vient pas la voir
        self.start_visit(pet)
        floor = pet.floors[0]
        width = DOG_W * pet.dog.S
        self.assertEqual(pet.dog.dir, 1)
        self.assertLess(pet.dog.fx + width, floor.cx0 + 5)     # il vient d'entrer : encore hors de l'écran
        seen_sitting = False
        for _ in range(60 * 60):
            pet.dog.step(1 / 60)
            seen_sitting = seen_sitting or pet.dog.state == "sit"
            if not pet.dog.active:
                break
        self.assertTrue(seen_sitting)
        self.assertFalse(pet.dog.active)
        self.assertFalse(pet.dog.isVisible())
        self.assertEqual(pet.dog.timer, dog_module.BETWEEN_VISITS_S[0])

    def test_he_can_also_come_from_the_right_and_skip_the_pause(self):
        pet = self.make_pet(FakeRng(0.9))
        self.start_visit(pet)
        self.assertEqual(pet.dog.dir, -1)
        self.assertGreaterEqual(pet.dog.fx, pet.floors[0].cx1 - 5)
        states = set()
        for _ in range(60 * 60):
            pet.dog.step(1 / 60)
            states.add(pet.dog.state)
            if not pet.dog.active:
                break
        self.assertNotIn("sit", states)
        self.assertFalse(pet.dog.active)

    def test_his_paws_stay_on_the_floor_of_cali(self):
        pet = self.make_pet(FakeRng(0.9))
        self.start_visit(pet)
        for _ in range(120):
            pet.dog.step(1 / 60)
        self.assertAlmostEqual(pet.dog.fy, pet.floor_y)
        self.assertEqual(pet.dog.y() + DOG_FOOT_ROW * pet.dog.S, round(pet.floor_y))
        self.assertEqual((pet.dog.width(), pet.dog.height()), (DOG_W * pet.dog.S, DOG_H * pet.dog.S))

    def test_he_never_draws_from_the_cat_random_sequence(self):
        pet = self.make_pet(None)
        pet.state = "work"                                     # occupée : pas de câlin, donc pas de petits cœurs
        before = pet.rng.getstate()
        self.run_dog(pet, 3000)
        self.assertEqual(pet.rng.getstate(), before)

    def test_no_visit_when_off_hidden_in_focus_or_cat_asleep(self):
        cases = {
            "réglage coupé": lambda pet: self.game.set_setting("jazz_visits", False),
            "chat caché": lambda pet: pet.set_user_hidden(True),
            "concentration": lambda pet: setattr(self.game, "focus", {"ends_at": self.now + 600, "total_min": 10}),
            "chat endormi": lambda pet: setattr(pet, "sys_sleep", True),
        }
        for name, setup in cases.items():
            with self.subTest(name):
                pet = self.make_pet(FakeRng(0.9))
                setup(pet)
                self.run_dog(pet, dog_module.FIRST_VISIT_S[0] + 1)
                self.assertFalse(pet.dog.active)
                self.assertFalse(pet.dog.isVisible())
                self.assertLessEqual(pet.dog.timer, dog_module.RETRY_S)

    def test_a_visit_is_interrupted_when_the_cat_is_hidden(self):
        pet = self.make_pet(FakeRng(0.9))
        self.start_visit(pet)
        pet.set_user_hidden(True)
        self.assertFalse(pet.dog.active)
        self.assertFalse(pet.dog.isVisible())

    def test_a_visit_is_interrupted_when_the_setting_is_turned_off(self):
        pet = self.make_pet(FakeRng(0.9))
        self.start_visit(pet)
        self.game.set_setting("jazz_visits", False)
        pet.dog.step(1 / 60)
        self.assertFalse(pet.dog.active)

    def test_he_cannot_be_clicked_and_the_cat_never_perches_on_him(self):
        pet = self.make_pet(FakeRng(0.9))
        self.start_visit(pet)
        self.assertTrue(pet.dog.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents))
        self.assertTrue(pet.dog.windowFlags() & Qt.WindowType.WindowTransparentForInput)
        self.assertIn(int(pet.dog.winId()), pet._own_hwnds())

    def test_the_test_button_brings_him_right_away_when_allowed(self):
        pet = self.make_pet(FakeRng(0.9))
        self.assertFalse(pet.dog.active)
        self.game.call_jazz()
        self.assertTrue(pet.dog.active)
        self.assertTrue(pet.dog.isVisible())

    def test_the_test_button_does_nothing_when_he_cannot_come(self):
        pet = self.make_pet(FakeRng(0.9))
        self.game.set_setting("jazz_visits", False)
        self.game.call_jazz()
        self.assertFalse(pet.dog.active)

    # ───────────────────────── visite à Cali
    def make_greeting_pet(self):
        pet = self.make_pet(FakeRng(0.0))          # random() = 0 : de la gauche, avec une pause, et il vient la voir
        pet.fx = 900.0                             # Cali au milieu du sol, libre
        return pet

    def run_until_greeting(self, pet):
        for _ in range(60 * 60):
            pet.dog.step(1 / 60)
            if pet.dog.state == "greet":
                return
        self.fail("Jazz n'est jamais arrivé près de Cali")

    def test_he_sits_next_to_cali_and_she_answers(self):
        pet = self.make_greeting_pet()
        self.start_visit(pet)
        self.assertTrue(pet.dog._approach)
        self.run_until_greeting(pet)
        jazz_cx = pet.dog.x() + pet.dog.width() / 2
        self.assertAlmostEqual(pet.cx - jazz_cx, dog_module.TOUCH_GAP * pet.dog.S, delta=1)
        self.assertEqual(pet.dir, -1)                          # elle se tourne vers lui (à sa gauche)
        self.assertEqual(pet.state, "idle")
        self.assertGreater(pet.happy_until, pet.t)
        self.assertTrue(pet._temp)                             # une bulle ("Jazz !", "Mrrr ♥"...)

    def test_he_stays_quiet_when_meows_are_off(self):
        self.game.set_setting("meows", False)
        pet = self.make_greeting_pet()
        self.start_visit(pet)
        self.run_until_greeting(pet)
        self.assertFalse(pet._temp)

    def test_cali_stays_put_as_long_as_he_is_there(self):
        pet = self.make_greeting_pet()
        self.start_visit(pet)
        self.run_until_greeting(pet)
        pet.timer = 0.0                                        # sans lui, elle déciderait de repartir tout de suite
        pet.dog.step(1 / 60)
        self.assertGreaterEqual(pet.timer, 1.0)
        self.assertEqual(pet.state, "idle")

    def test_he_leaves_the_way_he_came(self):
        pet = self.make_greeting_pet()
        self.start_visit(pet)
        self.run_until_greeting(pet)
        pet.dog.timer = 0.0                                    # fin du tête-à-tête
        pet.dog.step(1 / 60)
        self.assertEqual(pet.dog.state, "walk")
        self.assertEqual(pet.dog.dir, -1)                      # retour vers la gauche
        for _ in range(60 * 60):
            pet.dog.step(1 / 60)
            if not pet.dog.active:
                break
        self.assertFalse(pet.dog.active)
        self.assertFalse(pet.dog.isVisible())

    def test_no_greeting_when_cali_is_busy_or_not_on_the_floor(self):
        cases = {
            "au travail": lambda pet: setattr(pet, "state", "work"),
            "en plein saut": lambda pet: setattr(pet, "state", "jump"),
            "perchée sur une fenêtre": lambda pet: setattr(pet, "stand", 1234),
        }
        for name, setup in cases.items():
            with self.subTest(name):
                pet = self.make_greeting_pet()
                setup(pet)
                self.start_visit(pet)
                self.assertFalse(pet.dog._approach)

    def test_no_greeting_when_cali_is_too_close_to_the_edge(self):
        pet = self.make_greeting_pet()
        pet.fx = pet.floors[0].cx0 + 10
        self.start_visit(pet)
        self.assertFalse(pet.dog._approach)

    def test_no_greeting_when_the_dice_say_so(self):
        pet = self.make_pet(FakeRng(0.9))
        pet.fx = 900.0
        self.start_visit(pet)
        self.assertFalse(pet.dog._approach)

    def test_he_gives_up_when_cali_leaves_during_the_approach(self):
        pet = self.make_greeting_pet()
        self.start_visit(pet)
        pet.state = "jump"                                     # elle a sauté sur une autre surface
        pet.dog.step(1 / 60)
        self.assertFalse(pet.dog._approach)
        self.assertEqual(pet.dog.dir, 1)                       # il continue son chemin
        self.assertNotEqual(pet.dog.state, "greet")

    def test_he_leaves_when_cali_is_picked_up_during_the_greeting(self):
        pet = self.make_greeting_pet()
        self.start_visit(pet)
        self.run_until_greeting(pet)
        pet.state = "drag"
        pet.dog.step(1 / 60)
        self.assertEqual(pet.dog.state, "walk")
        self.assertEqual(pet.dog.dir, -1)

    # ───────────────────────── Cali le suit
    def run_both(self, pet, seconds, dt=1 / 60):
        for _ in range(round(seconds / dt)):
            pet.dog.step(dt)
            pet.step(dt)

    def jazz_cx(self, pet):
        return pet.dog.x() + pet.dog.width() / 2

    def leave_after_greeting(self, pet):
        self.start_visit(pet)
        self.run_until_greeting(pet)
        pet.dog.timer = 0.0                                    # fin du tête-à-tête
        pet.dog.step(1 / 60)

    def test_cali_trots_behind_jazz_when_he_leaves(self):
        pet = self.make_greeting_pet()
        self.leave_after_greeting(pet)
        self.assertGreater(pet.dog._escort, 0)
        start = pet.cx
        self.run_both(pet, 2.0)
        self.assertLess(pet.cx, start - 100)                   # elle l'a suivi vers la gauche
        behind = pet.cx - self.jazz_cx(pet)                    # et reste juste derrière lui, jamais devant
        self.assertGreater(behind, 0)
        self.assertLess(behind, dog_module.TOUCH_GAP * pet.dog.S + 60)
        self.assertIn(pet.state, ("walk", "idle"))

    def test_jazz_slows_down_to_her_pace_while_she_follows(self):
        pet = self.make_greeting_pet()
        self.leave_after_greeting(pet)
        before = pet.dog.fx
        pet.dog.step(1)
        self.assertAlmostEqual(before - pet.dog.fx, pet.speed * dog_module.ESCORT_SPEED, delta=1)

    def test_she_stops_following_after_a_while_and_he_leaves_at_his_pace(self):
        pet = self.make_greeting_pet()
        self.leave_after_greeting(pet)
        self.run_both(pet, dog_module.FOLLOW_S[0] + 1)
        self.assertLessEqual(pet.dog._escort, 0)
        before = pet.dog.fx
        pet.dog.step(1)
        self.assertAlmostEqual(before - pet.dog.fx, dog_module.DOG_SPEED * pet.dog.S / 4, delta=1)
        self.run_both(pet, 30)
        self.assertFalse(pet.dog.active)

    def test_she_does_not_follow_when_the_dice_say_no(self):
        self.game.set_setting("meows", False)                  # pas de tirage pour la bulle
        pet = self.make_pet(FakeRng(0.0, 0.0, 0.0, 0.9))       # côté, pause, visite : oui ; suivi : non
        pet.fx = 900.0
        self.leave_after_greeting(pet)
        self.assertEqual(pet.dog._escort, 0)
        start = pet.cx
        self.run_both(pet, 1.0)
        self.assertAlmostEqual(pet.cx, start, delta=1)

    def test_she_does_not_follow_when_the_greeting_was_cut_short(self):
        pet = self.make_greeting_pet()
        self.start_visit(pet)
        self.run_until_greeting(pet)
        pet.state = "drag"
        pet.dog.step(1 / 60)
        self.assertEqual(pet.dog._escort, 0)

    def test_the_escort_stops_when_cali_has_something_else_to_do(self):
        pet = self.make_greeting_pet()
        self.leave_after_greeting(pet)
        pet.state = "jump"
        pet.dog.step(1 / 60)
        self.assertEqual(pet.dog._escort, 0)
        self.assertEqual(pet.state, "jump")                    # il ne la remet pas en marche de force

    def test_the_escort_stops_at_the_end_of_the_floor_instead_of_flickering(self):
        pet = self.make_greeting_pet()
        pet.fx = 300.0                                         # près du bord gauche : Jazz va y repartir
        self.leave_after_greeting(pet)
        states = []
        for _ in range(60 * 12):
            pet.dog.step(1 / 60)
            pet.step(1 / 60)
            states.append(pet.state)
        changes = sum(1 for a, b in zip(states, states[1:], strict=False) if a != b)
        self.assertLess(changes, 12)                           # pas de bascule marche/arrêt à chaque image
        self.assertEqual(pet.dog._escort, 0)

    # ───────────────────────── sieste à deux
    def make_napping_pet(self, *randoms):
        pet = self.make_pet(FakeRng(*(randoms or (0.0,))))
        pet.fx = 900.0
        pet.state = "nap"
        pet.timer = 3.0                            # sa sieste allait bientôt finir
        return pet

    def run_until_lying(self, pet):
        for _ in range(60 * 60):
            pet.dog.step(1 / 60)
            if pet.dog.state == "lie":
                return
        self.fail("Jazz ne s'est jamais couché")

    def test_he_lies_down_against_a_napping_cali_without_waking_her(self):
        pet = self.make_napping_pet()
        self.start_visit(pet)
        self.assertTrue(pet.dog._approach)
        self.run_until_lying(pet)
        self.assertEqual(pet.state, "nap")                     # elle dort toujours
        gap = pet.cx - self.jazz_cx(pet)
        self.assertAlmostEqual(gap, dog_module.LIE_GAP * pet.dog.S, delta=1)
        self.assertEqual(pet.dog.dir, 1)                       # la tête tournée vers elle
        self.assertEqual(pet.dir, -1)                          # et elle vers lui
        self.assertGreaterEqual(pet.timer, dog_module.JOIN_S[0])   # sa sieste dure au moins un moment

    def test_both_keep_sleeping_while_time_passes(self):
        pet = self.make_napping_pet()
        self.start_visit(pet)
        self.run_until_lying(pet)
        self.run_both(pet, 5.0)
        self.assertEqual(pet.state, "nap")
        self.assertEqual(pet.dog.state, "lie")

    def test_he_leaves_when_she_wakes_up_and_she_follows(self):
        pet = self.make_napping_pet()
        self.start_visit(pet)
        self.run_until_lying(pet)
        for _ in range(60 * 40):
            pet.dog.step(1 / 60)
            pet.step(1 / 60)
            if pet.state != "nap":
                break
        self.assertNotEqual(pet.state, "nap")
        pet.dog.step(1 / 60)
        self.assertEqual(pet.dog.state, "walk")
        self.assertEqual(pet.dog.dir, -1)                      # il repart par où il est venu
        self.assertGreater(pet.dog._escort, 0)                 # réveillée, elle le suit

    def test_he_leaves_if_she_is_woken_by_a_caress(self):
        pet = self.make_napping_pet()
        self.start_visit(pet)
        self.run_until_lying(pet)
        pet.state = "idle"
        pet.dog.step(1 / 60)
        self.assertEqual(pet.dog.state, "walk")

    def test_he_leaves_without_an_escort_when_she_is_carried_away(self):
        pet = self.make_napping_pet()
        self.start_visit(pet)
        self.run_until_lying(pet)
        pet.state = "drag"
        pet.dog.step(1 / 60)
        self.assertEqual(pet.dog.state, "walk")
        self.assertEqual(pet.dog._escort, 0)

    def test_he_never_sleeps_longer_than_the_maximum(self):
        pet = self.make_napping_pet()
        self.start_visit(pet)
        self.run_until_lying(pet)
        pet.dog.timer = 0.0
        pet.dog.step(1 / 60)
        self.assertEqual(pet.dog.state, "walk")
        self.assertEqual(pet.dog._escort, 0)                   # elle dort encore : personne à escorter

    def test_a_napping_cali_gets_a_better_chance_of_company(self):
        napping = self.make_napping_pet(0.0, 0.0, 0.7)         # 0,7 : sous 0,8 (sieste) mais pas sous 0,6 (câlin)
        self.start_visit(napping)
        self.assertTrue(napping.dog._approach)
        awake = self.make_pet(FakeRng(0.0, 0.0, 0.7))
        awake.fx = 900.0
        self.start_visit(awake)
        self.assertFalse(awake.dog._approach)

    def test_he_lies_down_if_she_falls_asleep_on_his_way(self):
        pet = self.make_greeting_pet()                         # Cali éveillée : il vient la saluer
        self.start_visit(pet)
        pet.state = "nap"
        self.run_until_lying(pet)
        self.assertEqual(pet.state, "nap")

    def test_he_greets_instead_if_she_wakes_on_his_way(self):
        pet = self.make_napping_pet()
        self.start_visit(pet)
        pet.state = "idle"
        for _ in range(60 * 60):
            pet.dog.step(1 / 60)
            if pet.dog.state in ("greet", "lie"):
                break
        self.assertEqual(pet.dog.state, "greet")

    def test_no_nap_visit_when_she_sleeps_because_you_are_away(self):
        pet = self.make_napping_pet()
        pet.sys_sleep = True
        pet.state = "sleep"
        self.run_dog(pet, dog_module.FIRST_VISIT_S[0] + 1)
        self.assertFalse(pet.dog.active)

    # ───────────────────────── sa voix : aboiements et cri de Toller
    ALL_BARKS = {b for pool in phrases.BARKS.values() for b in pool}

    def run_until_bubble(self, pet, n=60 * 60):
        for _ in range(n):
            pet.dog.step(1 / 60)
            if pet.dog.bubble.isVisible():
                return
            if not pet.dog.active:
                break
        self.fail("Jazz n'a rien dit")

    def test_the_barks_are_dog_noises_with_the_toller_scream(self):
        self.assertEqual(set(phrases.BARKS), {"pass", "scream", "greet", "lie"})
        for pool in phrases.BARKS.values():
            self.assertTrue(pool)
        for line in phrases.BARKS["scream"]:
            self.assertTrue(line.startswith("Aou"), line)
        rng = random.Random(3)
        for kind in (*phrases.BARKS, "inconnu"):
            self.assertIn(phrases.pick_bark(rng, kind), self.ALL_BARKS)

    def test_he_calls_cali_with_the_toller_scream_when_he_spots_her(self):
        pet = self.make_greeting_pet()
        self.start_visit(pet)
        self.assertTrue(pet.dog._approach)
        self.run_until_bubble(pet)
        self.assertEqual(pet.dog.state, "walk")
        self.assertIn(pet.dog.bubble.text(), phrases.BARKS["scream"])

    def test_he_falls_silent_on_arrival_so_cali_can_answer(self):
        pet = self.make_greeting_pet()
        self.start_visit(pet)
        self.run_until_greeting(pet)
        self.assertFalse(pet.dog.bubble.isVisible())
        self.assertTrue(pet._temp)                             # la bulle de Cali

    def test_he_barks_now_and_then_while_crossing(self):
        pet = self.make_pet(FakeRng(0.9))                      # il traverse sans pause ni visite à Cali
        pet.dog.voice = FakeRng(0.5)                           # aboie (0,5 < 0,6), mais pas de cri (0,5 > 0,2)
        self.start_visit(pet)
        self.run_until_bubble(pet, n=60 * 5)
        self.assertIn(pet.dog.bubble.text(), phrases.BARKS["pass"])

    def test_his_bubble_floats_above_his_head_and_stays_on_screen(self):
        pet = self.make_pet(FakeRng(0.9))
        pet.dog.voice = FakeRng(0.5)
        self.start_visit(pet)
        self.run_until_bubble(pet, n=60 * 5)
        bubble, left, top, right, _bottom = pet.dog.bubble, *pet.work
        self.assertLessEqual(bubble.y() + bubble.height(), pet.dog.y())
        self.assertGreaterEqual(bubble.x(), left)
        self.assertLessEqual(bubble.x() + bubble.width(), right)
        self.assertGreaterEqual(bubble.y(), top)

    def test_his_bubble_disappears_by_itself_and_with_the_visit(self):
        pet = self.make_pet(FakeRng(0.9))
        pet.dog.voice = FakeRng(0.5)
        self.start_visit(pet)
        self.run_until_bubble(pet, n=60 * 5)
        self.run_dog(pet, dog_module.BARK_MS / 1000 + 0.2)
        self.assertFalse(pet.dog.bubble.isVisible())
        pet.dog.voice = FakeRng(0.5)
        pet.dog._bark_in = 0.0
        pet.dog.step(1 / 60)
        self.assertTrue(pet.dog.bubble.isVisible())
        pet.dog.cancel()
        self.assertFalse(pet.dog.bubble.isVisible())

    def test_his_bubble_window_is_only_created_when_he_first_speaks(self):
        pet = self.make_pet(FakeRng(0.9))
        self.assertIsNone(pet.dog._bubble)
        self.assertEqual(pet.dog.windows(), ())
        pet.dog._say("pass")
        self.assertIsNotNone(pet.dog._bubble)
        self.assertEqual(pet.dog.windows(), (pet.dog.bubble,))

    def test_his_bubble_cannot_be_clicked(self):
        pet = self.make_pet(FakeRng(0.9))
        self.assertTrue(pet.dog.bubble.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents))
        self.assertTrue(pet.dog.bubble.windowFlags() & Qt.WindowType.WindowTransparentForInput)

    def test_he_never_barks_when_the_bubbles_are_off(self):
        self.game.set_setting("meows", False)
        pet = self.make_greeting_pet()
        pet.dog.voice = FakeRng(0.0)                           # il aboierait à chaque occasion
        self.start_visit(pet)
        for _ in range(60 * 60):
            pet.dog.step(1 / 60)
            self.assertFalse(pet.dog.bubble.isVisible())
            if not pet.dog.active:
                break

    def test_he_says_a_sigh_when_he_lies_down_against_a_napping_cali(self):
        pet = self.make_napping_pet()
        self.start_visit(pet)
        self.run_until_lying(pet)
        self.assertIn(pet.dog.bubble.text(), phrases.BARKS["lie"])

    def test_his_voice_never_touches_his_movement_random_sequence(self):
        rng = FakeRng(0.1, 0.2, 0.3)
        pet = self.make_pet(rng)
        before = list(rng.values)
        pet.dog._say("pass")
        pet.dog._say("scream")
        self.assertEqual(rng.values, before)                  # ses phrases n'ont pas consommé son hasard
