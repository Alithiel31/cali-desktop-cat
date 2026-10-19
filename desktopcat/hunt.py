"""Chasse au curseur : quand la souris s'arrête près de lui, le chat la guette puis bondit dessus.

Fonctions pures (aucune dépendance à Qt ni à Windows). Coordonnées en pixels logiques, temps en secondes.
"""
from __future__ import annotations

STILL_MIN_S = 1.2           # la souris doit être immobile depuis au moins ce temps...
STILL_MAX_S = 15.0          # ...mais pas depuis trop longtemps : une souris oubliée n'intéresse pas le chat
STALK_S = (1.0, 2.0)        # durée de l'affût avant le bond
COOLDOWN_S = (25.0, 60.0)   # repos entre deux chasses réussies
ESCAPED_COOLDOWN_S = 8.0    # la proie a bougé pendant l'affût : il boude un peu
MAX_REACH = 520.0           # portée du bond (pour une échelle de 4)


def cursor_is_resting(now_s: float, moved_at_s: float | None) -> bool:
    """Vrai si la souris a bougé puis s'est arrêtée récemment (une souris qui n'a jamais bougé ne compte pas)."""
    return moved_at_s is not None and STILL_MIN_S <= now_s - moved_at_s <= STILL_MAX_S


def cursor_in_reach(cursor_x: float, cursor_y: float, cat_cx: float, feet_y: float, x0: float, x1: float,
                    cat_w: float, foot: float, scale: float) -> bool:
    """Vrai si la souris est une proie possible : au-dessus de la surface du chat, à sa hauteur, ni trop près ni
    trop loin. `x0`, `x1` : bords de la surface ; `foot` : hauteur du chat au-dessus de ses pieds."""
    margin = cat_w * 0.25
    if not x0 + margin <= cursor_x <= x1 - margin:
        return False
    if not cat_w * 0.6 <= abs(cursor_x - cat_cx) <= MAX_REACH * scale / 4:
        return False
    return feet_y - foot * 1.2 <= cursor_y <= feet_y + 4
