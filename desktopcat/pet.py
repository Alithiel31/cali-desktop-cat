"""Le chat : fenêtre transparente déplacée par Python, avec sa petite vie.

Modèle physique : le chat a une position (fx, fy) où fx = bord gauche de son sprite et fy = ordonnée de ses
pieds. Il se tient sur une « surface » : le sol d'un écran, ou le bord haut d'une fenêtre. Tout est en pixels
logiques de Qt ; les rectangles Windows (physiques) sont convertis écran par écran (voir screens.py).
Plusieurs écrans : un sol par écran. Des écrans collés dont les bas se touchent presque forment une « chaîne »
que le chat traverse en marchant ; sinon il saute ou tombe de l'un à l'autre.

États : idle, walk, nap, sleep (utilisateur absent), work (session de concentration), wait (cadeau posé),
        stalk (guette la souris), drag (porté à la souris), fall (chute libre), jump (saut vers une autre surface).
"""
from __future__ import annotations

import random
import time

from PySide6.QtCore import QRect, Qt, QTimer, Signal
from PySide6.QtGui import QCursor, QGuiApplication, QPainter
from PySide6.QtWidgets import QWidget

from . import hunt, winapi
from .dog import Dog
from .motion import Jump, advance_fall, advance_jump, advance_walk, make_jump
from .pet_companion import PetCompanion
from .pet_input import PetInput
from .pet_layout import compute_placement
from .phrases import meow_delay, pick_meow
from .screens import (
    ScreenInfo,
    bounds,
    build_floors,
    clip_to_bounds,
    floor_here,
    native_rects,
    nearest_rect_index,
    snap_to_floor,
)
from .sprite import FOOT_ROW, GRID_H, GRID_W, draw_cat
from .surfaces import Surface
from .world import build_surfaces, floor_surfaces, window_geometry

BASE_SPEED = 95.0         # px/s pour une échelle de 4
CARRY_SLACK_PX = 3        # écart toléré (arrondis d'affichage) avant de conclure que la personne a bougé la souris
LOOP_MS = 16              # boucle normale : ~60 images/s
LOOP_SLOW_MS = 100        # chat caché, ou endormi parce que l'utilisateur est absent : 10 passages/s suffisent


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def qt_screens() -> list:
    """Les écrans vus par Qt, l'écran principal en premier."""
    primary = QGuiApplication.primaryScreen()
    screens = sorted(QGuiApplication.screens(), key=lambda s: s is not primary)
    out = []
    for s in screens:
        g, a = s.geometry(), s.availableGeometry()
        out.append(ScreenInfo((g.left(), g.top(), g.left() + g.width(), g.top() + g.height()),
                              (a.left(), a.top(), a.left() + a.width(), a.top() + a.height()),
                              s.devicePixelRatio() or 1.0))
    return out


