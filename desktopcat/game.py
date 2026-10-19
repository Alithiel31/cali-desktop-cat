"""Règles du jeu : cadeaux, chapeaux, concentration, temps d'écran. Aucune interface ici."""
from __future__ import annotations

import os
import time
from datetime import date

from PySide6.QtCore import QObject, QTimer, Signal

from . import autostart, winapi
from .hats import BY_ID, RARITIES, roll_hat
from .store import MAX_PENDING_GIFTS, Store

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
    "hunt_cursor": bool,
    "focus_breaks": bool,
    "break_min": lambda v: max(1, min(30, int(v))),
    "hotkey": bool,
}
MIN_REWARD_MIN = 10         # en dessous, une session terminée ne rapporte rien (sinon : un cadeau par minute)
MIN_FOCUS_ACTIVITY = 0.5    # part minimale de la session passée devant l'ordinateur pour que la récompense compte
MAX_TICK_S = 5.0            # un « tick » ne compte jamais plus de 5 s (veille, gel de l'appli, minuterie en retard)

# Humeur (0 à 100) : elle baisse avec le temps passé devant l'ordinateur, les croquettes la remontent.
FEED_COST = 5               # croquettes par repas
FEED_GAIN = 25              # points d'humeur par repas
MOOD_FULL = 95              # au-dessus, il n'a plus faim : on ne gaspille pas de croquettes
MOOD_DECAY_S = 180          # 1 point perdu toutes les 3 min d'activité (de 100 à 0 en 5 h devant l'écran)
MOOD_HAPPY = 70             # repu : les cadeaux arrivent plus vite
MOOD_HUNGRY = 25            # affamé : il réclame
HAPPY_GIFT_BONUS = 0.25     # +25 % de progression vers le prochain cadeau quand il est repu
PET_MOOD_CAP = 60           # les caresses remontent l'humeur, mais pas au-delà : rien ne remplace un repas


