"""Ce que dit le chat. Fonctions pures : le hasard est passé en paramètre pour rester testable."""
from __future__ import annotations

MEOWS = {
    "idle": ["Miaou !", "Miaou~", "Mrrrp ?", "Prrrr…", "Mrow !", "Miaaaou", "Nyaa~", "Mew !", "Miaou miaou !",
             "Mrrr…", "Mip !", "Mraou ?"],
    "work": ["Mrp.", "Prrr… (je bosse)", "Miaou ?", "Tap tap tap…", "Mrrr."],
    "petted": ["Prrrrr~", "Mrrr ♥", "Miaou ♥", "Prrr prrr…", "Mrrp !"],
    "hungry": ["J'ai faim…", "Miaou… 🐟 ?", "Mrrr… (croquettes ?)", "Miaaaou ! (gamelle vide)"],
    "caught": ["Attrapée !", "Mrrp ! Je l'ai !", "Hop !", "Ma souris !"],
}

MEOW_MIN_MS = 45_000.0
MEOW_MAX_MS = 150_000.0


def pick_meow(rng, mood: str = "idle") -> str:
    pool = MEOWS.get(mood) or MEOWS["idle"]
    return pool[int(rng.random() * len(pool)) % len(pool)]


def meow_delay(rng) -> float:
    """Délai (ms) avant le prochain miaulement spontané."""
    return MEOW_MIN_MS + rng.random() * (MEOW_MAX_MS - MEOW_MIN_MS)
