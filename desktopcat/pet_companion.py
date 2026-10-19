"""Réactions du compagnon aux cadeaux, aux bulles et aux sessions de jeu."""
from __future__ import annotations

import math

from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor

from .phrases import meow_delay, pick_meow

STANDING = ("idle", "walk", "nap", "wait", "work", "sleep")


class PetCompanion:
    """Comportements expressifs du chat; l'état partagé reste porté par Pet."""

    def __init__(self, pet):
        self.pet = pet

    def try_meow(self) -> None:
        pet = self.pet
        free = (pet.state in ("idle", "walk", "work") and not pet._temp and not pet.gift_visible
                and not pet.sys_sleep and pet._press is None)
        if not free:
            pet.next_meow = pet.t + 4000
            return
        pet.say(pick_meow(pet.rng, "work" if pet.state == "work" else "idle"), 2200)
        if pet.rng.random() < 0.3:
            pet.fx_particle("heart")
        pet.next_meow = pet.t + meow_delay(pet.rng)

    def show_gift(self) -> None:
        pet = self.pet
        pet.state = "wait"
        pet.gift_visible = True
        pet.gift.show()
        pet.say("Miaou ! J'ai un cadeau pour toi 🎁", 6000)

    def say(self, html: str, ms: float = 3500, border: str = "#2a1d18") -> None:
        pet = self.pet
        pet._temp = True
        pet._temp_until = pet.t + ms
        pet._focus_text = ""
        pet.bubble.show_html(html, border)

    def bubble_tick(self) -> None:
        pet = self.pet
        if pet._temp and pet.t > pet._temp_until:
            pet._temp = False
            pet.bubble.hide()
        if pet._temp:
            return
        focus = pet.game.focus
        if focus:
            left = max(0, math.ceil(focus["ends_at"] - pet.game.clock()))
            text = f"⏱ {left // 60:02d}:{left % 60:02d}"
            if text != pet._focus_text:
                pet._focus_text = text
                pet.bubble.show_html(text)
        elif pet.bubble.isVisible():
            pet.bubble.hide()
            pet._focus_text = ""

    def spawn_particle(self, kind: str) -> None:
        pet = self.pet
        head_x = pet.fx + pet.CW * (0.62 if pet.dir > 0 else 0.38)
        pet.fxl.spawn(kind, head_x + pet.rng.uniform(-12, 12), pet.fy - pet.FOOT * 0.85)

    def gift_clicked(self) -> None:
        pet = self.pet
        result = pet.game.claim_gift()
        pet.gift_visible = False
        pet.gift.hide()
        if pet.state == "wait":
            pet._idle(3.0)
        if not result:
            return
        hat, rarity = result["hat"], result["rarity"]
        pet.happy_until = pet.t + 3500
        head = ("Nouveau chapeau : " + hat.name) if result["is_new"] \
            else f"{hat.name} (doublon ×{result['count']})"
        label_color = QColor(rarity["color"]).darker(150).name()
        pet.say(f"{head} — <b style='color:{label_color}'>{rarity['label']}</b>", 6500, rarity["color"])
        for i in range(5):
            QTimer.singleShot(i * 150, lambda: pet.fx_particle("star"))

    def sleeping_changed(self, asleep: bool) -> None:
        pet = self.pet
        pet.sys_sleep = asleep
        if asleep:
            if pet.state in STANDING:
                pet.state = "sleep"
        elif pet.state == "sleep":
            pet._idle(1.0)
            pet.happy_until = pet.t + 2000
            pet.say("Te revoilà !", 2500)
            pet.fx_particle("heart")
        pet._adapt_loop()

    def focus_changed(self, focus) -> None:
        pet = self.pet
        if focus:
            pet.say("Au travail ! Je reste avec toi 🐾", 3500)
            if pet.state in ("idle", "walk", "nap", "wait"):
                pet._go_work()
        elif pet.state == "work":
            pet._idle(1.0)

    def focus_finished(self, total: int) -> None:
        pet = self.pet
        pet.happy_until = pet.t + 4000
        pet.say("Bravo, session terminée !", 4000)
        for i in range(4):
            QTimer.singleShot(i * 200, lambda: pet.fx_particle("heart"))
