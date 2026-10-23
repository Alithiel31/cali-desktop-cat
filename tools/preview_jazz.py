"""Rend Jazz (et Cali à côté, pour l'échelle) dans tools/out/jazz_preview.png.

    python tools/preview_jazz.py
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter  # noqa: E402

from desktopcat.dog_sprite import DOG_H, DOG_W, draw_dog  # noqa: E402
from desktopcat.sprite import GRID_H, GRID_W, draw_cat  # noqa: E402

S = 6
POSES = [("sit", {}), ("sit", {"happy": True}), ("walk", {"frame": 0}), ("walk", {"frame": 1}), ("lie", {})]


def main() -> str:
    app = QGuiApplication.instance() or QGuiApplication([])  # noqa: F841
    pad = 3 * S
    width = pad + sum(DOG_W * S + pad for _ in POSES) + GRID_W * S + pad
    img = QImage(width, DOG_H * S + 2 * pad, QImage.Format.Format_ARGB32)
    img.fill(QColor("#e9e4dc"))
    p = QPainter(img)
    x = pad
    for pose, kw in POSES:
        p.save()
        p.translate(x, pad)
        draw_dog(p, S, pose=pose, t=400, **kw)
        p.restore()
        x += DOG_W * S + pad
    p.save()
    p.translate(x, pad + (DOG_H - GRID_H) * S)       # Cali, pieds alignés sur ceux de Jazz
    draw_cat(p, S, pose="sit", t=400)
    p.restore()
    p.end()
    out_dir = os.path.join(ROOT, "tools", "out")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "jazz_preview.png")
    img.save(path)
    return path


if __name__ == "__main__":
    print(main())
