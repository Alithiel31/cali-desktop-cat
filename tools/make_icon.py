"""Fabrique l'icône de l'exécutable (assets/desktopcat.ico) à partir du sprite du chat, dessiné par le code.

    python tools/make_icon.py

Le .ico contient plusieurs tailles (16 à 256 px) au format PNG, ce que Windows accepte depuis Vista.
À relancer seulement si le dessin du chat change ; le fichier produit est versionné.
"""
import os
import struct
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, Qt  # noqa: E402
from PySide6.QtGui import QImage, QPainter  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from desktopcat.sprite import GRID_H, GRID_W, OY, render_pixmap  # noqa: E402

SIZES = (256, 128, 64, 48, 32, 24, 16)
HEAD_MAX = 48               # à cette taille et en dessous, le chat entier serait illisible : on garde la tête
HEAD = (8, OY - 1, 18, 18)  # tête, oreilles et moustaches de la pose assise, en cases de la grille (x, y, w, h)
OUT = os.path.join(ROOT, "assets", "desktopcat.ico")


def square_cat(scale: int = 8) -> QImage:
    """Le chat assis, centré dans un carré transparent (le sprite est plus haut que large)."""
    cat = render_pixmap(scale, pose="sit", fur="ecaille", t=0).toImage()
    side = max(GRID_W, GRID_H) * scale
    img = QImage(side, side, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(0)
    p = QPainter(img)
    p.drawImage((side - cat.width()) // 2, (side - cat.height()) // 2, cat)
    p.end()
    return img


def cat_head(scale: int = 8) -> QImage:
    x, y, w, h = HEAD
    img = render_pixmap(scale, pose="sit", fur="ecaille", t=0).toImage()
    return img.copy(x * scale, y * scale, w * scale, h * scale)


def png_bytes(img: QImage) -> bytes:
    data = QByteArray()
    buf = QBuffer(data)
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    img.save(buf, "PNG")
    buf.close()
    return bytes(data)


def write_ico(path: str, images) -> None:
    """Écrit un .ico dont chaque entrée est une image PNG."""
    pngs = [png_bytes(im) for im in images]
    header = struct.pack("<HHH", 0, 1, len(pngs))
    offset = len(header) + 16 * len(pngs)
    entries, blobs = b"", b""
    for im, data in zip(images, pngs, strict=True):
        w = im.width() if im.width() < 256 else 0              # 0 signifie 256 dans le format .ico
        h = im.height() if im.height() < 256 else 0
        entries += struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(data), offset)
        blobs += data
        offset += len(data)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(header + entries + blobs)


def main() -> None:
    QApplication.instance() or QApplication([])
    body, head = square_cat(), cat_head()
    images = []
    for size in SIZES:
        src = head if size <= HEAD_MAX else body
        # Grandes tailles : pixels nets (pixel art) ; petites : lissage, sinon des traits disparaissent.
        mode = Qt.TransformationMode.FastTransformation if size >= 64 else Qt.TransformationMode.SmoothTransformation
        images.append(src.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, mode))
    write_ico(OUT, images)
    print("Icône écrite :", OUT)


if __name__ == "__main__":
    main()
