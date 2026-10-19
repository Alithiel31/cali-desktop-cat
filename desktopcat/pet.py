"""Le chat : fenêtre transparente déplacée par Python, avec sa petite vie.

Modèle physique : le chat a une position (fx, fy) où fx = bord gauche de son sprite et fy = ordonnée de ses
pieds. Il se tient sur une « surface » : le sol d'un écran, ou le bord haut d'une fenêtre. Tout est en pixels
logiques de Qt ; les rectangles Windows (physiques) sont convertis écran par écran (voir screens.py).
Plusieurs écrans : un sol par écran. Des écrans collés dont les bas se touchent presque forment une « chaîne »
que le chat traverse en marchant ; sinon il saute ou tombe de l'un à l'autre.

États : idle, walk, nap, sleep (utilisateur absent), work (session de concentration), wait (cadeau posé),
        drag (porté à la souris), fall (chute libre), jump (saut vers une autre surface).
"""
from __future__ import annotations

import math
import random
import time

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QColor, QCursor, QGuiApplication, QPainter
from PySide6.QtCore import QRect
from PySide6.QtWidgets import QApplication, QMenu, QWidget

from . import winapi
from .motion import Jump, advance_fall, advance_jump, advance_walk, make_jump
from .phrases import meow_delay, pick_meow
from .screens import (ScreenInfo, bounds, build_floors, clamp_point, native_rects, nearest_floor,
                      nearest_rect_index)
from .sprite import FOOT_ROW, GRID_H, GRID_W, draw_cat
from .surfaces import Surface
from .world import build_surfaces, floor_surfaces, window_geometry