class Pet(QWidget):
    open_panel = Signal()
    quit_app = Signal()
    start_focus = Signal(int)
    stop_focus = Signal()

    def __init__(self, game, bubble, gift, fx, rng=None, screens=None, dog_rng=None):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
                         | Qt.WindowType.Tool | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.game, self.bubble, self.gift, self.fxl = game, bubble, gift, fx
        self.rng = rng or random.Random()

        self.t = 0.0                         # temps de simulation en ms
        self.S = 0
        self._screens_fn = screens or qt_screens
        self.floor_idx = 0                   # sol (= écran) sur lequel il marche quand `stand` est None
        self._apply_scale()
        self._refresh_screen()

        # position et mouvement
        w0 = self.works[0]
        self.fx = self.rng.uniform(w0[0] + 100, max(w0[0] + 101, w0[2] - 100 - self.CW))
        self.fy = self.floors[0].y
        self.vy = 0.0
        self.dir = 1
        self.stand: int | None = None        # hwnd de la fenêtre sur laquelle il se tient, None = sol
        self.stand_left = 0.0
        self.surfaces: list[Surface] = self._floor_surfaces()
        self._scan_acc = 1.0
        self._follow_acc = 0.0
        self._last_fg = None

        # état
        self.state = "idle"
        self.timer = 1.0
        self.target = 0.0
        self.then = None
        self.frame = 0
        self._frame_t = 0.0
        self.jump: Jump | None = None
        self.sys_sleep = False

        # chasse au curseur (aucun tirage au hasard ici : la suite des tirages reste celle des tests existants)
        self._cursor_last = None             # dernière position vue de la souris
        self._cursor_moved_at: float | None = None   # ms ; None tant que la souris n'a jamais bougé
        self._hunt_cool = 20_000.0           # pas de chasse avant (ms)
        self._stalk_since = 0.0
        self.hunt_x = 0.0
        self._pounce = False                 # le saut en cours est un bond sur la souris
        self._carry_at: tuple | None = None  # position où elle tient la souris ; None si elle ne l'emporte pas
        self.hidden = False
        self.user_hidden = False
        self._fullscreen = False
        self.gift_visible = False

        # expressions
        self.blink_until = 0.0
        self.next_blink = 2500.0
        self.happy_until = 0.0
        self.surprised_until = 0.0
        self.next_z = 0.0
        self.next_meow = meow_delay(self.rng)

        # bulle
        self._temp = False
        self._temp_until = 0.0
        self._focus_text = ""

        self._press = None
        self.input = PetInput(self)
        self._pet_timer = QTimer(self)       # un clic simple attend de savoir si c'est un double-clic
        self._pet_timer.setSingleShot(True)
        self._pet_timer.timeout.connect(self._pet)
        self.companion = PetCompanion(self)
        self.dog = Dog(self, dog_rng)        # Jazz : son propre hasard, pour ne pas toucher à celui du chat
        self._place(force=True)
        self.show()

        game.sleeping_changed.connect(self._on_sleeping)
        game.fullscreen_changed.connect(self._on_fullscreen)
        game.focus_changed.connect(self._on_focus)
        game.focus_finished.connect(self._on_focus_finished)
        game.break_finished.connect(self.companion.break_finished)
        game.fed.connect(self.companion.fed)
        game.changed.connect(self._on_changed)
        gift.clicked.connect(self._on_gift_clicked)
        game.jazz_requested.connect(self.dog.call_now)

        self._last = time.perf_counter()
        self.loop = QTimer(self)
        self.loop.setTimerType(Qt.TimerType.PreciseTimer)
        self.loop.timeout.connect(self._on_loop)
        self.loop.start(LOOP_MS)
        self.anim = QTimer(self)
        self.anim.timeout.connect(self.update)
        self.anim.start(80)

    # ───────────────────────── paramètres et écran
    @property
    def settings(self) -> dict:
        return self.game.settings

    def _apply_scale(self) -> None:
        s = int(self.game.settings["scale"])
        if s == self.S:
            return
        self.S = s
        self.CW = GRID_W * s
        self.FOOT = FOOT_ROW * s
        self.setFixedSize(GRID_W * s, GRID_H * s)
        self.gift.set_scale(s)
        self.bubble.set_scale(s)

    def _refresh_screen(self) -> None:
        """Relit les écrans (branchés, débranchés, déplacés, barre des tâches changée...)."""
        screens = list(self._screens_fn()) or [ScreenInfo((0, 0, 1920, 1080), (0, 0, 1920, 1040))]
        self.screens = screens
        self._screens_sig = self._signature(screens)
        self.works = [s.work for s in screens]
        self.floors = build_floors(self.works)
        self.bounds = bounds(self.works)
        self.floor_idx = min(self.floor_idx, len(self.floors) - 1)
        self.game.set_monitors(native_rects(screens))
        b = self.bounds
        self.fx_area = QRect(int(b[0]), int(b[1]), int(b[2] - b[0]), int(b[3] - b[1]))
        self.fxl.set_areas([QRect(round(g[0]), round(g[1]), round(g[2] - g[0]), round(g[3] - g[1]))
                            for g in (sc.geom for sc in screens)])

    @staticmethod
    def _signature(screens) -> tuple:
        return tuple((s.geom, s.work, s.dpr) for s in screens)

    def _check_screens(self) -> None:
        """Appelée régulièrement : si la configuration des écrans a changé, on s'y adapte."""
        screens = list(self._screens_fn())
        if screens and self._signature(screens) != self._screens_sig:
            self._refresh_screen()
            if self.stand is None and self.state not in ("drag", "fall", "jump"):
                self._snap_to_floor()
            if self.state == "work" and self.game.focus:
                self._go_work()                       # l'écran a changé : il se replace pour rester entièrement visible
            self._update_hidden()

    def _snap_to_floor(self) -> None:
        """Ramène le chat sur le sol le plus proche (un écran vient de disparaître sous ses pieds)."""
        self.floor_idx, self.fx, self.fy = snap_to_floor(self.floors, self.cx, self.fy, self.CW)

    @property
    def work(self) -> tuple:
        """Zone utile de l'écran où se trouve le chat."""
        return self.works[nearest_rect_index(self.works, self.cx, self.fy - self.FOOT / 2)]

    @property
    def floor_y(self) -> float:
        return self.floors[self.floor_idx].y

    def _screen_index(self) -> int:
        return nearest_rect_index(self.works, self.cx, self.fy - self.FOOT / 2)

    def _floor_surfaces(self) -> list:
        return floor_surfaces(self.floors)

    def _floor_here(self):
        """Le sol sous ses pieds : celui de l'écran courant, ou son voisin de la même chaîne s'il l'a traversé."""
        self.floor_idx = floor_here(self.floors, self.cx, self.floor_idx)
        return self.floors[self.floor_idx]

    def _clip(self, x0: float, x1: float) -> tuple:
        """Partie d'un segment qui reste sur un écran (une fenêtre peut dépasser du bureau)."""
        return clip_to_bounds(x0, x1, self.bounds)

    @property
    def speed(self) -> float:
        return BASE_SPEED * self.S / 4

    def _own_hwnds(self):
        out = []
        for w in (self, self.bubble, self.gift, self.dog, *self.fxl.windows()):
            if w.isVisible():
                out.append(int(w.winId()))
        return out

    # ───────────────────────── boucle
    def _on_loop(self) -> None:
        now = time.perf_counter()
        dt = min(now - self._last, 2.5 * self.loop.interval() / 1000)     # plafond : un gel ne fait pas un bond
        self._last = now
        self.step(dt)
        self.dog.step(dt)
        self._adapt_loop()

    def loop_interval(self) -> int:
        """Rythme de la boucle voulu dans l'état actuel. Endormi (utilisateur absent), le chat ne fait que respirer :
        inutile de le recalculer 60 fois par seconde. La sieste (« nap ») garde le rythme normal : l'utilisateur
        est là et peut déplacer la fenêtre sous le chat."""
        return LOOP_SLOW_MS if self.hidden or self.state == "sleep" else LOOP_MS

    def _adapt_loop(self) -> None:
        want = self.loop_interval()
        if self.loop.interval() != want:
            self.loop.setInterval(want)

    def step(self, dt: float) -> None:
        """Avance la simulation de dt secondes (appelée par la minuterie, ou directement dans les tests)."""
        self.t += dt * 1000
        if self.hidden:
            return
        self._scan_acc += dt
        if self._scan_acc >= 0.2:
            self._scan_acc = 0.0
            self._check_screens()
            self._refresh_surfaces()
            if self._compute_hidden() != self.hidden:        # le chat a changé d'écran, ou l'appli plein écran aussi
                self._update_hidden()
                if self.hidden:
                    return

        st = self.state
        if st == "drag":
            pass
        elif st == "fall":
            self._step_fall(dt)
        elif st == "jump":
            self._step_jump(dt)
        else:
            self._step_stand(dt)

        self._step_misc(dt)
        self._place()

    # ───────────────────────── surfaces
    def _refresh_surfaces(self) -> None:
        self.surfaces = build_surfaces(self.screens, self.works, self.floors, self.settings["perch_windows"],
                                       self._own_hwnds(), self.FOOT, self.CW)

    def _window_geometry(self, hwnd):
        """(y du bord haut, gauche, droite) de la fenêtre telle qu'elle est MAINTENANT, ou None si elle a disparu."""
        return window_geometry(hwnd, self.screens, self.settings["perch_windows"])

    def _current_surface(self):
        """(y, x0, x1) de la surface sous ses pieds, ou None si elle a disparu."""
        if self.stand is None:
            f = self._floor_here()
            return (f.y, f.cx0, f.cx1)
        return self._window_geometry(self.stand)

    @property
    def cx(self) -> float:
        return self.fx + self.CW / 2

    # ───────────────────────── états « au sol »
    def _idle(self, sec=None) -> None:
        self.state = "idle"
        self.timer = sec if sec is not None else self.rng.uniform(2, 6)

    def _nap(self) -> None:
        self.state = "nap"
        self.timer = self.rng.uniform(15, 35)

    def _walk_to(self, target_cx: float, then=None) -> None:
        self.state = "walk"
        self.target = target_cx
        self.then = then
        if abs(target_cx - self.cx) > 1:
            self.dir = 1 if target_cx > self.cx else -1

    def _go_work(self) -> None:
        surf = self._current_surface()
        if surf is None:
            return
        _y, x0, x1 = surf
        x0, x1 = self._clip(x0, x1)
        # Au travail, tout le sprite doit être visible : l'ordinateur occupe son côté droit (ou gauche s'il est
        # retourné). Pour marcher, le chat peut déborder un peu (marges transparentes) ; pas ici.
        m = self.CW / 2 + self.S
        target = x1 - m if x1 - x0 >= 2 * m else (x0 + x1) / 2        # surface trop étroite : au milieu
        self._walk_to(target, then="work")

    def _step_stand(self, dt: float) -> None:
        surf = self._current_surface()
        if surf is None:
            self._start_fall()
            return
        y, x0, x1 = surf
        if self.stand is not None:
            self.fx += x0 - self.stand_left          # la fenêtre a bougé : le chat suit
            self.stand_left = x0
            if y > self.fy + 14:                     # elle s'est dérobée vers le bas : il tombe
                self._start_fall()
                return
            self.fy = y
        elif abs(y - self.fy) > 0.01:                # marche d'un écran à l'autre, ou barre des tâches déplacée
            self.fy += _clamp(y - self.fy, -420 * dt, 420 * dt)
        if self.cx < x0 - 2 or self.cx > x1 + 2:     # la fenêtre a glissé sous lui
            self._start_fall()
            return

        st = self.state
        if st == "idle":
            self.timer -= dt
            if self.timer <= 0:
                self._decide()
        elif st == "walk":
            self._step_walk(dt, x0, x1)
        elif st == "nap":
            self.timer -= dt
            if self.timer <= 0:
                self._idle(1.0)
        elif st == "stalk":
            self._step_stalk(dt, y, x0, x1)

    # ───────────────────────── chasse au curseur
    def _track_cursor(self) -> None:
        pos = QCursor.pos()
        p = (pos.x(), pos.y())
        if self._carry_at is not None:
            self._step_carry(p)
            return
        if p != self._cursor_last:
            if self._cursor_last is not None:
                self._cursor_moved_at = self.t
            self._cursor_last = p

    def _try_hunt(self, x0: float, x1: float) -> bool:
        """Commence l'affût si la souris vient de s'arrêter à sa portée."""
        if not self.settings["hunt_cursor"] or self.t < self._hunt_cool or self.sys_sleep or self.game.focus:
            return False
        moved = None if self._cursor_moved_at is None else self._cursor_moved_at / 1000
        if not hunt.cursor_is_resting(self.t / 1000, moved):
            return False
        pos = QCursor.pos()
        if not hunt.cursor_in_reach(pos.x(), pos.y(), self.cx, self.fy, x0, x1, self.CW, self.FOOT, self.S):
            return False
        self.state = "stalk"
        self.timer = self.rng.uniform(*hunt.STALK_S)
        self.hunt_x = float(pos.x())
        self._stalk_since = self.t
        self.dir = 1 if self.hunt_x > self.cx else -1
        return True

    def _paws(self) -> tuple:
        """Où elle tient la souris : devant ses pattes."""
        return round(self.cx + self.dir * self.CW * 0.3), round(self.fy - self.FOOT * 0.12)

    def _start_carry(self) -> None:
        """Le bond vient de réussir : elle garde la souris sous ses pattes."""
        if not (self.settings["carry_cursor"] and self.settings["hunt_cursor"]) or self.sys_sleep or self.game.focus:
            return
        self._carry_at = (-10**6, -10**6)               # remplacée aussitôt par la vraie position
        self._move_cursor(self._paws())

    def _move_cursor(self, target: tuple) -> None:
        QCursor.setPos(*target)
        pos = QCursor.pos()                              # Windows arrondit (échelle d'affichage) : on lit le résultat
        self._carry_at = (pos.x(), pos.y())
        self._cursor_last = self._carry_at

    def _step_carry(self, seen: tuple) -> None:
        """Elle emmène la souris partout où elle va, tant que la personne ne la rebouge pas."""
        ax, ay = self._carry_at
        user_moved = abs(seen[0] - ax) > CARRY_SLACK_PX or abs(seen[1] - ay) > CARRY_SLACK_PX
        if user_moved or self.state == "drag" or self.sys_sleep or self.game.focus or self.hidden \
                or not self.settings["carry_cursor"]:
            self._release_cursor(seen)
        elif self._paws() != (ax, ay):
            self._move_cursor(self._paws())

    def _release_cursor(self, seen: tuple) -> None:
        self._carry_at = None
        self._cursor_last = seen
        self._cursor_moved_at = self.t
        # pas de nouvelle chasse tout de suite
        self._hunt_cool = max(self._hunt_cool, self.t + hunt.COOLDOWN_S[0] * 1000)
        if self.state in ("idle", "walk"):
            self.surprised_until = self.t + 400

    def _step_stalk(self, dt: float, y: float, x0: float, x1: float) -> None:
        if self._cursor_moved_at is not None and self._cursor_moved_at > self._stalk_since:
            self.surprised_until = self.t + 500                # la proie s'est enfuie
            self._hunt_cool = self.t + hunt.ESCAPED_COOLDOWN_S * 1000
            self._idle(1.5)
            return
        self.timer -= dt
        if self.timer > 0:
            return
        cx0, cx1 = self._clip(x0, x1)
        m = self.CW * 0.25
        land = _clamp(self.hunt_x, cx0 + m, cx1 - m)
        if self.stand is None:
            dest = Surface(None, y, x0, x1, x0, "sol", floor=self.floor_idx)
        else:
            dest = Surface(self.stand, y, x0, x1, self.stand_left, "fenêtre")
        self._hunt_cool = self.t + self.rng.uniform(*hunt.COOLDOWN_S) * 1000
        self._begin_jump(dest, land)
        self._pounce = True

    def _step_walk(self, dt: float, x0: float, x1: float) -> None:
        x0, x1 = self._clip(x0, x1)
        old_cx = self.cx
        new_cx, self._frame_t, self.frame, direction, arrived = advance_walk(
            old_cx, self.target, x0, x1, self.CW, self.speed, dt, self._frame_t, self.frame)
        self.fx += new_cx - old_cx
        if arrived:
            then, self.then = self.then, None
            if then == "work" and self.game.focus:
                self.state = "work"
            else:
                self._idle()
        else:
            self.dir = direction

    def _decide(self) -> None:
        r = self.rng.random()
        surf = self._current_surface()
        if surf is None:
            return
        _y, x0, x1 = surf
        x0, x1 = self._clip(x0, x1)
        if self._try_hunt(x0, x1):
            return
        m = self.CW * 0.25
        lo, hi = x0 + m, x1 - m
        can_walk = hi - lo > 20
        if r < 0.40 and can_walk:
            self._walk_to(self.rng.uniform(lo, hi))
        elif r < 0.50:
            self._idle() if self._carry_at is not None else self._nap()    # elle ne s'endort pas sur la souris
        elif r < 0.62 and can_walk:                              # curieux : va voir la souris
            self._walk_to(_clamp(QCursor.pos().x(), lo, hi))
        elif r < 0.80 and self.settings["jump_between_windows"]:
            if not self._jump_somewhere():
                self._idle()
        else:
            self._idle()

    # ───────────────────────── sauts
    def _candidates(self, reach_up: float):
        m = self.CW * 0.25
        scale = self.S / 4
        out = []
        here = self.floors[self.floor_idx].chain
        for s in self.surfaces:
            on_same_surface = (s.hwnd == self.stand) if s.hwnd is not None else \
                (self.stand is None and self.floors[s.floor].chain == here)
            if on_same_surface or s.x1 - s.x0 < self.CW * 0.9:
                continue
            if self.fy - s.y > reach_up * scale:
                continue
            land = _clamp(self.cx + self.rng.uniform(-350, 350) * scale, s.x0 + m, s.x1 - m)
            if abs(land - self.cx) > 750 * scale:
                continue
            out.append((s, land))
        return out

    def _jump_somewhere(self, prefer_hwnd=None, reach_up: float = 260) -> bool:
        cands = self._candidates(reach_up)
        if not cands:
            return False
        fg = winapi.foreground() if prefer_hwnd is None else None
        want = prefer_hwnd if prefer_hwnd is not None else (fg.hwnd if fg else None)
        preferred = [c for c in cands if want is not None and c[0].hwnd == want]
        pick = self.rng.choice(preferred) if preferred and (prefer_hwnd is not None or self.rng.random() < 0.6) \
            else self.rng.choice(cands)
        self._begin_jump(*pick)
        return True

    def _begin_jump(self, dest: Surface, land_cx: float) -> None:
        self.jump = make_jump(self.fx, self.fy, land_cx, dest.y, self.CW, self.S, dest)
        self.dir = 1 if land_cx >= self.cx else -1
        self.stand = None
        self.state = "jump"
        self.then = None

    def _step_jump(self, dt: float) -> None:
        jump = self.jump
        self.fx, self.fy, arrived = advance_jump(jump, dt)
        if arrived:
            dest, self.jump = jump.dest, None
            self._land(dest, soft=True)

    # ───────────────────────── chute et atterrissage
    def _start_fall(self) -> None:
        self._pounce = False
        if self.state != "fall":
            self.state = "fall"
            self.vy = 0.0
            self.surprised_until = self.t + 600
        self.stand = None
        self.jump = None
        self._refresh_surfaces()                     # sinon il se rattrape sur une surface périmée
        self._scan_acc = 0.0

    def _step_fall(self, dt: float) -> None:
        center_x = self.cx
        center_x, self.fy, self.vy, landing = advance_fall(
            center_x, self.fy, self.vy, dt, self.surfaces, self.floors)
        self.fx += center_x - self.cx
        if landing is not None:
            self._land(landing)

    def _land(self, s: Surface, soft: bool = False) -> None:
        if s.hwnd is not None:
            # La surface date du dernier scan (jusqu'à 0,2 s) ou du début du saut : la fenêtre a pu bouger depuis.
            # Se poser sur son ancienne position téléporterait le chat quand il se mettrait à la suivre.
            geo = self._window_geometry(s.hwnd)
            if geo is None or abs(geo[0] - s.y) > 14 or not (geo[1] - 2 <= self.cx <= geo[2] + 2):
                self._start_fall()
                return
            s = Surface(s.hwnd, geo[0], s.x0, s.x1, geo[1], s.title)
        self.fy = s.y
        self.vy = 0.0
        self.stand = s.hwnd
        if s.hwnd is None:
            self.floor_idx = s.floor
        self.stand_left = s.wleft
        if not soft:
            self.surprised_until = self.t + 400
        if self._pounce:
            self._pounce = False
            self.companion.caught()
            self._start_carry()
        if self.sys_sleep:
            self.state = "sleep"
        elif self.game.focus:
            self._go_work()
        else:
            self._idle(self.rng.uniform(0.6, 2.0))

    # ───────────────────────── suivi de la fenêtre active, cadeaux, bulle
    def _step_misc(self, dt: float) -> None:
        self._track_cursor()
        if self.t > self.next_blink:
            self.blink_until = self.t + 140
            self.next_blink = self.t + self.rng.uniform(2200, 5200)

        if self.state in ("nap", "sleep") and self.t > self.next_z:
            self.next_z = self.t + 1600
            self.fx_particle("zzz")

        self._follow_acc += dt
        if self._follow_acc >= 0.5:
            self._follow_acc = 0.0
            self._follow_active()

        data = self.game.data
        # `_temp` : on laisse finir la bulle en cours (celle du chapeau qu'on vient d'ouvrir, quand un 2e cadeau attend)
        if data["gifts_pending"] and not self.gift_visible and not self.sys_sleep and not self._temp \
                and self.state in ("idle", "walk", "nap"):
            self._show_gift()

        if self.t >= self.next_meow and self.settings["meows"]:
            self._try_meow()

        self._bubble_tick()

    def _try_meow(self) -> None:
        self.companion.try_meow()

    def _follow_active(self) -> None:
        if not self.settings["follow_active"]:
            return
        fg = winapi.foreground()
        hwnd = fg.hwnd if fg else None
        changed = hwnd != self._last_fg
        self._last_fg = hwnd
        if not changed or hwnd is None or hwnd == self.stand or self.state not in ("idle", "walk", "nap"):
            return
        if any(s.hwnd == hwnd for s in self.surfaces):
            self._jump_somewhere(prefer_hwnd=hwnd, reach_up=600)

    def _show_gift(self) -> None:
        self.companion.show_gift()

    def say(self, html: str, ms: float = 3500, border: str = "#2a1d18") -> None:
        self.companion.say(html, ms, border)

    def _bubble_tick(self) -> None:
        self.companion.bubble_tick()

    def fx_particle(self, kind: str) -> None:
        self.companion.spawn_particle(kind)

    # ───────────────────────── réactions aux événements du jeu
    def _on_gift_clicked(self) -> None:
        self.companion.gift_clicked()

    def _on_sleeping(self, asleep: bool) -> None:
        self.companion.sleeping_changed(asleep)

    def _on_fullscreen(self, full: bool) -> None:
        self._fullscreen = full
        self._update_hidden()

    def set_user_hidden(self, hide: bool) -> None:
        self.user_hidden = hide
        self._update_hidden()

    def _compute_hidden(self) -> bool:
        """Caché si l'utilisateur l'a demandé, ou si une appli plein écran occupe SON écran
        (le chat reste visible sur un autre écran)."""
        if self.user_hidden:
            return True
        if not self._fullscreen:
            return False
        mon = self.game.fullscreen_monitor
        return mon is None or mon == self._screen_index()

    def _update_hidden(self) -> None:
        self.hidden = self._compute_hidden()
        if self.hidden:
            self.hide()
            self.dog.cancel()
            self.bubble.hide()
            self.gift.hide()
            self.fxl.clear()
        else:
            self.show()
            if self.gift_visible:
                self.gift.show()
        self._adapt_loop()

    def _on_focus(self, f) -> None:
        self.companion.focus_changed(f)

    def _on_focus_finished(self, total: int) -> None:
        self.companion.focus_finished(total)

    def _on_changed(self) -> None:
        self._apply_scale()
        self.update()

    def force_gift(self) -> None:
        self.game.force_gift()

    # ───────────────────────── souris : caresser, porter, menu
    def mousePressEvent(self, e) -> None:
        self.input.press(e)

    def mouseMoveEvent(self, e) -> None:
        self.input.move(e)

    def mouseReleaseEvent(self, e) -> None:
        self.input.release(e)

    def mouseDoubleClickEvent(self, e) -> None:
        self.input.double_click()

    def _pet(self) -> None:
        if self.sys_sleep:
            return
        self.game.petted()
        self.happy_until = self.t + 2200
        if not self._temp and self.settings["meows"] and self.rng.random() < 0.5:
            self.say(pick_meow(self.rng, "petted"), 2000)
        for i in range(3):
            QTimer.singleShot(i * 220, lambda: self.fx_particle("heart"))
        if self.state == "nap":
            self._idle(2.0)

    # ───────────────────────── rendu et placement
    def paintEvent(self, event) -> None:
        st = self.state
        pose = "sleep" if st in ("nap", "sleep") else "walk" if st in ("walk", "jump") else \
            "work" if st == "work" else "sit"
        d = self.game.data
        p = QPainter(self)
        draw_cat(p, self.S, pose=pose, frame=self.frame if st == "walk" else 0, flip=self.dir < 0,
                 fur=d["fur"], hat=d["equipped"], t=self.t,
                 blink=self.t < self.blink_until, happy=self.t < self.happy_until and pose != "sleep",
                 surprised=st in ("drag", "fall", "stalk") or self.t < self.surprised_until)
        p.end()

    def _place(self, force: bool = False) -> None:
        gift_size = (self.gift.width(), self.gift.height()) if self.gift_visible else None
        bubble_size = (self.bubble.width(), self.bubble.height()) if self.bubble.isVisible() else None
        placement = compute_placement(self.fx, self.fy, self.FOOT, self.CW, self.dir, self.work,
                                      gift_size, bubble_size, self.S, GRID_W)
        x, y = placement.pet
        if force or (x, y) != (self.x(), self.y()):
            self.move(x, y)
        if placement.gift is not None:
            self.gift.move(*placement.gift)
        if placement.bubble is not None:
            self.bubble.set_tail_x(placement.bubble_tail_x)  # la pointe vise la tête, même si la bulle est décalée
            self.bubble.move(*placement.bubble)
