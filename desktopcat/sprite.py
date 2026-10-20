"""Le chat en pixel art, dessiné par code avec QPainter (aucune image externe).

Le dessin se fait sur une grille logique de GRID_W x GRID_H « pixels » ; S est la taille d'un pixel à l'écran.
Le chat regarde vers la droite ; `flip=True` le retourne. Les pieds touchent toujours la ligne FOOT_ROW.
"""
from __future__ import annotations

import math
from functools import cache

from PySide6.QtGui import QColor, QImage, QPainter, QPixmap

from .hats import BY_ID

GRID_W = 32
GRID_H = 36
OY = 6              # marge en haut de la grille pour les chapeaux hauts
FOOT_ROW = 35       # ligne (exclue) sous laquelle se trouve la surface où le chat marche
GIFT_SIZE = 16

OUTLINE = "#2a1d18"
EYE = "#241a1a"
PINK = "#f08aa4"
WHISKER = "#e9e2d8"

FURS = {
    # Tabby écaille : rayures brun-vert, plaques caramel, face crème, museau blanc, bout de queue noir.
    "ecaille": {"label": "Écaille", "base": "#8c7552", "dark": "#3a2f25", "belly": "#d8c3a0",
                "patch": "#d08c4a", "face": "#e0b072", "muzzle": "#f3eadc", "tip": "#1e1a18"},
    "orange": {"label": "Roux", "base": "#e8a35c", "dark": "#c47a2c", "belly": "#f6d9ae"},
    "gris": {"label": "Gris", "base": "#9aa3ad", "dark": "#6f7882", "belly": "#d8dde2"},
    "noir": {"label": "Noir", "base": "#3c3c44", "dark": "#27272d", "belly": "#585862"},
    "blanc": {"label": "Blanc", "base": "#f4f1ec", "dark": "#d3cdc4", "belly": "#ffffff"},
}


@cache
def qc(color: str) -> QColor:
    return QColor(color)


class _Canvas:
    __slots__ = ("p", "s", "flip")

    def __init__(self, painter: QPainter, s: int, flip: bool):
        self.p, self.s, self.flip = painter, s, flip

    def rect(self, x, y, w, h, color):
        if self.flip:
            x = GRID_W - x - w
        s = self.s
        fill = color if isinstance(color, QColor) else qc(color)
        self.p.fillRect(int(x * s), int(y * s), int(w * s), int(h * s), fill)


def _render(c: _Canvas, parts, decor, oy):
    """parts : formes contourées (la silhouette) ; decor : détails sans contour."""
    for x, y, w, h, _col in parts:
        c.rect(x - 1, y + oy - 1, w + 2, h + 2, OUTLINE)
    for x, y, w, h, col in parts:
        c.rect(x, y + oy, w, h, col)
    for x, y, w, h, col in decor:
        c.rect(x, y + oy, w, h, col)


def _eyes(kind, xs, cy):
    out = []
    for ex in xs:
        if kind == "open":
            out += [(ex, cy, 2, 3, EYE), (ex, cy, 1, 1, "#ffffff")]
        elif kind == "wide":
            out += [(ex - 1, cy - 1, 3, 4, EYE), (ex - 1, cy - 1, 1, 1, "#ffffff")]
        elif kind == "happy":
            out += [(ex - 1, cy + 2, 1, 1, EYE), (ex, cy + 1, 2, 1, EYE), (ex + 2, cy + 2, 1, 1, EYE)]
        else:                                   # fermés
            out += [(ex, cy + 2, 2, 1, EYE)]
    return out


