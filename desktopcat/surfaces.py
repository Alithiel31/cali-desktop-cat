"""Calcul des « sols » sur lesquels le chat peut marcher : le bord haut des fenêtres visibles.

Fonctions pures (aucune dépendance à Qt ni à Windows), donc testables partout.
Toutes les coordonnées sont en pixels logiques (voir screens.py pour la conversion depuis les pixels Windows).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LWin:
    """Une fenêtre, en pixels logiques. L'ordre de la liste est l'ordre d'empilement (dessus en premier)."""
    hwnd: int
    title: str
    l: float  # noqa: E741 (l, t, r, b = left, top, right, bottom, comme dans tout le code)
    t: float
    r: float
    b: float
    zoomed: bool = False


@dataclass(frozen=True)
class Surface:
    hwnd: int | None      # None = le sol de l'écran
    y: float              # ordonnée du bord haut
    x0: float             # segment horizontal praticable
    x1: float
    wleft: float          # bord gauche de la fenêtre entière (sert à suivre la fenêtre quand elle bouge)
    title: str = ""
    floor: int = -1       # indice de l'écran quand la surface est un sol (hwnd None), -1 sinon


def subtract(segments, a: float, b: float):
    """Retire l'intervalle [a, b] d'une liste de segments (x0, x1)."""
    out = []
    for x0, x1 in segments:
        if b <= x0 or a >= x1:
            out.append((x0, x1))
            continue
        if a > x0:
            out.append((x0, a))
        if b < x1:
            out.append((b, x1))
    return out


def compute_surfaces(wins, work, headroom: float, min_width: float):
    """Bords hauts visibles des fenêtres.

    - work : (gauche, haut, droite, bas) de la zone utile de l'écran
    - headroom : place nécessaire au-dessus du bord pour que le chat y tienne debout
    - min_width : largeur minimale d'un segment pour qu'on puisse s'y poser
    Une fenêtre au-dessus dans l'empilement qui couvre la ligne du bord masque la partie correspondante.
    """
    wl, wt, wr, wb = work
    out = []
    for i, w in enumerate(wins):
        if w.zoomed:
            continue                                   # une fenêtre maximisée n'offre pas de bord libre
        y = w.t
        if y - headroom < wt or y > wb - 40:
            continue                                   # pas de place au-dessus, ou collée au sol
        segs = [(max(w.l, wl), min(w.r, wr))]
        if segs[0][1] <= segs[0][0]:
            continue
        for above in wins[:i]:
            if above.t <= y < above.b:
                segs = subtract(segs, above.l, above.r)
                if not segs:
                    break
        for x0, x1 in segs:
            if x1 - x0 >= min_width:
                out.append(Surface(w.hwnd, y, x0, x1, w.l, w.title))
    return out
