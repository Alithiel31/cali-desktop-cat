"""Tests de la géométrie multi-écrans et des phrases (fonctions pures : aucune fenêtre n'est ouverte)."""
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from desktopcat import phrases
from desktopcat.screens import (ScreenInfo, bounds, build_floors, clamp_point, clip_to_bounds, floor_here,
                                native_rects, nearest_floor, nearest_rect_index, screen_at_native, snap_to_floor,
                                to_logical)

# Deux écrans côte à côte : A (1920x1080, 100 %) puis B (4K à 200 % = 1920x1080 logiques).
A = ScreenInfo((0, 0, 1920, 1080), (0, 0, 1920, 1040), 1.0)
B = ScreenInfo((1920, 0, 3840, 1080), (1920, 0, 3840, 1080), 2.0)


class ScreenInfoTest(unittest.TestCase):
    def test_native_rect_uses_the_screen_scale(self):
        self.assertEqual(A.native, (0, 0, 1920, 1080))
        self.assertEqual(B.native, (1920, 0, 1920 + 3840, 2160))
        self.assertEqual(native_rects([A, B]), [(0, 0, 1920, 1080), (1920, 0, 5760, 2160)])

    def test_screen_at_native_point(self):
        self.assertEqual(screen_at_native([A, B], 100, 100), 0)
        self.assertEqual(screen_at_native([A, B], 2500, 1500), 1)
        self.assertEqual(screen_at_native([A, B], 1920, 500), 1)          # le bord droit de A appartient à B
        self.assertEqual(screen_at_native([A, B], 9000, 9000), 1)         # hors bureau : l'écran le plus proche
        self.assertEqual(screen_at_native([A, B], -50, 500), 0)

    def test_window_rect_to_logical(self):
        self.assertEqual(to_logical((100, 200, 900, 700), [A, B]), (100, 200, 900, 700))
        # sur B (200 %) : on repart de l'origine de B et on divise par 2
        self.assertEqual(to_logical((2120, 200, 3000, 800), [A, B]), (2020.0, 100.0, 2460.0, 400.0))

    def test_single_screen_is_identity(self):
        self.assertEqual(to_logical((10, 20, 30, 40), [A]), (10, 20, 30, 40))


class FloorsTest(unittest.TestCase):
    def test_touching_screens_with_same_bottom_form_one_chain(self):
        f = build_floors([(0, 0, 1000, 800), (1000, 0, 2000, 800)])
        self.assertEqual(len(f), 2)
        self.assertEqual(f[0].chain, f[1].chain)
        self.assertEqual((f[0].cx0, f[0].cx1), (0, 2000))

    def test_a_taskbar_step_is_walkable_but_a_cliff_is_not(self):
        step = build_floors([(0, 0, 1000, 760), (1000, 0, 2000, 800)])
        self.assertEqual(step[0].chain, step[1].chain)
        cliff = build_floors([(0, 0, 1000, 800), (1000, 0, 2000, 400)])
        self.assertNotEqual(cliff[0].chain, cliff[1].chain)
        self.assertEqual((cliff[0].cx0, cliff[0].cx1), (0, 1000))

    def test_a_gap_or_stacked_screens_break_the_chain(self):
        gap = build_floors([(0, 0, 1000, 800), (1100, 0, 2000, 800)])
        self.assertNotEqual(gap[0].chain, gap[1].chain)
        stacked = build_floors([(0, 0, 1000, 800), (0, 800, 1000, 1600)])
        self.assertNotEqual(stacked[0].chain, stacked[1].chain)

    def test_chain_does_not_depend_on_screen_order(self):
        f = build_floors([(2000, 0, 3000, 800), (0, 0, 1000, 800), (1000, 0, 2000, 800)])
        self.assertEqual(len({x.chain for x in f}), 1)
        self.assertEqual((f[0].cx0, f[0].cx1), (0, 3000))

    def test_nearest_floor(self):
        f = build_floors([(0, 0, 1000, 800), (1100, 0, 2000, 400)])
        self.assertEqual(nearest_floor(f, 500, 790), 0)
        self.assertEqual(nearest_floor(f, 1500, 390), 1)
        self.assertEqual(nearest_floor(f, 1050, 600), 0)                  # dans le trou : le plus proche

    def test_floor_here_tracks_only_a_neighbor_in_the_same_chain(self):
        f = build_floors([(0, 0, 1000, 800), (1000, 0, 2000, 800), (2200, 0, 3000, 800)])
        self.assertEqual(floor_here(f, 1500, 0), 1)
        self.assertEqual(floor_here(f, 2500, 0), 0)  # écran séparé : on reste dans la chaîne courante
        self.assertEqual(floor_here(f, 500, 0), 0)

    def test_snap_to_floor_clamps_center_before_returning_sprite_position(self):
        f = build_floors([(0, 0, 1000, 800), (1100, 0, 2000, 400)])
        self.assertEqual(snap_to_floor(f, 1050, 600, 80), (0, 960, 800))

    def test_clip_to_bounds_limits_a_segment_to_the_desktop(self):
        self.assertEqual(clip_to_bounds(-100, 1300, (-20, 0, 1000, 800)), (-20, 1000))


class PointsTest(unittest.TestCase):
    def test_clamp_point_keeps_the_cat_on_a_screen(self):
        rects = [(0, 140, 1000, 800), (1000, 140, 2000, 400)]
        self.assertEqual(clamp_point(rects, 500, 500), (500, 500))
        self.assertEqual(clamp_point(rects, -80, 900), (0, 800))
        self.assertEqual(clamp_point(rects, 1500, 700), (1500, 400))      # sous l'écran B : posé sur son bord bas
        self.assertEqual(clamp_point(rects, 5000, 0), (2000, 140))

    def test_bounds_and_nearest_rect(self):
        rects = [(0, 0, 1000, 800), (1000, 100, 2000, 600)]
        self.assertEqual(bounds(rects), (0, 0, 2000, 800))
        self.assertEqual(nearest_rect_index(rects, 1500, 300), 1)
        self.assertEqual(nearest_rect_index(rects, 10, 10), 0)
        self.assertEqual(nearest_rect_index(rects, 1500, 700), 1)         # sous B, mais plus près de B que de A


class PhrasesTest(unittest.TestCase):
    def test_every_mood_has_text(self):
        for mood, pool in phrases.MEOWS.items():
            self.assertTrue(pool, mood)
            self.assertTrue(all(isinstance(p, str) and p for p in pool), mood)

    def test_pick_stays_in_the_pool_and_covers_it(self):
        rng, seen = random.Random(3), set()
        for _ in range(500):
            seen.add(phrases.pick_meow(rng, "idle"))
        self.assertEqual(seen, set(phrases.MEOWS["idle"]))
        self.assertIn(phrases.pick_meow(rng, "petted"), phrases.MEOWS["petted"])
        self.assertIn(phrases.pick_meow(rng, "inconnu"), phrases.MEOWS["idle"])   # humeur inconnue : valeur par défaut

    def test_pick_survives_extreme_random_values(self):
        class Edge:
            def __init__(self, v):
                self.v = v

            def random(self):
                return self.v
        for v in (0.0, 0.999999999, 1.0):
            self.assertIn(phrases.pick_meow(Edge(v)), phrases.MEOWS["idle"])

    def test_delay_range(self):
        rng = random.Random(1)
        for _ in range(200):
            d = phrases.meow_delay(rng)
            self.assertTrue(phrases.MEOW_MIN_MS <= d <= phrases.MEOW_MAX_MS)


if __name__ == "__main__":
    unittest.main()
