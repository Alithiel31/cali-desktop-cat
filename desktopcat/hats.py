"""Catalogue des chapeaux et tirage au sort.

Chaque chapeau est un petit sprite de 10 colonnes : '.' = transparent, les autres lettres
pointent vers `pal`. Deux lettres spéciales : 'R' = arc-en-ciel animé, 'S' = étoile qui scintille.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

RARITIES = {
    "common":    {"label": "Commun",     "weight": 60.0, "color": "#9aa4b2", "sell": 5},
    "uncommon":  {"label": "Peu commun", "weight": 22.0, "color": "#4ec27a", "sell": 12},
    "rare":      {"label": "Rare",       "weight": 11.0, "color": "#4a90e2", "sell": 30},
    "epic":      {"label": "Épique",     "weight": 5.0,  "color": "#a259e6", "sell": 80},
    "legendary": {"label": "Légendaire", "weight": 1.5,  "color": "#f5a623", "sell": 250},
    "exotic":    {"label": "Exotique",   "weight": 0.5,  "color": "#ff4fa3", "sell": 800},
}
RARITY_ORDER = list(RARITIES)


@dataclass(frozen=True)
class Hat:
    id: str
    name: str
    rarity: str
    pal: dict
    px: tuple
    animated: bool = False
    floating: bool = False


def _h(id, name, rarity, pal, px, **kw):
    return Hat(id, name, rarity, pal, tuple(px), **kw)


HATS = [
    # --- Communs
    _h("beanie", "Bonnet", "common", {"a": "#d9534f", "b": "#f2f2f2", "c": "#f2f2f2"},
       ["....cc....", "...aaaa...", "..aaaaaa..", ".aaaaaaaa.", "bbbbbbbbbb"]),
    _h("cap", "Casquette", "common", {"a": "#3b6fd6", "b": "#274a99"},
       ["..aaaaaa..", ".aaaaaaaa.", ".aaaaaaaa.", "bbbbbbbbbb"]),
    _h("bow", "Ruban rose", "common", {"a": "#ff7eb6", "b": "#d9558a"},
       ["aa......aa", "aaa....aaa", "aabbbbbbaa", "aaa....aaa", "aa......aa"]),
    _h("band", "Bandeau sport", "common", {"a": "#ffffff", "b": "#e03c3c"},
       ["aaaaaaaaaa", "bbbbbbbbbb"]),
    # --- Peu communs
    _h("straw", "Chapeau de paille", "uncommon", {"a": "#e8c872", "b": "#c79a3a", "c": "#d9534f"},
       ["..aaaaaa..", "..aaaaaa..", "..cccccc..", "bbbbbbbbbb"]),
    _h("beret", "Béret", "uncommon", {"a": "#7a1f3d", "b": "#561329"},
       ["....bb....", ".aaaaaaaa.", "aaaaaaaaaa", ".aaaaaaaa."]),
    _h("party", "Chapeau de fête", "uncommon", {"a": "#ffd23f", "b": "#ee4266", "c": "#3bceac"},
       ["....cc....", "....ab....", "...abab...", "...baba...", "..ababab..", ".cccccccc."]),
    _h("flower", "Couronne de fleurs", "uncommon", {"a": "#ff9ecb", "b": "#ffe066", "c": "#4ec27a"},
       [".a..b..a..", "abacccaaba", "cccccccccc"]),
    # --- Rares
    _h("cowboy", "Chapeau de cowboy", "rare", {"a": "#8b5a2b", "b": "#5e3a17", "c": "#d9b26f"},
       ["..a....a..", "..aaaaaa..", "..aaaaaa..", "..cccccc..", "bbbbbbbbbb"]),
    _h("chef", "Toque de chef", "rare", {"a": "#ffffff", "b": "#dcdcdc"},
       ["..aaaaaa..", ".aaaaaaaa.", ".aaaaaaaa.", "..aaaaaa..", "..bbbbbb.."]),
    _h("wizard", "Chapeau de sorcier", "rare", {"a": "#4b3b9a", "b": "#ffd23f", "c": "#2e2370"},
       ["....aa....", "....aa....", "...abaa...", "...aaaa...", "..aaabaa..", ".aaaaaaaa.", "cccccccccc"]),
    _h("headphones", "Casque audio", "rare", {"a": "#2d2d2d", "b": "#ff4fa3"},
       ["..aaaaaa..", ".a......a.", "ab......ba", "bb......bb"]),
    # --- Épiques
    _h("tophat", "Haut-de-forme", "epic", {"a": "#1d1d1f", "b": "#c0392b", "c": "#3a3a3d"},
       ["..aaaaaa..", "..aaaaaa..", "..aaaaaa..", "..bbbbbb..", "cccccccccc"]),
    _h("viking", "Casque viking", "epic", {"a": "#8f98a3", "b": "#f0e6c8", "c": "#5f6872"},
       ["b........b", "b.aaaaaa.b", "bbaaaaaabb", ".baaaaaab.", "..cccccc.."]),
    _h("pirate", "Tricorne de pirate", "epic", {"a": "#222222", "b": "#e8e8e8", "c": "#c9a227"},
       ["...aaaa...", "..aabbaa..", ".aaabbaaa.", "aaaaccaaaa", "a.aaaaaa.a"]),
    # --- Légendaires
    _h("crown", "Couronne royale", "legendary",
       {"a": "#ffd23f", "b": "#e63946", "c": "#c9a227", "d": "#3b9dff"},
       ["a..a..a..a", "aa.aaaa.aa", "aaaaaaaaaa", "abaadaabaa", "cccccccccc"]),
    _h("halo", "Auréole", "legendary", {"a": "#fff3a3", "b": "#ffd23f"},
       ["..bbbbbb..", ".a......a.", "..bbbbbb.."], floating=True),
    _h("astro", "Casque de cosmonaute", "legendary", {"a": "#f5f7fa", "b": "#9bd1ff", "c": "#c3ccd6"},
       ["..aaaaaa..", ".aaaaaaaa.", "aabbbbbbaa", "aabbbbbbaa", "accccccca."]),
    # --- Exotiques (animés)
    _h("rainbow", "Couronne arc-en-ciel", "exotic", {"a": "#ffffff"},
       ["..RRRRRR..", ".RRRRRRRR.", "RRRRRRRRRR", "aaaaaaaaaa"], animated=True),
    _h("galaxy", "Chapeau galaxie", "exotic", {"a": "#1b1464", "b": "#5b3fd6", "c": "#2a1b8f"},
       ["..aaSaaa..", ".aabaSaaa.", "aaSaabaaaa", "cccccccccc"], animated=True),
]

BY_ID = {h.id: h for h in HATS}


def roll_hat(rng=None) -> Hat:
    """Tirage pondéré : d'abord la rareté, puis un chapeau au hasard dans cette rareté."""
    rng = rng or random
    total = sum(r["weight"] for r in RARITIES.values())
    x = rng.random() * total
    rarity = "common"
    for key, r in RARITIES.items():
        if x < r["weight"]:
            rarity = key
            break
        x -= r["weight"]
    pool = [h for h in HATS if h.rarity == rarity]
    return pool[int(rng.random() * len(pool)) % len(pool)]
