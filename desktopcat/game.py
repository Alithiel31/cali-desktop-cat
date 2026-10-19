"""Règles du jeu : cadeaux, chapeaux, concentration, temps d'écran. Aucune interface ici."""
from __future__ import annotations

import os
import time

from PySide6.QtCore import QObject, QTimer, Signal

from . import autostart, winapi
from .hats import BY_ID, RARITIES, roll_hat
from .store import Store

FURS = ("ecaille", "orange", "gris", "noir", "blanc")
SETTING_RULES = {
    "gift_every_min": lambda v: max(5, min(120, int(v))),
    "sleep_after_min": lambda v: max(1, min(60, int(v))),
    "scale": lambda v: max(3, min(6, int(v))),
    "notifications": bool,
    "launch_at_startup": bool,
    "perch_windows": bool,
    "jump_between_windows": bool,
    "follow_active": bool,
    "meows": bool,
    "track_apps": bool,
}
MIN_REWARD_MIN = 10         # en dessous, une session terminée ne rapporte rien (sinon : un cadeau par minute)
MIN_FOCUS_ACTIVITY = 0.5    # part minimale de la session passée devant l'ordinateur pour que la récompense compte
MAX_TICK_S = 5.0            # un « tick » ne compte jamais plus de 5 s (veille, gel de l'appli, minuterie en retard)