BASE_SPEED = 95.0         # px/s pour une échelle de 4
STANDING = ("idle", "walk", "nap", "wait", "work", "sleep")
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

    def __init__(self, game, bubble, gift, fx, rng=None, screens=None):
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
        self._pet_timer = QTimer(self)       # un clic simple attend de savoir si c'est un double-clic
        self._pet_timer.setSingleShot(True)
        self._pet_timer.timeout.connect(self._pet)
        self._place(force=True)
        self.show()

        game.sleeping_changed.connect(self._on_sleeping)
        game.fullscreen_changed.connect(self._on_fullscreen)
        game.focus_changed.connect(self._on_focus)
        game.focus_finished.connect(self._on_focus_finished)
        game.changed.connect(self._on_changed)
        gift.clicked.connect(self._on_gift_clicked)

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
        i = nearest_floor(self.floors, self.cx, self.fy)
        f = self.floors[i]
        self.floor_idx = i
        self.fx = _clamp(self.cx, f.x0, f.x1) - self.CW / 2
        self.fy = f.y

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
        cur = self.floors[self.floor_idx]
        if cur.x0 <= self.cx <= cur.x1:
            return cur
        for f in self.floors:
            if f.chain == cur.chain and f.x0 <= self.cx <= f.x1:
                self.floor_idx = f.idx
                return f
        return cur

    def _clip(self, x0: float, x1: float) -> tuple:
        """Partie d'un segment qui reste sur un écran (une fenêtre peut dépasser du bureau)."""
        return max(x0, self.bounds[0]), min(x1, self.bounds[2])

    @property
    def speed(self) -> float:
        return BASE_SPEED * self.S / 4

    def _own_hwnds(self):
        out = []
        for w in (self, self.bubble, self.gift, *self.fxl.windows()):
            if w.isVisible():
                out.append(int(w.winId()))
        return out

    # ───────────────────────── boucle
    def _on_loop(self) -> None:
        now = time.perf_counter()
        dt = min(now - self._last, 2.5 * self.loop.interval() / 1000)     # plafond : un gel ne fait pas un bond
        self._last = now
        self.step(dt)
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
        m = self.CW * 0.25
        lo, hi = x0 + m, x1 - m
        can_walk = hi - lo > 20
        if r < 0.40 and can_walk:
            self._walk_to(self.rng.uniform(lo, hi))
        elif r < 0.50:
            self._nap()
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
        if self.sys_sleep:
            self.state = "sleep"
        elif self.game.focus:
            self._go_work()
        else:
            self._idle(self.rng.uniform(0.6, 2.0))

    # ───────────────────────── suivi de la fenêtre active, cadeaux, bulle
    def _step_misc(self, dt: float) -> None:
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
        if data["gift_pending"] and not self.gift_visible and not self.sys_sleep \
                and self.state in ("idle", "walk", "nap"):
            self._show_gift()

        if self.t >= self.next_meow and self.settings["meows"]:
            self._try_meow()

        self._bubble_tick()

    def _try_meow(self) -> None:
        """Un miaulement spontané dans une bulle, seulement s'il ne dérange rien."""
        free = (self.state in ("idle", "walk", "work") and not self._temp and not self.gift_visible
                and not self.sys_sleep and self._press is None)
        if not free:
            self.next_meow = self.t + 4000          # on réessaie bientôt
            return
        self.say(pick_meow(self.rng, "work" if self.state == "work" else "idle"), 2200)
        if self.rng.random() < 0.3:
            self.fx_particle("heart")
        self.next_meow = self.t + meow_delay(self.rng)

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
        self.state = "wait"
        self.gift_visible = True
        self.gift.show()
        self.say("Miaou ! J'ai un cadeau pour toi 🎁", 6000)

    def say(self, html: str, ms: float = 3500, border: str = "#2a1d18") -> None:
        self._temp = True
        self._temp_until = self.t + ms
        self._focus_text = ""
        self.bubble.show_html(html, border)

    def _bubble_tick(self) -> None:
        if self._temp and self.t > self._temp_until:
            self._temp = False
            self.bubble.hide()
        if self._temp:
            return
        f = self.game.focus
        if f:
            left = max(0, math.ceil(f["ends_at"] - self.game.clock()))
            text = f"⏱ {left // 60:02d}:{left % 60:02d}"
            if text != self._focus_text:
                self._focus_text = text
                self.bubble.show_html(text)
        elif self.bubble.isVisible():
            self.bubble.hide()
            self._focus_text = ""

    def fx_particle(self, kind: str) -> None:
        head_x = self.fx + self.CW * (0.62 if self.dir > 0 else 0.38)
        self.fxl.spawn(kind, head_x + self.rng.uniform(-12, 12), self.fy - self.FOOT * 0.85)

    # ───────────────────────── réactions aux événements du jeu
    def _on_gift_clicked(self) -> None:
        res = self.game.claim_gift()
        self.gift_visible = False
        self.gift.hide()
        if self.state == "wait":
            self._idle(3.0)
        if not res:
            return
        hat, rar = res["hat"], res["rarity"]
        self.happy_until = self.t + 3500
        head = ("Nouveau chapeau : " + hat.name) if res["is_new"] else f"{hat.name} (doublon ×{res['count']})"
        label_color = QColor(rar["color"]).darker(150).name()        # le gris/jaune clair d'une rareté se lit mal sur le crème
        self.say(f"{head} — <b style='color:{label_color}'>{rar['label']}</b>", 6500, rar["color"])
        for i in range(5):
            QTimer.singleShot(i * 150, lambda: self.fx_particle("star"))

    def _on_sleeping(self, asleep: bool) -> None:
        self.sys_sleep = asleep
        if asleep:
            if self.state in STANDING:
                self.state = "sleep"
        elif self.state == "sleep":
            self._idle(1.0)
            self.happy_until = self.t + 2000
            self.say("Te revoilà !", 2500)
            self.fx_particle("heart")
        self._adapt_loop()

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
            self.bubble.hide()
            self.gift.hide()
            self.fxl.clear()
        else:
            self.show()
            if self.gift_visible:
                self.gift.show()
        self._adapt_loop()

    def _on_focus(self, f) -> None:
        if f:
            self.say("Au travail ! Je reste avec toi 🐾", 3500)
            if self.state in ("idle", "walk", "nap", "wait"):
                self._go_work()
        elif self.state == "work":
            self._idle(1.0)

    def _on_focus_finished(self, total: int) -> None:
        self.happy_until = self.t + 4000
        self.say("Bravo, session terminée !", 4000)
        for i in range(4):
            QTimer.singleShot(i * 200, lambda: self.fx_particle("heart"))

    def _on_changed(self) -> None:
        self._apply_scale()
        self.update()

    def force_gift(self) -> None:
        self.game.force_gift()

    # ───────────────────────── souris : caresser, porter, menu
    def mousePressEvent(self, e) -> None:
        g = e.globalPosition().toPoint()
        if e.button() == Qt.MouseButton.LeftButton:
            self._press = {"g": g, "moved": False, "off": (e.position().x(), e.position().y())}
        elif e.button() == Qt.MouseButton.RightButton:
            self._menu(g)

    def mouseMoveEvent(self, e) -> None:
        p = self._press
        if not p:
            return
        g = e.globalPosition().toPoint()
        if not p["moved"] and math.hypot(g.x() - p["g"].x(), g.y() - p["g"].y()) > 5:
            p["moved"] = True
            self.state = "drag"
            self.stand, self.jump, self.vy = None, None, 0.0
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        if p["moved"]:
            nx = g.x() - p["off"][0]
            ny = g.y() - p["off"][1]
            if abs(nx - self.fx) > 1:
                self.dir = 1 if nx > self.fx else -1
            # on le garde sur un écran : le point (centre, pieds) est ramené dans la zone utile la plus proche
            zones = [(w[0], w[1] + self.FOOT, w[2], w[3]) for w in self.works]
            cx, fy = clamp_point(zones, nx + self.CW / 2, ny + self.FOOT)
            self.fx, self.fy = cx - self.CW / 2, fy

    def mouseReleaseEvent(self, e) -> None:
        p, self._press = self._press, None
        if not p or e.button() != Qt.MouseButton.LeftButton:
            return
        if p["moved"]:
            self.unsetCursor()
            self.state = "fall"
            self.vy = 0.0
        else:
            self._pet_timer.start(min(400, QApplication.doubleClickInterval()))

    def mouseDoubleClickEvent(self, e) -> None:
        self._pet_timer.stop()                       # c'était un double-clic : pas de caresse
        self.open_panel.emit()

    def _pet(self) -> None:
        if self.sys_sleep:
            return
        self.happy_until = self.t + 2200
        if not self._temp and self.settings["meows"] and self.rng.random() < 0.5:
            self.say(pick_meow(self.rng, "petted"), 2000)
        for i in range(3):
            QTimer.singleShot(i * 220, lambda: self.fx_particle("heart"))
        if self.state == "nap":
            self._idle(2.0)

    def _menu(self, pos) -> None:
        menu = QMenu()
        menu.addAction("Ouvrir le panneau", self.open_panel.emit)
        if self.game.focus:
            menu.addAction("Arrêter la concentration", self.stop_focus.emit)
        else:
            menu.addAction("Concentration 25 min", lambda: self.start_focus.emit(25))
        menu.addSeparator()
        menu.addAction("Quitter", self.quit_app.emit)
        menu.exec(pos)

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
                 surprised=st in ("drag", "fall") or self.t < self.surprised_until)
        p.end()

    def _place(self, force: bool = False) -> None:
        x, y = round(self.fx), round(self.fy - self.FOOT)
        if force or (x, y) != (self.x(), self.y()):
            self.move(x, y)

        w0, w1 = self.work[0], self.work[2]
        if self.gift_visible:
            gw = self.gift.width()
            gx = self.fx + 24 * self.S if self.dir > 0 else self.fx + (GRID_W - 24) * self.S - gw
            self.gift.move(round(_clamp(gx, w0, w1 - gw)), round(self.fy - self.gift.height() + self.S))
        if self.bubble.isVisible():
            bw, bh = self.bubble.width(), self.bubble.height()
            bx = _clamp(self.fx + self.CW / 2 - bw / 2, w0, max(w0, w1 - bw))
            by = max(self.work[1], self.fy - self.FOOT - bh - 4)
            head_x = self.fx + self.CW * (0.62 if self.dir > 0 else 0.38)
            self.bubble.set_tail_x(head_x - bx)          # la pointe vise la tête, même si la bulle est décalée
            self.bubble.move(round(bx), round(by))
