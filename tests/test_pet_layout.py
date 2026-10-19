"""Tests du placement visuel du chat et de ses widgets, sans Qt."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from desktopcat.pet_layout import compute_placement


class PetPlacementTest(unittest.TestCase):
    WORK = (0, 100, 1000, 760)

    def test_places_pet_gift_and_bubble_and_points_tail_at_the_cat(self):
        placement = compute_placement(900, 700, 40, 80, 1, self.WORK,
                                      (80, 60), (200, 80), 4, 20)

        self.assertEqual(placement.pet, (900, 660))
        self.assertEqual(placement.gift, (920, 644))
        self.assertEqual(placement.bubble, (800, 576))
        self.assertAlmostEqual(placement.bubble_tail_x, 149.6)

    def test_clamps_bubble_and_gift_inside_work_area_and_flips_gift_side(self):
        placement = compute_placement(5, 120, 40, 80, -1, self.WORK,
                                      (100, 50), (200, 80), 4, 20)

        self.assertEqual(placement.gift, (0, 74))
        self.assertEqual(placement.bubble, (0, 100))
        self.assertAlmostEqual(placement.bubble_tail_x, 35.4)

    def test_hidden_widgets_have_no_placement(self):
        placement = compute_placement(100, 200, 40, 80, 1, self.WORK, None, None, 4, 20)

        self.assertIsNone(placement.gift)
        self.assertIsNone(placement.bubble)
        self.assertIsNone(placement.bubble_tail_x)


if __name__ == "__main__":
    unittest.main()
