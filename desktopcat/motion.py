"""Calculs de trajectoire sans dépendance à Qt ni à Windows."""
from __future__ import annotations

from dataclasses import dataclass

from .surfaces import Surface


@dataclass
class Jump:
    """Trajectoire parabolique entre la position courante et une surface cible."""

    x0: float
    y0: float
    x1: float
    y1: float
    dest: Surface
    duration: float
    height: float
    elapsed: float = 0.0


def make_jump(x: float, y: float, target_cx: float, target_y: float, sprite_width: float,
              scale: float, dest: Surface) -> Jump:
    distance = abs(target_cx - (x + sprite_width / 2))
    upward = max(0.0, y - target_y)
    return Jump(
        x, y, target_cx - sprite_width / 2, target_y, dest,
        0.45 + distance / 1400 + upward / 1500,
        max(60.0, upward + 45.0) * scale / 4,
    )


def advance_jump(jump: Jump, dt: float) -> tuple[float, float, bool]:
    """Avance le saut et renvoie (x, y, arrivé)."""
    jump.elapsed = min(jump.duration, jump.elapsed + dt)
    progress = jump.elapsed / jump.duration
    x = jump.x0 + (jump.x1 - jump.x0) * progress
    y = jump.y0 + (jump.y1 - jump.y0) * progress - 4 * jump.height * progress * (1 - progress)
    return x, y, progress >= 1.0
