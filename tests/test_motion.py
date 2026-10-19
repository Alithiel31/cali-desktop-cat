"""Tests des calculs de trajectoire, sans Qt ni API Windows."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from desktopcat.motion import advance_jump, make_jump
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


if __name__ == "__main__":
    unittest.main()