def _sit(fur, t, working, blink, happy, surprised):
    tx = round(math.sin(t / 320))
    base, dark, belly = fur["base"], fur["dark"], fur["belly"]
    hc = fur.get("face", base)
    parts = [
        (6, 24, 5, 3, base), (4, 20, 3, 5, base), (3 + tx, 17, 3, 4, base),         # queue
        (9, 14, 13, 12, base),                                                       # corps
        (11, 24, 4, 4, base), (17, 24, 4, 4, base),                                  # pattes
        (11, 4, 12, 11, hc),                                                         # tête
        (11, 1, 3, 4, hc), (20, 1, 3, 4, hc),                                        # oreilles
    ]
    dx = 1 if working else 0
    kind = "wide" if surprised else "happy" if happy else "closed" if blink else "open"
    decor = [(13, 18, 6, 6, belly)]
    if "patch" in fur:
        decor += [(10, 15, 4, 3, fur["patch"]), (18, 20, 3, 4, fur["patch"]), (5, 21, 2, 3, fur["patch"])]
    if "muzzle" in fur:
        decor += [(14, 10, 6, 4, fur["muzzle"])]
    decor += [
        (15, 5, 1, 2, dark), (17, 5, 1, 3, dark), (19, 5, 1, 2, dark),               # rayures du front
        (9, 17, 2, 1, dark), (9, 20, 2, 1, dark), (20, 17, 2, 1, dark), (20, 20, 2, 1, dark),
        (3 + tx, 18, 3, 1, dark), (4, 22, 3, 1, dark),
    ]
    if "tip" in fur:
        decor += [(3 + tx, 17, 3, 2, fur["tip"])]
    decor += [(12, 2, 1, 2, PINK), (21, 2, 1, 2, PINK)]
    decor += _eyes(kind, [13 + dx, 19 + dx], 8)
    decor += [(16, 11, 2, 1, PINK),
              (8, 11, 3, 1, WHISKER), (8, 13, 3, 1, WHISKER), (23, 11, 3, 1, WHISKER), (23, 13, 3, 1, WHISKER)]
    if happy:
        decor += [(12, 12, 2, 1, "#ff9bb0"), (20, 12, 2, 1, "#ff9bb0")]
    return parts, decor, (12, 4)


def _walk(fur, t, frame, blink, happy):
    tx = round(math.sin(t / 200))
    base, dark, belly = fur["base"], fur["dark"], fur["belly"]
    hc = fur.get("face", base)
    parts = [
        (4, 15, 3, 3, base), (3 + tx, 9, 3, 6, base),
        (6, 13, 16, 10, base),
        (19, 8, 10, 10, hc),
        (20, 5, 3, 4, hc), (25, 5, 3, 4, hc),
    ]
    for i, lx in enumerate((7, 12, 17, 21)):
        parts.append((lx, 23, 3, 3 if (i + frame) % 2 == 1 else 5, base))
    decor = [(8, 19, 12, 4, belly)]
    if "patch" in fur:
        decor += [(8, 14, 4, 3, fur["patch"]), (15, 16, 4, 3, fur["patch"])]
    if "muzzle" in fur:
        decor += [(26, 13, 3, 4, fur["muzzle"])]
    decor += [
        (10, 13, 1, 3, dark), (14, 13, 1, 3, dark), (18, 13, 1, 3, dark),
        (22, 9, 1, 2, dark), (24, 9, 1, 2, dark),
        (3 + tx, 11, 3, 1, dark),
    ]
    if "tip" in fur:
        decor += [(3 + tx, 9, 3, 2, fur["tip"])]
    decor += [(21, 6, 1, 2, PINK), (26, 6, 1, 2, PINK)]
    decor += _eyes("happy", [26], 11) if happy else _eyes("closed" if blink else "open", [25], 11)
    decor += [(28, 13, 2, 2, PINK), (28, 16, 3, 1, WHISKER)]
    return parts, decor, (19, 8)


def _sleep(fur, t):
    b = round((math.sin(t / 700) + 1) / 2)             # respiration
    base, dark = fur["base"], fur["dark"]
    hc = fur.get("face", base)
    parts = [
        (4, 17, 24, 11, base),
        (7, 15 - b, 18, 2 + b, base),
        (19, 20, 9, 8, hc),
        (20, 17, 3, 3, hc), (25, 17, 3, 3, hc),
        (4, 24, 9, 4, dark),
    ]
    decor = []
    if "patch" in fur:
        decor += [(8, 18, 4, 3, fur["patch"]), (15, 19, 4, 3, fur["patch"])]
    if "muzzle" in fur:
        decor += [(24, 24, 4, 3, fur["muzzle"])]
    if "tip" in fur:
        decor += [(4, 25, 2, 3, fur["tip"])]
    decor += [(10, 17, 1, 3, dark), (14, 17, 1, 3, dark),
              (21, 18, 1, 1, PINK), (26, 18, 1, 1, PINK),
              (22, 24, 3, 1, EYE), (27, 25, 1, 1, PINK)]
    return parts, decor, (19, 19)


