"""Calcul des positions du chat et de ses éléments d'interface, sans dépendance à Qt."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PetPlacement:
    pet: tuple[int, int]
    gift: tuple[int, int] | None
    bubble: tuple[int, int] | None
    bubble_tail_x: float | None


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


def compute_placement(fx: float, fy: float, foot: int, cat_width: int, direction: int,
                      work: tuple, gift_size: tuple[int, int] | None,
                      bubble_size: tuple[int, int] | None, scale: int, grid_width: int) -> PetPlacement:
    """Calcule les positions écran, cadeau et bulle en conservant les éléments dans l'écran utile."""
    work_left, work_top, work_right, _work_bottom = work
    gift = None
    if gift_size is not None:
        gift_width, gift_height = gift_size
        gift_x = fx + 24 * scale if direction > 0 else fx + (grid_width - 24) * scale - gift_width
        gift = (round(_clamp(gift_x, work_left, work_right - gift_width)),
                round(fy - gift_height + scale))

    bubble = None
    bubble_tail_x = None
    if bubble_size is not None:
        bubble_width, bubble_height = bubble_size
        bubble_x = _clamp(fx + cat_width / 2 - bubble_width / 2,
                          work_left, max(work_left, work_right - bubble_width))
        bubble_y = max(work_top, fy - foot - bubble_height - 4)
        head_x = fx + cat_width * (0.62 if direction > 0 else 0.38)
        bubble = (round(bubble_x), round(bubble_y))
        bubble_tail_x = head_x - bubble_x

    return PetPlacement((round(fx), round(fy - foot)), gift, bubble, bubble_tail_x)
