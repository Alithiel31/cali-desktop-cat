"""Jazz, le Nova Scotia Duck Tolling Retriever, en pixel art dessiné par code (comme le chat).

Même principe que sprite.py : une grille logique de DOG_W x DOG_H « pixels » de taille S à l'écran.
Jazz regarde vers la droite ; `flip=True` le retourne. Ses pattes touchent toujours la ligne DOG_FOOT_ROW.
Il est environ 1,5 fois plus grand que Cali, à taille de pixel identique.
"""
from __future__ import annotations

import math

from PySide6.QtGui import QColor, QImage, QPainter, QPixmap

from .sprite import EYE, OUTLINE, PINK, qc

DOG_W = 48
DOG_H = 40
DOG_FOOT_ROW = 40   # ligne (exclue) sous laquelle se trouve la surface où Jazz marche

# Pelage cuivré profond, franges plus claires, « chaussettes » et poitrail blancs.
COAT = {
    "base": "#a8572a",
    "dark": "#7b3b1c",
    "light": "#c97a3e",
    "white": "#f4efe6",
    "toe": "#d6c9b6",
    "nose": "#4a2e26",
    "shine": "#8a6a60",
}


class _DogCanvas:
    __slots__ = ("p", "s", "flip")

    def __init__(self, painter: QPainter, s: int, flip: bool):
        self.p, self.s, self.flip = painter, s, flip

    def rect(self, x, y, w, h, color):
        if self.flip:
            x = DOG_W - x - w
        s = self.s
        fill = color if isinstance(color, QColor) else qc(color)
        self.p.fillRect(int(x * s), int(y * s), int(w * s), int(h * s), fill)


def _render(c: _DogCanvas, parts, decor):
    """parts : formes contourées (la silhouette) ; decor : détails sans contour."""
    for x, y, w, h, _col in parts:
        c.rect(x - 1, y - 1, w + 2, h + 2, OUTLINE)
    for x, y, w, h, col in parts:
        c.rect(x, y, w, h, col)
    for x, y, w, h, col in decor:
        c.rect(x, y, w, h, col)


def _shift(items, dx):
    return [(x + dx, y, w, h, col) for x, y, w, h, col in items]


def _eyes(kind, xs, cy):
    out = []
    for ex in xs:
        if kind == "open":
            out += [(ex, cy, 2, 3, EYE), (ex, cy, 1, 1, "#ffffff")]
        elif kind == "happy":
            out += [(ex - 1, cy + 2, 1, 1, EYE), (ex, cy + 1, 2, 1, EYE), (ex + 2, cy + 2, 1, 1, EYE)]
        else:                                   # fermés
            out += [(ex, cy + 2, 2, 1, EYE)]
    return out


def _sit(t, blink, happy):
    """Assis, de face : c'est la pose de la photo, avec les deux chaussettes blanches devant."""
    k = COAT
    tx = round(math.sin(t / 180) * 2)           # la queue balaie le sol
    parts = [
        (2 + tx, 35, 4, 4, k["base"]), (5, 36, 9, 3, k["base"]),                    # queue
        (9, 26, 26, 13, k["base"]),                                                  # hanches
        (12, 17, 20, 20, k["base"]),                                                 # torse
        (15, 28, 5, 10, k["base"]), (24, 28, 5, 10, k["base"]),                      # pattes avant
        (14, 36, 7, 3, k["white"]), (23, 36, 7, 3, k["white"]),                      # chaussettes
        (13, 3, 18, 16, k["base"]),                                                  # tête
        (10, 5, 5, 13, k["dark"]), (29, 5, 5, 13, k["dark"]),                        # oreilles tombantes
    ]
    decor = [
        (17, 20, 10, 5, k["light"]),                                                 # fraise de poil
        (19, 22, 6, 8, k["white"]),                                                  # poitrail blanc
        (9, 33, 3, 5, k["light"]), (32, 33, 3, 5, k["light"]),                       # franges des hanches
        (5, 37, 8, 1, k["light"]),                                                   # plume de la queue
        (16, 37, 1, 2, k["toe"]), (18, 37, 1, 2, k["toe"]),
        (25, 37, 1, 2, k["toe"]), (27, 37, 1, 2, k["toe"]),
        (21, 4, 2, 8, k["white"]),                                                   # liste blanche
        (18, 11, 8, 7, k["light"]),                                                  # museau
        (20, 11, 4, 3, k["nose"]), (21, 11, 1, 1, k["shine"]),                       # truffe
        (21, 14, 2, 3, k["dark"]),                                                   # babines
    ]
    if happy:
        decor += [(20, 15, 4, 3, PINK)]                                              # langue
    kind = "happy" if happy else "closed" if blink else "open"
    decor += _eyes(kind, [17, 25], 9)
    decor += [(16, 7, 3, 1, k["light"]), (25, 7, 3, 1, k["light"])]                 # sourcils
    return _shift(parts, 2), _shift(decor, 2)