class Game(QObject):
    changed = Signal()                  # l'état sauvegardé a changé (panneau et chat se rafraîchissent)
    gift_ready = Signal()
    sleeping_changed = Signal(bool)     # l'utilisateur est parti / revenu
    fullscreen_changed = Signal(bool)   # un jeu ou une vidéo occupe tout l'écran
    focus_changed = Signal(object)      # dict {ends_at, total_min} ou None
    focus_finished = Signal(int)
    notice = Signal(str, str)           # (titre, message) pour une notification

    def __init__(self, store: Store, parent=None, clock=time.time, monitor_rects=None, mono=time.monotonic):
        super().__init__(parent)
        self.store = store
        self.clock = clock                  # heure murale : sert aux échéances (fin de session)
        self.mono = mono                    # horloge monotone : sert à mesurer le temps réellement écoulé
        self.monitor_rects = list(monitor_rects or [(0, 0, 1920, 1080)])   # pixels physiques, réglés par le chat
        self.focus: dict | None = None
        self.sleeping = False
        self.fullscreen = False
        self.fullscreen_monitor: int | None = None    # indice de l'écran couvert par une appli plein écran
        self._ticks = 0
        self._acc = 0.0                     # fraction de seconde pas encore comptée
        self._last_mono: float | None = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer)

    def start(self) -> None:
        self._restore_focus()
        self._last_mono = None
        self._timer.start(1000)

    def set_monitors(self, rects) -> None:
        self.monitor_rects = list(rects) or [(0, 0, 1920, 1080)]

    def _restore_focus(self) -> None:
        """Reprend une session interrompue par un redémarrage de l'appli, si elle n'est pas déjà finie.
        Une session finie pendant l'absence ne rapporte rien : rien ne prouve que l'utilisateur ait travaillé."""
        f = self.data.get("focus")
        if f and f["ends_at"] > self.clock():
            if "active" not in f:               # ancienne sauvegarde : on laisse le bénéfice du doute
                f["active"] = max(0, int(f["total_min"] * 60 - (f["ends_at"] - self.clock())))
            self.focus = f                      # même objet que dans la sauvegarde : il y reste à jour
            self.focus_changed.emit(self.focus)
            self.changed.emit()
        elif f:
            self.data["focus"] = None

    @property
    def data(self) -> dict:
        return self.store.data

    @property
    def settings(self) -> dict:
        return self.store.data["settings"]

    # ───────── environ une fois par seconde
    def _on_timer(self) -> None:
        """Mesure le temps réellement écoulé depuis le dernier passage (plafonné) et le transmet à `tick`."""
        now = self.mono()
        last, self._last_mono = self._last_mono, now
        dt = 1.0 if last is None else now - last
        self.tick(min(max(dt, 0.0), MAX_TICK_S))

    def tick(self, dt: float = 1.0) -> None:
        """Avance le jeu de `dt` secondes. Seules les secondes entières sont comptées, le reste est reporté."""
        self._acc += dt
        secs = int(self._acc + 1e-9)
        self._acc = max(0.0, self._acc - secs)
        s, d = self.settings, self.store.day()
        idle = winapi.idle_seconds()
        active = idle < 60
        fg = winapi.foreground()

        if active and secs:
            d["active"] += secs
            if not self.data["gift_pending"]:
                self.data["gift_progress"] += secs
            if s["track_apps"] and fg is not None and fg.pid != os.getpid():
                self.store.add_app_seconds(fg.exe or "", secs)

        if self.focus:
            if secs:
                d["focus"] += secs
                if active:
                    self.focus["active"] = self.focus.get("active", 0) + secs
            if self.clock() >= self.focus["ends_at"]:
                self.stop_focus(completed=True)

        if not self.sleeping and idle >= s["sleep_after_min"] * 60:
            self.sleeping = True
            self.sleeping_changed.emit(True)
        elif self.sleeping and idle < 5:
            self.sleeping = False
            self.sleeping_changed.emit(False)

        if not self.data["gift_pending"] and self.data["gift_progress"] >= s["gift_every_min"] * 60:
            self.data["gift_pending"] = True
            self.data["gift_progress"] = 0
            self.gift_ready.emit()
            self.changed.emit()

        mon = winapi.fullscreen_monitor(fg, self.monitor_rects)
        if mon != self.fullscreen_monitor:
            self.fullscreen_monitor = mon
            self.fullscreen = mon is not None
            self.fullscreen_changed.emit(self.fullscreen)       # aussi quand l'appli change d'écran

        self._ticks += 1
        if self._ticks % 30 == 0:
            self.store.save()

    # ───────── cadeaux et chapeaux
    def claim_gift(self):
        if not self.data["gift_pending"]:
            return None
        hat = roll_hat()
        hats = self.data["hats"]
        is_new = hat.id not in hats
        hats[hat.id] = hats.get(hat.id, 0) + 1
        self.data["gift_pending"] = False
        self.data["gift_progress"] = 0
        self.store.day()["gifts"] += 1
        if is_new:
            self.data["equipped"] = hat.id          # le chat porte tout de suite sa nouveauté
        self.store.save()
        self.changed.emit()
        return {"hat": hat, "is_new": is_new, "count": hats[hat.id], "rarity": RARITIES[hat.rarity]}

    def force_gift(self) -> None:
        """Pour tester : un cadeau tout de suite."""
        self.data["gift_pending"] = True
        self.gift_ready.emit()
        self.changed.emit()

    def equip(self, hat_id) -> bool:
        if hat_id is not None and not self.data["hats"].get(hat_id):
            return False
        self.data["equipped"] = hat_id
        self.store.save()
        self.changed.emit()
        return True

    def sell(self, hat_id: str) -> bool:
        hat = BY_ID.get(hat_id)
        if hat is None or self.data["hats"].get(hat_id, 0) < 2:      # on ne vend que les doublons
            return False
        self.data["hats"][hat_id] -= 1
        self.data["fish"] += RARITIES[hat.rarity]["sell"]
        self.store.save()
        self.changed.emit()
        return True

    # ───────── concentration
    def start_focus(self, minutes) -> None:
        m = max(1, min(180, int(minutes)))
        self.focus = {"ends_at": self.clock() + m * 60, "total_min": m, "active": 0}
        self.data["focus"] = self.focus                        # survit à un redémarrage de l'appli
        self.store.save()
        self.focus_changed.emit(self.focus)
        self.changed.emit()

    def stop_focus(self, completed: bool = False) -> None:
        if not self.focus:
            return
        total = self.focus["total_min"]
        present = self.focus.get("active", total * 60)         # secondes passées devant l'ordinateur
        self.focus = None
        self.data["focus"] = None
        self.focus_changed.emit(None)
        if completed and total < MIN_REWARD_MIN:
            self.notice.emit(f"{self.data['name']} est content",
                             f"Session de {total} min terminée. Pas de cadeau en dessous de {MIN_REWARD_MIN} min.")
            self.focus_finished.emit(total)
        elif completed and present < total * 60 * MIN_FOCUS_ACTIVITY:
            self.notice.emit(f"{self.data['name']} s'est ennuyé",
                             f"Session de {total} min terminée, mais tu étais surtout absent : pas de cadeau.")
        elif completed:
            self.data["fish"] += 10 + total
            self.data["gift_pending"] = True
            self.notice.emit(f"{self.data['name']} est fier de toi",
                             f"Session de {total} min terminée : un cadeau t'attend.")
            self.focus_finished.emit(total)
            self.gift_ready.emit()
        self.store.save()
        self.changed.emit()

    # ───────── réglages
    def set_name(self, name: str) -> None:
        self.data["name"] = (name or "").strip()[:20] or "Miso"
        self.store.save()
        self.changed.emit()

    def set_fur(self, fur: str) -> None:
        if fur in FURS:
            self.data["fur"] = fur
            self.store.save()
            self.changed.emit()

    def set_setting(self, key: str, value) -> bool:
        rule = SETTING_RULES.get(key)
        if rule is None:
            return False
        try:
            self.settings[key] = rule(value)
        except (TypeError, ValueError):
            return False
        if key == "launch_at_startup":
            if not autostart.set_enabled(self.settings[key]):
                self.settings[key] = not self.settings[key]
                return False
        self.store.save()
        self.changed.emit()
        return True

    def clear_stats(self) -> None:
        """Efface les statistiques (et leurs traces dans les copies de sécurité). Chapeaux et croquettes restent."""
        self.store.clear_stats()
        self.changed.emit()

    def save(self) -> None:
        self.store.save()
