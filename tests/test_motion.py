"""Tests des calculs de trajectoire, sans Qt ni API Windows."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from desktopcat.motion import advance_fall, advance_jump, make_jump
from desktopcat.screens import Floor
from desktopcat.surfaces import Surface


class JumpMotionTest(unittest.TestCase):
    def test_jump_uses_target_distance_and_scale(self):
        destination = Surface(42, 300, 200, 800, 200, "Window")
        jump = make_jump(100, 600, 500, 300, 80, 4, destination)

        self.assertEqual(jump.duration, 0.45 + 360 / 1400 + 300 / 1500)
        self.assertEqual(jump.height, 345)
        self.assertEqual((jump.x1, jump.y1), (460, 300))
        self.assertIs(jump.dest, destination)

    def test_advance_jump_interpolates_and_clamps_at_landing(self):
        destination = Surface(None, 700, 0, 1000, 0, "Floor", floor=0)
        jump = make_jump(100, 400, 500, 700, 80, 4, destination)

        x, y, arrived = advance_jump(jump, jump.duration / 2)
        self.assertAlmostEqual(x, 280)
        self.assertLess(y, 550)  # la parabole passe au-dessus de la ligne entre départ et arrivée
        self.assertFalse(arrived)

        x, y, arrived = advance_jump(jump, jump.duration)
        self.assertTrue(arrived)
        self.assertEqual((x, y), (jump.x1, jump.y1))
        self.assertEqual(jump.elapsed, jump.duration)


class FallMotionTest(unittest.TestCase):
    def test_fall_lands_on_the_first_surface_crossed(self):
        window = Surface(42, 300, 100, 500, 100, "Window")
        floor = Floor(0, 700, 0, 1000, 0, 0, 1000)

        x, y, velocity, landing = advance_fall(250, 299.5, 0, 0.02, [window, Surface(None, 700, 0, 1000, 0,
                                                                                 "sol", floor=0)], [floor])

        self.assertGreater(y, 300)
        self.assertGreater(velocity, 0)
        self.assertIs(landing, window)
        self.assertEqual(x, 250)

    def test_fall_in_a_gap_is_repositioned_on_the_nearest_floor(self):
        floors = [Floor(0, 400, 0, 1000, 0, 0, 1000), Floor(1, 800, 1100, 2000, 1, 1100, 2000)]

        x, y, _velocity, landing = advance_fall(-1000, 790, 2400, 0.1, [], floors)

        self.assertEqual(x, 0)  # le chat est replacé au bord du sol le plus proche
        self.assertIsNotNone(landing)
        self.assertEqual(landing.floor, 0)
        self.assertEqual(y, 1030)


if __name__ == "__main__":
    unittest.main()