class Game(QObject):
    changed = Signal()                  # l'état sauvegardé a changé (panneau et chat se rafraîchissent)
    gift_ready = Signal()
    sleeping_changed = Signal(bool)     # l'utilisateur est parti / revenu
    fullscreen_changed = Signal(bool)   # un jeu ou une vidéo occupe tout l'écran
    focus_changed = Signal(object)      # dict {ends_at, total_min} ou None
    focus_finished = Signal(int)
    break_changed = Signal(object)      # pause après une session : dict {ends_at, total_min} ou None
    break_finished = Signal()           # la pause est arrivée à son terme (pas quand on la passe)
    fed = Signal()                      # le chat vient de manger
    notice = Signal(str, str)           # (titre, message) pour une notification

    def __init__(self, store: Store, parent=None, clock=time.time, monitor_rects=None, mono=time.monotonic):
        super().__init__(parent)
        self.store = store
        self.clock = clock                  # heure murale : sert aux échéances (fin de session)
        self.mono = mono                    # horloge monotone : sert à mesurer le temps réellement écoulé
        self.monitor_rects = list(monitor_rects or [(0, 0, 1920, 1080)])   # pixels physiques, réglés par le chat
        self.focus: dict | None = None
        self.brk: dict | None = None        # pause en cours (non sauvegardée : un redémarrage l'oublie)
        self._mood_acc = 0                  # secondes d'activité pas encore retirées de l'humeur
        self._bonus_acc = 0.0               # fraction de seconde de bonus pas encore comptée
        self.sleeping = False
        self.fullscreen = False
        self.fullscreen_monitor: int | None = None    # indice de l'écran couvert par une appli plein écran
        self._ticks = 0
        self._acc = 0.0                     # fraction de seconde pas encore comptée
        self._last_mono: float | None = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer)

    def start(self) -> None:
        self.sync_autostart(refresh_path=True)
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
            if not self.data["gifts_pending"]:
                self.data["gift_progress"] += secs + self._gift_bonus(secs)
            self._mood_acc += secs
            if self._mood_acc >= MOOD_DECAY_S:
                lost, self._mood_acc = divmod(self._mood_acc, MOOD_DECAY_S)
                self.data["mood"] = max(0, self.data["mood"] - lost)
            if s["track_apps"] and fg is not None and fg.pid != os.getpid():
                self.store.add_app_seconds(fg.exe or "", secs)

        if self.focus:
            if secs:
                d["focus"] += secs
                if active:
                    self.focus["active"] = self.focus.get("active", 0) + secs
            if self.clock() >= self.focus["ends_at"]:
                self.stop_focus(completed=True)
        elif self.brk and self.clock() >= self.brk["ends_at"]:
            self.brk = None
            self.break_changed.emit(None)
            self.break_finished.emit()
            self.notice.emit("Pause terminée", f"{self.data['name']} est prêt pour la prochaine session.")

        if not self.sleeping and idle >= s["sleep_after_min"] * 60:
            self.sleeping = True
            self.sleeping_changed.emit(True)
        elif self.sleeping and idle < 5:
            self.sleeping = False
            self.sleeping_changed.emit(False)

        if not self.data["gifts_pending"] and self.data["gift_progress"] >= s["gift_every_min"] * 60:
            self._add_gift()
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

    # ───────── humeur et croquettes
    @property
    def mood(self) -> int:
        return self.data["mood"]

    def mood_level(self) -> str:
        """« affamé », « content » ou « repu »."""
        return "repu" if self.mood >= MOOD_HAPPY else "affamé" if self.mood < MOOD_HUNGRY else "content"

    def _gift_bonus(self, secs: int) -> int:
        if self.mood < MOOD_HAPPY:
            return 0
        self._bonus_acc += secs * HAPPY_GIFT_BONUS
        extra = int(self._bonus_acc)
        self._bonus_acc -= extra
        return extra

    def can_feed(self) -> bool:
        return self.data["fish"] >= FEED_COST and self.mood < MOOD_FULL

    def feed(self) -> bool:
        """Un repas : FEED_COST croquettes contre FEED_GAIN points d'humeur."""
        if not self.can_feed():
            return False
        self.data["fish"] -= FEED_COST
        self.data["mood"] = min(100, self.mood + FEED_GAIN)
        self.store.save()
        self.fed.emit()
        self.changed.emit()
        return True

    def petted(self) -> None:
        """Une caresse : +1 d'humeur, sans dépasser PET_MOOD_CAP."""
        if self.mood < PET_MOOD_CAP:
            self.data["mood"] += 1
            self.changed.emit()

    # ───────── cadeaux et chapeaux
    def _add_gift(self) -> None:
        self.data["gifts_pending"] = min(MAX_PENDING_GIFTS, self.data["gifts_pending"] + 1)

    def claim_gift(self):
        if not self.data["gifts_pending"]:
            return None
        hat = roll_hat(today=date.fromtimestamp(self.clock()))
        hats = self.data["hats"]
        is_new = hat.id not in hats
        hats[hat.id] = hats.get(hat.id, 0) + 1
        self.data["gifts_pending"] -= 1
        self.data["gift_progress"] = 0
        self.store.day()["gifts"] += 1
        if is_new:
            self.data["equipped"] = hat.id          # le chat porte tout de suite sa nouveauté
        self.store.save()
        self.changed.emit()
        return {"hat": hat, "is_new": is_new, "count": hats[hat.id], "rarity": RARITIES[hat.rarity]}

    def force_gift(self) -> None:
        """Pour tester : un cadeau tout de suite."""
        self._add_gift()
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
        self.skip_break()                                      # on reprend : la pause s'arrête
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
            self._add_gift()                                   # s'ajoute à un cadeau ordinaire déjà en attente
            pause = ""
            if self.settings["focus_breaks"]:
                self._start_break()                            # avant focus_finished : le chat annonce la pause
                pause = f" Pause de {self.brk['total_min']} min : lève-toi un peu !"
            self.notice.emit(f"{self.data['name']} est fier de toi",
                             f"Session de {total} min terminée : un cadeau t'attend.{pause}")
            self.focus_finished.emit(total)
            self.gift_ready.emit()
        self.store.save()
        self.changed.emit()

    # ───────── pause (méthode Pomodoro)
    def _start_break(self) -> None:
        m = self.settings["break_min"]
        self.brk = {"ends_at": self.clock() + m * 60, "total_min": m}
        self.break_changed.emit(self.brk)

    def skip_break(self) -> None:
        if self.brk:
            self.brk = None
            self.break_changed.emit(None)
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

    def sync_autostart(self, refresh_path: bool = False) -> None:
        """Aligne la case « Lancer avec Windows » sur le registre, qui fait foi (une désactivation dans le Gestionnaire
        des tâches ne passe pas par l'appli). Au démarrage, réécrit aussi le chemin de l'exe s'il a changé."""
        actual = autostart.is_enabled()
        if actual is None:                              # hors Windows, ou registre illisible : on ne touche à rien
            return
        if actual and refresh_path:
            autostart.refresh_path()
        if actual != self.settings["launch_at_startup"]:
            self.settings["launch_at_startup"] = actual
            self.store.save()
            self.changed.emit()

    def clear_stats(self) -> None:
        """Efface les statistiques (et leurs traces dans les copies de sécurité). Chapeaux et croquettes restent."""
        self.store.clear_stats()
        self.changed.emit()

    def save(self) -> None:
        self.store.save()
