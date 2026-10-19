"""Adaptation des fenêtres Windows en surfaces praticables pour le chat."""
from __future__ import annotations

from . import winapi
from .screens import to_logical
from .surfaces import LWin, Surface, compute_surfaces


def floor_surfaces(floors) -> list[Surface]:
    """Représente le bas de chaque écran comme une surface praticable."""
    return [Surface(None, floor.y, floor.x0, floor.x1, floor.x0, "sol", floor=floor.idx) for floor in floors]


def window_geometry(hwnd: int, screens, enabled: bool, get_window_rect=None):
    """Renvoie (haut, gauche, droite) en coordonnées Qt pour une fenêtre encore praticable."""
    if not enabled:
        return None
    get_window_rect = get_window_rect or winapi.window_rect
    rect = get_window_rect(hwnd)
    if rect is None:
        return None
    left, top, right, _bottom = to_logical(rect, screens)
    return top, left, right


def build_surfaces(screens, works, floors, enabled: bool, excluded_hwnds, foot: float, cat_width: float,
                   list_windows=None) -> list[Surface]:
    """Construit les bords de fenêtres praticables et ajoute le sol de chaque écran."""
    result = []
    if enabled:
        list_windows = list_windows or winapi.list_windows
        windows = [LWin(window.hwnd, window.title, *to_logical(window.rect, screens), window.zoomed)
                   for window in list_windows(exclude=excluded_hwnds)]
        for work in works:
            result.extend(compute_surfaces(windows, work, foot, cat_width * 0.9))
    result.extend(floor_surfaces(floors))
    return result
