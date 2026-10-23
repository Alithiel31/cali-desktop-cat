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
from desktopcat.dog_sprite import DOG_FOOT_ROW, DOG_H, DOG_W
from desktopcat.pet import Pet
from desktopcat.widgets import Bubble, FxLayer, GiftBox
from test_logic import DEFAULT_SCREENS, FixedCursor, GameTestCase


class FakeRng:
    """Hasard réglable : `random()` renvoie toujours `value`, `uniform(a, b)` toujours `a`."""

    def __init__(self, value):
        self.value = value

    def random(self):
        return self.value

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