def _draw_hat(c: _Canvas, hat, anchor, t):
    if hat is None:
        return
    ax, bottom = anchor
    bob = round(math.sin(t / 400)) - 1 if hat.floating else 0
    y0 = bottom - len(hat.px) + 1 + bob + OY
    for r, row in enumerate(hat.px):
        for col, ch in enumerate(row):
            if ch == ".":
                continue
            if ch == "R":
                color = QColor.fromHslF(((col * 36 + t * 0.15) % 360) / 360, 0.9, 0.6)
            elif ch == "S":
                color = qc("#ffffff") if int(t // 250) % 2 else qc("#ffe066")
            else:
                color = hat.pal[ch]
            c.rect(ax + col, y0 + r, 1, 1, color)


def draw_cat(p: QPainter, S: int, *, pose="sit", frame=0, flip=False, fur="ecaille", hat=None,
             t=0.0, blink=False, happy=False, surprised=False):
    """Dessine le chat dans (0, 0, GRID_W*S, GRID_H*S).

    pose : sit | walk | sleep | work ; hat : id de chapeau ou None ; t : temps en ms (animations).
    """
    c = _Canvas(p, S, flip)
    fd = FURS.get(fur, FURS["ecaille"])
    if pose == "walk":
        parts, decor, anchor = _walk(fd, t, frame, blink, happy)
    elif pose == "sleep":
        parts, decor, anchor = _sleep(fd, t)
    else:
        parts, decor, anchor = _sit(fd, t, pose == "work", blink, happy, surprised)
    _render(c, parts, decor, OY)
    if pose == "work":                                  # ordinateur portable devant lui
        c.rect(21, 15 + OY, 10, 11, OUTLINE)
        c.rect(22, 16 + OY, 8, 7, "#2b3a55")
        c.rect(23, 17 + OY, 6, 1, "#7fd1ff")
        c.rect(23, 19 + OY, 4, 1, "#7fd1ff")
        c.rect(23, 21 + OY, 5, 1, "#7fd1ff")
        c.rect(20, 23 + OY, 12, 3, OUTLINE)
        c.rect(21, 24 + OY, 10, 1, "#c9ced6")
    _draw_hat(c, BY_ID.get(hat) if isinstance(hat, str) else hat, anchor, t)


def draw_gift(p: QPainter, S: int, t: float = 0.0):
    """Boîte cadeau qui saute un peu, dans (0, 0, GIFT_SIZE*S, GIFT_SIZE*S)."""
    p.save()
    p.translate(S, 0)
    c = _Canvas(p, S, False)
    lift = round(abs(math.sin(t / 260)))
    parts = [(1, 7, 12, 6, "#e8574d"), (0, 5, 14, 3, "#ff7a70"), (4, 2, 3, 3, "#ffd23f"), (7, 2, 3, 3, "#ffd23f")]
    decor = [(6, 7, 2, 6, "#ffd23f"), (6, 5, 2, 3, "#ffd23f")]
    if int(t // 400) % 2:
        decor += [(12, 1, 1, 1, "#ffffff"), (1, 3, 1, 1, "#ffffff")]
    _render(c, parts, decor, 2 - lift)
    p.restore()


def render_pixmap(S: int, locked: bool = False, **kw) -> QPixmap:
    """Chat complet dans un QPixmap transparent ; `locked` = silhouette grisée (chapeau pas encore trouvé)."""
    img = QImage(GRID_W * S, GRID_H * S, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(0)
    p = QPainter(img)
    draw_cat(p, S, **kw)
    if locked:
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        p.fillRect(img.rect(), QColor(18, 20, 30, 120))
    p.end()
    return QPixmap.fromImage(img)
