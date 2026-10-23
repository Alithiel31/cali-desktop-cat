"""Tests du sprite de Jazz (hors écran, Qt en mode offscreen)."""
import os
import sys
import unittest

if sys.platform != "win32":
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from desktopcat.dog_sprite import DOG_FOOT_ROW, DOG_H, DOG_W, render_dog_pixmap

APP = QApplication.instance() or QApplication([])
S = 4


def _opaque_bounds(pixmap):
    img = pixmap.toImage()
    xs, ys = [], []
    for y in range(img.height()):
        for x in range(img.width()):
            if img.pixelColor(x, y).alpha() > 0:
                xs.append(x)
                ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


class DogSpriteTest(unittest.TestCase):
    def test_every_pose_draws_inside_the_grid_and_stands_on_the_foot_row(self):
        for pose in ("sit", "walk", "lie"):
            for frame in (0, 1):
                with self.subTest(pose=pose, frame=frame):
                    pm = render_dog_pixmap(S, pose=pose, frame=frame, t=123.0)
                    self.assertEqual((pm.width(), pm.height()), (DOG_W * S, DOG_H * S))
                    x0, y0, x1, y1 = _opaque_bounds(pm)
                    self.assertGreaterEqual(x0, 0)
                    self.assertGreaterEqual(y0, 0)
                    self.assertEqual(y1 + 1, DOG_FOOT_ROW * S)      # les pieds touchent la ligne du sol

    def test_flip_mirrors_the_drawing(self):
        straight = render_dog_pixmap(S, pose="walk", t=0.0).toImage()
        flipped = render_dog_pixmap(S, pose="walk", t=0.0, flip=True).toImage()
        self.assertEqual(straight.flipped(Qt.Orientation.Horizontal), flipped)

    def test_happy_and_blink_change_the_face(self):
        calm = render_dog_pixmap(S, pose="sit", t=0.0).toImage()
        self.assertNotEqual(calm, render_dog_pixmap(S, pose="sit", t=0.0, happy=True).toImage())
        self.assertNotEqual(calm, render_dog_pixmap(S, pose="sit", t=0.0, blink=True).toImage())


if __name__ == "__main__":
    unittest.main()
