"""Calculs de mouvement (marche, sauts et chutes) sans dépendance à Qt ni à Windows."""
from __future__ import annotations

from dataclasses import dataclass

from .screens import nearest_floor
from .surfaces import Surface

GRAVITY = 2200.0          # px/s²
MAX_FALL = 2400.0         # px/s


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


def advance_fall(x: float, previous_y: float, velocity: float, dt: float,
                 surfaces: list[Surface], floors) -> tuple[float, float, float, Surface | None]:
    """Avance une chute et renvoie la première surface touchée (ou le sol de secours)."""
    velocity = min(velocity + GRAVITY * dt, MAX_FALL)
    y = previous_y + velocity * dt
    landing = None
    for surface in surfaces:
        if surface.x0 <= x <= surface.x1 and previous_y - 0.5 <= surface.y <= y + 0.5:
            if landing is None or surface.y < landing.y:
                landing = surface
    if landing is None and y >= max(floor.y for floor in floors):
        floor = floors[nearest_floor(floors, x, y)]
        x = max(floor.x0, min(floor.x1, x))
        landing = Surface(None, floor.y, floor.x0, floor.x1, floor.x0, "sol", floor=floor.idx)
    return x, y, velocity, landing


def advance_walk(x: float, target: float, left: float, right: float, sprite_width: float,
                 speed: float, dt: float, frame_elapsed: float, frame: int):
    """Avance une marche sur une surface et renvoie position, animation, direction et arrivée."""
    margin = sprite_width * 0.25
    low, high = left + margin, right - margin
    target = max(low, min(high, target)) if high >= low else x
    distance = target - x
    step = speed * dt
    frame_elapsed += dt
    if frame_elapsed > 0.17:
        frame_elapsed = 0.0
        frame ^= 1
    if abs(distance) <= step:
        return x + distance, frame_elapsed, frame, 0, True
    return x + (step if distance > 0 else -step), frame_elapsed, frame, (1 if distance > 0 else -1), False
