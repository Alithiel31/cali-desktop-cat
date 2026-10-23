"""Jazz, le grand frère de Cali : un Nova Scotia Duck Tolling Retriever qui passe de temps en temps.

C'est une petite fenêtre transparente, comme le chat, mais sans souris ni clavier : Jazz ne gêne jamais un clic.
Il entre par un bord de l'écran, trotte sur le sol de l'écran de Cali (en traversant toute la chaîne d'écrans
collés), s'assoit parfois un instant, puis ressort de l'autre côté. Il n'utilise PAS le hasard du chat (`pet.rng`) :
la suite des tirages du chat, sur laquelle les tests s'appuient, reste la même.

États : away (absent, un compte à rebours tourne), walk (il trotte), sit (il s'assoit un instant).
"""
from __future__ import annotations

import random

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget

from .dog_sprite import DOG_FOOT_ROW, DOG_H, DOG_W, draw_dog
from .screens import floor_here

DOG_SPEED = 150.0               # px/s pour une échelle de 4 (le chat : 95) : il trotte plus vite qu'elle
FIRST_VISIT_S = (120.0, 300.0)  # première visite : entre 2 et 5 min après le lancement
BETWEEN_VISITS_S = (360.0, 900.0)   # ensuite : toutes les 6 à 15 min
RETRY_S = 30.0                  # visite impossible à cet instant (chat caché, concentration...) : on réessaie
SIT_CHANCE = 0.5                # une visite sur deux comprend un temps d'arrêt
SIT_S = (2.0, 4.0)
FRAME_S = 0.14                  # durée d'une image de la marche
BLINK_EVERY_MS = 3500
BLINK_MS = 120


class Dog(QWidget):
    def __init__(self, pet, rng=None):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
                         | Qt.WindowType.Tool | Qt.WindowType.WindowDoesNotAcceptFocus
                         | Qt.WindowType.WindowTransparentForInput)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.pet = pet
        self.rng = rng or random.Random()
        self.S = 0
        self.t = 0.0                    # temps de visite en ms (animations)
        self.state = "away"
        self.timer = self.rng.uniform(*FIRST_VISIT_S)
        self.fx = 0.0                   # bord gauche du sprite
        self.fy = 0.0                   # ordonnée des pattes
        self.dir = 1
        self.floor_idx = 0
        self.frame = 0
        self._frame_t = 0.0
        self._exit_x = 0.0              # position `fx` à partir de laquelle Jazz est entièrement sorti
        self._sit_x: float | None = None
        self._happy = False

    @property
    def active(self) -> bool:
        return self.state != "away"

    @property
    def width_px(self) -> float:
        return DOG_W * self.S

    # ───────────────────────── conditions
    def _allowed(self) -> bool:
        """Jazz ne passe pas quand le chat est caché ou endormi, ni pendant une session de concentration."""
        pet = self.pet
        return bool(pet.settings["jazz_visits"]) and not pet.hidden and not pet.sys_sleep and not pet.game.focus

    def _visit_still_ok(self) -> bool:
        return self._allowed() and self.S == int(self.pet.settings["scale"]) \
            and self.floor_idx < len(self.pet.floors)

    # ───────────────────────── cycle de vie d'une visite
    def start_visit(self) -> None:
        pet = self.pet
        self.S = int(pet.settings["scale"])
        self.setFixedSize(DOG_W * self.S, DOG_H * self.S)
        floor = pet.floors[min(pet.floor_idx, len(pet.floors) - 1)]
        self.floor_idx = floor.idx
        width = self.width_px
        if self.rng.random() < 0.5:                     # il vient de la gauche
            self.dir, self.fx, self._exit_x = 1, floor.cx0 - width, floor.cx1
        else:
            self.dir, self.fx, self._exit_x = -1, floor.cx1, floor.cx0 - width
        self.fy = floor.y
        span = abs(self._exit_x - self.fx)
        self._sit_x = self.fx + self.dir * span * self.rng.uniform(0.3, 0.7) \
            if self.rng.random() < SIT_CHANCE else None
        self.t, self.frame, self._frame_t, self._happy = 0.0, 0, 0.0, False
        self.state = "walk"
        self._place()
        self.show()

    def call_now(self) -> None:
        """Fait venir Jazz tout de suite (bouton de test du panneau)."""
        if self.state == "away" and self._allowed():
            self.start_visit()

    def cancel(self, retry_s: float = 2 * RETRY_S) -> None:
        """Interrompt la visite en cours (chat caché, réglage coupé...) ; il repassera plus tard."""
        self._end(retry_s)

    def _end(self, wait_s: float) -> None:
        self.state = "away"
        self.timer = wait_s
        self._sit_x = None
        self.hide()

    # ───────────────────────── boucle
    def step(self, dt: float) -> None:
        if self.state == "away":
            self.timer -= dt
            if self.timer <= 0:
                if self._allowed():
                    self.start_visit()
                else:
                    self.timer = RETRY_S
            return
        if not self._visit_still_ok():
            self.cancel()
            return
        self.t += dt * 1000
        if self.state == "sit":
            self.timer -= dt
            if self.timer <= 0:
                self.state = "walk"
        else:
            self._step_walk(dt)
        if self.state != "away":
            self._follow_floor(dt)
            self._place()
            self.update()

    def _step_walk(self, dt: float) -> None:
        self.fx += self.dir * DOG_SPEED * self.S / 4 * dt
        self._frame_t += dt
        if self._frame_t > FRAME_S:
            self._frame_t = 0.0
            self.frame ^= 1
        if self._sit_x is not None and self.dir * (self.fx - self._sit_x) >= 0:
            self._sit_x = None
            self.state, self.timer = "sit", self.rng.uniform(*SIT_S)
            self._happy = self.rng.random() < 0.5
        elif self.dir * (self.fx - self._exit_x) >= 0:
            self._end(self.rng.uniform(*BETWEEN_VISITS_S))

    def _follow_floor(self, dt: float) -> None:
        """Les pattes suivent le sol de l'écran sous lui (les écrans d'une chaîne n'ont pas tous la même hauteur)."""
        pet = self.pet
        chain = pet.floors[self.floor_idx]
        cx = min(max(self.fx + self.width_px / 2, chain.cx0), chain.cx1)
        self.floor_idx = floor_here(pet.floors, cx, self.floor_idx)
        want = pet.floors[self.floor_idx].y
        if abs(want - self.fy) > 0.01:
            self.fy += max(-420 * dt, min(420 * dt, want - self.fy))

    def _place(self) -> None:
        self.move(round(self.fx), round(self.fy - DOG_FOOT_ROW * self.S))

    # ───────────────────────── rendu
    def paintEvent(self, event) -> None:
        sitting = self.state == "sit"
        p = QPainter(self)
        draw_dog(p, self.S, pose="sit" if sitting else "walk", frame=0 if sitting else self.frame,
                 flip=self.dir < 0, t=self.t, blink=self.t % BLINK_EVERY_MS < BLINK_MS,
                 happy=sitting and self._happy)
        p.end()
