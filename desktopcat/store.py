"""Sauvegarde locale (un fichier JSON) : rien ne quitte le PC."""
from __future__ import annotations

import copy
import json
import os
import sys
from datetime import date

DEFAULTS = {
    "version": 1,
    "name": "Miso",
    "fur": "ecaille",
    "hats": {},                 # {id_chapeau: quantité}
    "equipped": None,
    "fish": 0,                  # croquettes gagnées en vendant des doublons
    "gift_progress": 0,         # secondes d'activité depuis le dernier cadeau
    "gift_pending": False,
    "settings": {
        "gift_every_min": 20,
        "sleep_after_min": 5,
        "notifications": True,
        "launch_at_startup": False,
        "scale": 4,                     # taille d'un « pixel » du chat à l'écran (3 à 6)
        "perch_windows": True,          # marche sur le bord haut des fenêtres
        "jump_between_windows": True,   # saute d'une fenêtre à l'autre
        "follow_active": False,         # rejoint la fenêtre qu'on vient d'activer
        "meows": True,                  # bulles « miaou » spontanées
    },
    "focus": None,              # session de concentration en cours : {"ends_at": epoch, "total_min": n}
    "days": {},                 # {"2026-10-18": {"active": s, "focus": s, "gifts": n, "apps": {exe: s}}}
}

KEEP_DAYS = 60
KEEP_APPS_PER_DAY = 40


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v == v and abs(v) != float("inf")


def _nat(v, default: int = 0) -> int:
    """Entier >= 0, sinon la valeur par défaut."""
    return int(v) if _num(v) and v >= 0 else default


def _clean_day(raw) -> dict:
    raw = raw if isinstance(raw, dict) else {}
    apps = raw.get("apps")
    apps = {k: _nat(v) for k, v in apps.items() if isinstance(k, str) and _num(v) and v > 0} \
        if isinstance(apps, dict) else {}
    return {"active": _nat(raw.get("active")), "focus": _nat(raw.get("focus")),
            "gifts": _nat(raw.get("gifts")), "apps": apps}


def _sanitize(d: dict) -> dict:
    """Remet d'aplomb un fichier de sauvegarde abîmé ou modifié à la main : mieux vaut perdre un champ que planter."""
    name = d.get("name")
    d["name"] = name.strip()[:20] if isinstance(name, str) and name.strip() else DEFAULTS["name"]
    if not isinstance(d.get("fur"), str):
        d["fur"] = DEFAULTS["fur"]
    hats = d.get("hats")
    d["hats"] = {k: int(v) for k, v in hats.items() if isinstance(k, str) and _num(v) and v >= 1} \
        if isinstance(hats, dict) else {}
    if d.get("equipped") not in d["hats"]:
        d["equipped"] = None                      # un chapeau qu'on ne possède pas (ou plus) ne se porte pas
    d["fish"] = _nat(d.get("fish"))
    d["gift_progress"] = _nat(d.get("gift_progress"))
    d["gift_pending"] = d.get("gift_pending") is True
    days = d.get("days")
    d["days"] = {k: _clean_day(v) for k, v in days.items() if isinstance(k, str)} if isinstance(days, dict) else {}
    f = d.get("focus")
    ok = isinstance(f, dict) and _num(f.get("ends_at")) and _num(f.get("total_min")) and 1 <= f["total_min"] <= 180
    d["focus"] = {"ends_at": float(f["ends_at"]), "total_min": int(f["total_min"])} if ok else None
    return d


def default_path() -> str:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return os.path.join(base, "DesktopCat", "save.json")


class Store:
    def __init__(self, path: str | None = None):
        self.path = path or default_path()
        self.data = copy.deepcopy(DEFAULTS)
        self.load()

    # ───────── lecture / écriture
    def load(self) -> None:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                saved = json.load(f)
        except FileNotFoundError:
            return
        except (OSError, ValueError):
            # Fichier illisible : on le met de côté au lieu de l'écraser silencieusement.
            try:
                os.replace(self.path, self.path + ".bak")
            except OSError:
                pass
            return
        if not isinstance(saved, dict):
            return
        merged = copy.deepcopy(DEFAULTS)
        for key, value in saved.items():
            if key == "settings" and isinstance(value, dict):
                for k, v in value.items():
                    if k in DEFAULTS["settings"] and type(v) is type(DEFAULTS["settings"][k]):
                        merged["settings"][k] = v
            elif key in DEFAULTS and key != "version":
                merged[key] = value
        self.data = _sanitize(merged)

    def save(self) -> bool:
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False)
            os.replace(tmp, self.path)          # écriture atomique : pas de fichier à moitié écrit
            return True
        except OSError as e:
            print("Sauvegarde impossible :", e, file=sys.stderr)
            return False

    # ───────── statistiques
    def day(self, key: str | None = None) -> dict:
        key = key or date.today().isoformat()
        days = self.data["days"]
        if key not in days:
            days[key] = {"active": 0, "focus": 0, "gifts": 0, "apps": {}}
            for old in sorted(days)[:-KEEP_DAYS]:
                del days[old]
        d = days[key]
        d.setdefault("apps", {})
        return d

    def add_app_seconds(self, exe: str, seconds: int = 1) -> None:
        if not exe:
            return
        apps = self.day()["apps"]
        apps[exe] = apps.get(exe, 0) + seconds
        if len(apps) > KEEP_APPS_PER_DAY:
            for name, _ in sorted(apps.items(), key=lambda kv: kv[1])[: len(apps) - KEEP_APPS_PER_DAY]:
                del apps[name]
