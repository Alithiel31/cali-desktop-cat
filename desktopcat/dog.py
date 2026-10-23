"""Jazz, le grand frère de Cali : un Nova Scotia Duck Tolling Retriever qui passe de temps en temps.

C'est une petite fenêtre transparente, comme le chat, mais sans souris ni clavier : Jazz ne gêne jamais un clic.
Il entre par un bord de l'écran et trotte sur le sol de l'écran de Cali (en traversant toute la chaîne d'écrans
collés). Selon le cas, il vient lui dire bonjour (il s'arrête à côté d'elle, elle réagit, puis il repart par où il est
venu) ou il ne fait que passer (avec parfois un temps d'arrêt), et il ressort de l'autre côté.

Ses décisions n'utilisent PAS le hasard du chat (`pet.rng`), pour ne pas changer la suite de tirages du chat sur
laquelle les tests s'appuient. Seule la dispersion des petits cœurs de Cali, purement visuelle, y puise (`fx_particle`).

Si Cali fait la sieste, il vient plutôt se coucher contre elle (état `lie`) et reste tant qu'elle dort ; à son
réveil il repart, et elle le suit souvent.

Quand il repart, Cali le suit souvent quelques secondes (`_escort`) : il ralentit à son allure, elle trottine
derrière lui, puis elle décroche et il reprend son rythme.

Il a sa propre bulle (`Bubble`, transparente aux clics) : des aboiements et, plus rarement, le « cri de Toller »
(« Aouaouaouaou ! »). Il ne parle que si les bulles sont activées (réglage « meows ») et se tait en arrivant près de
Cali pour lui laisser répondre. Ses phrases ont leur propre hasard (`voice`), séparé de celui de ses déplacements.

États : away (absent, un compte à rebours tourne), walk (il trotte), sit (il s'assoit un instant en passant),
        greet (il est assis près de Cali, qui lui répond), lie (il dort contre Cali pendant sa sieste).
"""
from __future__ import annotations

import random

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget

from .dog_sprite import DOG_FOOT_ROW, DOG_H, DOG_W, draw_dog
from .phrases import pick_bark
from .screens import floor_here
from .widgets import Bubble

DOG_SPEED = 150.0               # px/s pour une échelle de 4 (le chat : 95) : il trotte plus vite qu'elle
FIRST_VISIT_S = (120.0, 300.0)  # première visite : entre 2 et 5 min après le lancement
BETWEEN_VISITS_S = (360.0, 900.0)   # ensuite : toutes les 6 à 15 min
RETRY_S = 30.0                  # visite impossible à cet instant (chat caché, concentration...) : on réessaie
SIT_CHANCE = 0.5                # une visite « de passage » sur deux comprend un temps d'arrêt
SIT_S = (2.0, 4.0)
GREET_CHANCE = 0.6              # visites où Jazz vient voir Cali (si elle est là, au sol et disponible)
GREET_S = (3.5, 6.0)            # durée du tête-à-tête
FOLLOW_CHANCE = 0.7             # après le tête-à-tête, Cali le suit 7 fois sur 10
FOLLOW_S = (4.0, 8.0)           # durée pendant laquelle elle le suit
ESCORT_SPEED = 0.97             # son allure en escorte, par rapport à celle de Cali : elle rattrape donc peu à peu
FOLLOW_START_PX = 8             # Cali ne repart que s'il s'est éloigné d'au moins ça
JOIN_CHANCE = 0.8               # visites où Cali fait la sieste : il vient presque toujours se coucher près d'elle
JOIN_S = (12.0, 25.0)           # sa sieste dure au moins ça une fois qu'il est couché contre elle
JOIN_MAX_S = 90.0               # il ne dort jamais plus longtemps que ça, quoi qu'elle fasse
LIE_GAP = 36                    # écart entre leurs centres quand ils dorment côte à côte, en « pixels » de grille
TOUCH_GAP = 22                  # écart entre les centres de Cali et de Jazz assis, en « pixels » de grille
FRAME_S = 0.14                  # durée d'une image de la marche
BARK_FIRST_S = (1.5, 5.0)       # premier aboiement possible, après son entrée
BARK_EVERY_S = (4.0, 9.0)       # ensuite, une occasion d'aboyer toutes les 4 à 9 s...
BARK_CHANCE = 0.6               # ...saisie 6 fois sur 10
SCREAM_CHANCE = 0.2             # dont une fois sur cinq par le cri de Toller
SPOT_PX = 260                   # distance (échelle 4) à laquelle il repère Cali et l'appelle
BARK_MS = 1800                  # durée d'une bulle d'aboiement
SCREAM_MS = 2600
QUIET_NEAR_PX = 100             # (échelle 4) il ne parle pas par-dessus la bulle de Cali quand elle est si près
BLINK_EVERY_MS = 3500
BLINK_MS = 120


