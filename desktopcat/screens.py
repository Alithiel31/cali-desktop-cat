"""Géométrie multi-écrans. Fonctions pures (ni Qt ni Windows) : testables partout.

Deux systèmes de coordonnées coexistent :
- PHYSIQUE : pixels natifs de Windows (fenêtres, plein écran) ;
- LOGIQUE  : pixels de Qt (ce qu'utilisent les widgets du chat).

Dans Qt 6, le coin haut-gauche d'un écran est le même dans les deux systèmes ; seule sa taille est divisée par
le facteur d'échelle (dpr) de CET écran. La conversion d'un point se fait donc à partir de l'origine de l'écran
qui le contient, ce qui reste juste même quand les écrans n'ont pas la même échelle.
"""
from __future__ import annotations

from dataclasses import dataclass

STEP_TOL = 80.0     # dénivelé max (px) entre deux sols voisins pour que le chat passe de l'un à l'autre à pied
GAP_TOL = 2.0       # écart horizontal max entre deux écrans pour les considérer comme collés


@dataclass(frozen=True)
class ScreenInfo:
    geom: tuple             # (gauche, haut, droite, bas) logiques : écran entier
    work: tuple             # zone utile logique : écran moins barre des tâches
    dpr: float = 1.0

    @property
    def native(self) -> tuple:
        l, t, r, b = self.geom
        d = self.dpr or 1.0
        return (l, t, l + (r - l) * d, t + (b - t) * d)


def native_rects(screens) -> list:
    """Rectangles physiques entiers, dans l'ordre des écrans (sert à détecter le plein écran)."""
    return [tuple(round(v) for v in s.native) for s in screens]


def _dist2(rect, x, y, half_open=False) -> float:
    l, t, r, b = rect
    dx = l - x if x < l else (x - r + 1e-6 if (x >= r if half_open else x > r) else 0.0)
    dy = t - y if y < t else (y - b + 1e-6 if (y >= b if half_open else y > b) else 0.0)
    return dx * dx + dy * dy


def nearest_rect_index(rects, x: float, y: float) -> int:
    """Indice du rectangle qui contient (x, y), sinon du plus proche."""
    best, best_d = 0, float("inf")
    for i, rect in enumerate(rects):
        d = _dist2(rect, x, y)
        if d < best_d:
            best, best_d = i, d
    return best


def screen_at_native(screens, x: float, y: float) -> int:
    """Écran qui contient le point PHYSIQUE (x, y) (bords droit/bas exclus), sinon le plus proche."""
    best, best_d = 0, float("inf")
    for i, s in enumerate(screens):
        d = _dist2(s.native, x, y, half_open=True)
        if d < best_d:
            best, best_d = i, d
    return best


def to_logical(rect, screens) -> tuple:
    """Rectangle de fenêtre physique -> logique. L'écran de référence est celui du milieu du bord haut."""
    l, t, r, b = rect
    s = screens[screen_at_native(screens, (l + r) / 2, t)]
    gx, gy = s.geom[0], s.geom[1]
    d = s.dpr or 1.0
    return (gx + (l - gx) / d, gy + (t - gy) / d, gx + (r - gx) / d, gy + (b - gy) / d)


@dataclass(frozen=True)
class Floor:
    """Le sol d'un écran : le bas de sa zone utile. `chain` regroupe les sols qu'on peut traverser à pied."""
    idx: int                # indice de l'écran correspondant
    y: float
    x0: float
    x1: float
    chain: int
    cx0: float              # étendue horizontale de toute la chaîne
    cx1: float


def build_floors(works, step_tol: float = STEP_TOL, gap_tol: float = GAP_TOL) -> list:
    """Un sol par écran. Deux écrans côte à côte (collés, bords bas presque à la même hauteur)
    forment une chaîne : le chat les traverse en marchant."""
    n = len(works)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(n):
        for j in range(i + 1, n):
            a, b = works[i], works[j]
            gap = max(a[0], b[0]) - min(a[2], b[2])
            if gap <= gap_tol and abs(a[3] - b[3]) <= step_tol:
                parent[find(i)] = find(j)

    roots = sorted({find(i) for i in range(n)})
    chain_of = {r: k for k, r in enumerate(roots)}
    ext = {}
    for i in range(n):
        c = chain_of[find(i)]
        lo, hi = ext.get(c, (works[i][0], works[i][2]))
        ext[c] = (min(lo, works[i][0]), max(hi, works[i][2]))
    return [Floor(i, float(works[i][3]), float(works[i][0]), float(works[i][2]), chain_of[find(i)],
                  float(ext[chain_of[find(i)]][0]), float(ext[chain_of[find(i)]][1])) for i in range(n)]


def nearest_floor(floors, x: float, y: float) -> int:
    best, best_d = 0, float("inf")
    for f in floors:
        dx = f.x0 - x if x < f.x0 else (x - f.x1 if x > f.x1 else 0.0)
        d = dx * dx + (f.y - y) ** 2
        if d < best_d:
            best, best_d = f.idx, d
    return best


def clamp_point(rects, x: float, y: float) -> tuple:
    """Ramène (x, y) dans le rectangle le plus proche (pour garder le chat sur un écran quand on le porte)."""
    best = None
    for l, t, r, b in rects:
        cx, cy = min(max(x, l), r), min(max(y, t), b)
        d = (x - cx) ** 2 + (y - cy) ** 2
        if best is None or d < best[0]:
            best = (d, cx, cy)
    return (best[1], best[2]) if best else (x, y)


def bounds(rects) -> tuple:
    """Plus petit rectangle englobant tous les rectangles."""
    return (min(r[0] for r in rects), min(r[1] for r in rects), max(r[2] for r in rects), max(r[3] for r in rects))