def _walk(t, frame, blink, happy):
    """De profil, au trot : queue en panache, pattes qui alternent, chaussettes blanches."""
    k = COAT
    tx = round(math.sin(t / 150) * 2)
    parts = [
        (3 + tx, 9, 4, 8, k["base"]), (5, 15, 4, 4, k["base"]),                      # queue
        (6, 16, 28, 12, k["base"]),                                                  # corps
        (32, 7, 11, 11, k["base"]),                                                  # tête
        (41, 11, 5, 5, k["base"]),                                                   # museau
        (32, 8, 4, 9, k["dark"]),                                                    # oreille tombante
    ]
    decor = [
        (10, 24, 20, 4, k["light"]),                                                 # ventre
        (8, 16, 22, 1, k["dark"]),                                                   # ligne du dos
        (30, 21, 4, 5, k["white"]),                                                  # poitrail
        (3 + tx, 11, 1, 5, k["light"]),                                              # plume de la queue
        (45, 11, 2, 3, k["nose"]), (46, 11, 1, 1, k["shine"]),                       # truffe
        (42, 14, 3, 1, k["dark"]),
        (39, 9, 3, 1, k["light"]), (41, 8, 1, 3, k["white"]),                       # sourcil, liste
    ]
    for i, lx in enumerate((8, 13, 27, 32)):
        h = 7 if (i + frame) % 2 == 1 else 11
        parts.append((lx, 28, 4, h, k["base"]))
        decor += [(lx, 28 + h - 3, 4, 3, k["white"]), (lx + 1, 28, 1, h - 3, k["light"])]
    kind = "happy" if happy else "closed" if blink else "open"
    decor += _eyes(kind, [39], 10)
    if happy:
        decor += [(43, 15, 3, 2, PINK)]
    return parts, decor


def _lie(t, blink, happy):
    """Couché à plat, la tête sur les pattes : il respire doucement."""
    k = COAT
    b = round((math.sin(t / 800) + 1) / 2)
    tx = round(math.sin(t / 400))
    parts = [
        (0, 35 + tx, 8, 4, k["base"]),                                               # queue
        (4, 25, 32, 14, k["base"]),                                                  # corps
        (8, 20 - b, 18, 6 + b, k["base"]),                                           # dos qui respire
        (30, 27, 14, 12, k["base"]),                                                 # tête
        (40, 31, 7, 8, k["base"]),                                                   # museau
        (30, 27, 5, 10, k["dark"]),                                                  # oreille
        (34, 35, 13, 4, k["white"]),                                                 # pattes avant blanches
    ]
    decor = [
        (8, 33, 16, 5, k["light"]),
        (10, 25, 1, 4, k["dark"]), (15, 25, 1, 4, k["dark"]),
        (29, 28, 1, 9, k["dark"]), (28, 29, 1, 6, k["light"]),                       # séparation cou / tête
        (30, 27, 14, 1, k["light"]),                                                 # dessus de la tête
        (44, 31, 3, 3, k["nose"]), (45, 31, 1, 1, k["shine"]),
        (41, 28, 1, 3, k["white"]),
        (37, 37, 1, 2, k["toe"]), (41, 37, 1, 2, k["toe"]), (45, 37, 1, 2, k["toe"]),
    ]
    decor += _eyes("closed" if not happy else "happy", [38], 29)
    return parts, decor


def draw_dog(p: QPainter, S: int, *, pose="sit", frame=0, flip=False, t=0.0, blink=False, happy=False):
    """Dessine Jazz dans (0, 0, DOG_W*S, DOG_H*S). pose : sit | walk | lie."""
    c = _DogCanvas(p, S, flip)
    if pose == "walk":
        parts, decor = _walk(t, frame, blink, happy)
    elif pose == "lie":
        parts, decor = _lie(t, blink, happy)
    else:
        parts, decor = _sit(t, blink, happy)
    _render(c, parts, decor)


def render_dog_pixmap(S: int, **kw) -> QPixmap:
    """Jazz complet dans un QPixmap transparent."""
    img = QImage(DOG_W * S, DOG_H * S, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(0)
    p = QPainter(img)
    draw_dog(p, S, **kw)
    p.end()
    return QPixmap.fromImage(img)