class Dog(QWidget):
    def __init__(self, pet, rng=None, voice=None):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
                         | Qt.WindowType.Tool | Qt.WindowType.WindowDoesNotAcceptFocus
                         | Qt.WindowType.WindowTransparentForInput)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.pet = pet
        self.rng = rng or random.Random()
        self.voice = voice or random.Random()      # ses phrases : hasard à part, pour ne pas changer ses déplacements
        self._bubble: Bubble | None = None      # créée au premier aboiement seulement : une fenêtre de moins sinon
        self._bubble_until = 0.0
        self._bark_in = 0.0
        self._called = False            # il a déjà appelé Cali pendant cette approche
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
        self._back_x = 0.0              # idem, du côté par lequel il est entré
        self._side = 1                  # sens de son arrivée : 1 = il vient de la gauche
        self._approach = False          # il va voir Cali
        self._escort = 0.0              # secondes pendant lesquelles Cali le suit encore
        self._sit_x: float | None = None
        self._happy = False
        self._heart_in = 0.0

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

    def _cali_free(self) -> bool:
        """Cali est au sol et fait quelque chose d'interruptible : il peut aller la voir."""
        pet = self.pet
        return pet.stand is None and pet.state in ("idle", "walk", "nap")

    def _meet_fx(self) -> float | None:
        """Où (bord gauche du sprite) Jazz s'arrête près de Cali, du côté d'où il vient ; None si c'est hors écran.
        Il se met plus près d'elle quand elle dort (couché, il est plus long)."""
        pet = self.pet
        chain = pet.floors[self.floor_idx]
        gap = LIE_GAP if pet.state == "nap" else TOUCH_GAP
        center = pet.cx - self._side * gap * self.S
        if not chain.cx0 + self.width_px * 0.25 <= center <= chain.cx1 - self.width_px * 0.25:
            return None
        return center - self.width_px / 2

    # ───────────────────────── cycle de vie d'une visite
    def start_visit(self) -> None:
        pet = self.pet
        self.S = int(pet.settings["scale"])
        self.setFixedSize(DOG_W * self.S, DOG_H * self.S)
        floor = pet.floors[min(pet.floor_idx, len(pet.floors) - 1)]
        self.floor_idx = floor.idx
        width = self.width_px
        if self.rng.random() < 0.5:                     # il vient de la gauche
            self._side, self.fx, self._exit_x, self._back_x = 1, floor.cx0 - width, floor.cx1, floor.cx0 - width
        else:
            self._side, self.fx, self._exit_x, self._back_x = -1, floor.cx1, floor.cx0 - width, floor.cx1
        self.dir = self._side
        self.fy = floor.y
        span = abs(self._exit_x - self.fx)
        self._sit_x = self.fx + self.dir * span * self.rng.uniform(0.3, 0.7) \
            if self.rng.random() < SIT_CHANCE else None
        chance = JOIN_CHANCE if pet.state == "nap" else GREET_CHANCE
        self._approach = self.rng.random() < chance and self._cali_free() and self._meet_fx() is not None
        self.t, self.frame, self._frame_t, self._happy = 0.0, 0, 0.0, False
        self._escort = 0.0
        self._called = False
        self._bark_in = self.voice.uniform(*BARK_FIRST_S)
        if self._bubble is not None:
            self._bubble.set_scale(self.S)
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
        self._approach = False
        self._escort = 0.0
        self._hush()
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
        elif self.state == "greet":
            self._step_greet(dt)
        elif self.state == "lie":
            self._step_lie(dt)
        else:
            self._step_walk(dt)
        if self.state != "away":
            self._follow_floor(dt)
            self._place()
            self._tick_voice(dt)
            self.update()

    def closeEvent(self, event) -> None:
        if self._bubble is not None:
            self._bubble.close()
        super().closeEvent(event)

    # ───────────────────────── voix
    @property
    def bubble(self) -> Bubble:
        if self._bubble is None:
            self._bubble = Bubble(self.S or 4)
            self._bubble.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            self._bubble.setWindowFlag(Qt.WindowType.WindowTransparentForInput, True)
        return self._bubble

    def windows(self) -> tuple:
        """Ses fenêtres déjà créées en dehors de la sienne (sa bulle, si elle existe)."""
        return (self._bubble,) if self._bubble is not None else ()

    def _center_x(self) -> float:
        return self.fx + self.width_px / 2

    def _say(self, kind: str, ms: float = BARK_MS) -> None:
        if not self.pet.settings["meows"]:
            return
        self.bubble.set_scale(self.S or 4)
        self.bubble.show_html(pick_bark(self.voice, kind))
        self._bubble_until = self.t + ms
        self._place_bubble()

    def _hush(self) -> None:
        self._bubble_until = 0.0
        if self._bubble is not None:
            self._bubble.hide()

    def _cali_is_talking_nearby(self) -> bool:
        return self.pet._temp and abs(self._center_x() - self.pet.cx) < QUIET_NEAR_PX * self.S / 4

    def _tick_voice(self, dt: float) -> None:
        """Aboiements spontanés en chemin, durée de la bulle et position au-dessus de sa tête."""
        if self._bubble is not None and self._bubble.isVisible() and self.t >= self._bubble_until:
            self._bubble.hide()
        if self.state in ("walk", "sit"):
            self._bark_in -= dt
            if self._bark_in <= 0:
                self._bark_in = self.voice.uniform(*BARK_EVERY_S)
                if self.voice.random() < BARK_CHANCE and not self._cali_is_talking_nearby():
                    scream = self.voice.random() < SCREAM_CHANCE
                    self._say("scream" if scream else "pass", SCREAM_MS if scream else BARK_MS)
        self._place_bubble()

    def _place_bubble(self) -> None:
        bubble = self._bubble
        if bubble is None or not bubble.isVisible():
            return
        left, top, right, _bottom = self.pet.work
        head = self._center_x() + (0.22 if self.dir > 0 else -0.22) * self.width_px
        x = min(max(head - bubble.width() / 2, left), max(left, right - bubble.width()))
        bubble.set_tail_x(head - x)
        bubble.move(round(x), round(max(top, self.y() - bubble.height() - 2)))

    def _animate_walk(self, dt: float) -> None:
        self._frame_t += dt
        if self._frame_t > FRAME_S:
            self._frame_t = 0.0
            self.frame ^= 1

    def _step_walk(self, dt: float) -> None:
        if self._escort > 0:
            self._escort_step(dt)
        speed = self.pet.speed * ESCORT_SPEED if self._escort > 0 else DOG_SPEED * self.S / 4
        stride = speed * dt
        if self._approach:
            meet = self._meet_fx() if self._cali_free() else None
            if meet is None:                            # Cali est partie, ou trop près du bord : il passera son chemin
                self._approach = False
                self.dir = self._side
            else:
                self._animate_walk(dt)
                self.dir = 1 if meet > self.fx else -1
                if not self._called and abs(meet - self.fx) < SPOT_PX * self.S / 4:
                    self._called = True                 # il l'a repérée : cri de Toller
                    self._say("scream", SCREAM_MS)
                if abs(meet - self.fx) <= stride:
                    self.fx = meet
                    if self.pet.state == "nap":
                        self._begin_join()
                    else:
                        self._begin_greet()
                else:
                    self.fx += self.dir * stride
                return
        self.fx += self.dir * stride
        self._animate_walk(dt)
        if self._sit_x is not None and self.dir * (self.fx - self._sit_x) >= 0:
            self._sit_x = None
            self.state, self.timer = "sit", self.rng.uniform(*SIT_S)
            self._happy = self.rng.random() < 0.5
        elif self.dir * (self.fx - self._exit_x) >= 0:
            self._end(self.rng.uniform(*BETWEEN_VISITS_S))

    # ───────────────────────── tête-à-tête avec Cali
    def _begin_greet(self) -> None:
        self._approach = False
        self._sit_x = None
        self.state, self.timer = "greet", self.rng.uniform(*GREET_S)
        self._heart_in = self.timer / 2
        self._happy = True
        self._hush()                                    # à elle de répondre
        center = self.fx + self.width_px / 2
        self.pet.companion.jazz_arrived(1 if center > self.pet.cx else -1)

    def _step_greet(self, dt: float) -> None:
        pet = self.pet
        if pet.stand is not None or pet.state != "idle":    # on l'a portée, un cadeau est arrivé, elle a sauté...
            self._leave()
            return
        pet.timer = max(pet.timer, 1.0)                     # elle reste là tant qu'il est là
        self.timer -= dt
        self._heart_in -= dt
        if self._heart_in <= 0 < self._heart_in + dt:
            pet.fx_particle("heart")
            if not pet._temp:
                self._say("greet")
        if self.timer <= 0:
            self._leave(friendly=True)

    def _begin_join(self) -> None:
        """Cali dort : il se couche contre elle, la tête tournée vers la sienne, sans la réveiller."""
        pet = self.pet
        self._approach = False
        self._sit_x = None
        self.state, self.timer = "lie", JOIN_MAX_S
        self.dir = self._side
        self._happy = False
        pet.timer = max(pet.timer, self.rng.uniform(*JOIN_S))     # sa sieste dure au moins un moment
        self._hush()
        self._say("lie", BARK_MS)
        center = self.fx + self.width_px / 2
        pet.companion.jazz_lies_down(1 if center > pet.cx else -1)

    def _step_lie(self, dt: float) -> None:
        pet = self.pet
        self.timer -= dt
        if pet.stand is not None or pet.state != "nap" or self.timer <= 0:    # elle se réveille (ou on la dérange)
            self._leave(friendly=pet.stand is None and pet.state == "idle")

    def _leave(self, friendly: bool = False) -> None:
        """Il repart par où il est venu. `friendly` : fin normale du tête-à-tête (Cali peut alors le suivre)."""
        self._escort = self.rng.uniform(*FOLLOW_S) if friendly and self.rng.random() < FOLLOW_CHANCE else 0.0
        self._hush()
        self.state = "walk"
        self.dir = -self._side
        self._exit_x = self._back_x
        self._happy = False

    def _escort_step(self, dt: float) -> None:
        """Cali trottine derrière Jazz, à distance constante ; elle arrête dès qu'elle a autre chose à faire."""
        pet = self.pet
        surface = pet._current_surface() if pet.stand is None else None
        if surface is None or pet.state not in ("idle", "walk"):    # sautée, portée, au travail, cadeau...
            self._escort = 0.0
            return
        _y, x0, x1 = surface
        x0, x1 = pet._clip(x0, x1)
        margin = pet.CW * 0.25
        target = self.fx + self.width_px / 2 + self._side * TOUCH_GAP * self.S      # juste derrière lui
        if not x0 + margin <= target <= x1 - margin:                # elle est au bout du sol : elle le regarde partir
            self._escort = 0.0
            return
        self._escort -= dt
        if pet.state == "idle":
            pet.timer = max(pet.timer, 1.0)                         # pas d'idée soudaine tant qu'elle le suit
        if pet.state == "walk" or abs(target - pet.cx) > FOLLOW_START_PX:
            pet._walk_to(target)

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
        seated = self.state in ("sit", "greet")
        pose = "lie" if self.state == "lie" else "sit" if seated else "walk"
        p = QPainter(self)
        draw_dog(p, self.S, pose=pose, frame=0 if pose != "walk" else self.frame,
                 flip=self.dir < 0, t=self.t, blink=self.t % BLINK_EVERY_MS < BLINK_MS,
                 happy=seated and self._happy)
        p.end()
