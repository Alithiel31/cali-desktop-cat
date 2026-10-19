"""Sauvegarde locale (un fichier JSON) : rien ne quitte le PC.

Trois protections contre la perte de progression :
- un fichier illisible est mis de côté sous un nom horodaté (les 3 dernières copies sont gardées) ;
- une copie quotidienne est faite au premier lancement du jour (les 7 dernières sont gardées, dossier `backups/`),
  et sert à restaurer automatiquement si le fichier principal est illisible ;
- un numéro de version et des migrations permettent de faire évoluer le format sans casser les anciennes sauvegardes.
"""
from __future__ import annotations

import copy
import glob
import json
import logging
import os
import shutil
import sys
import time
from datetime import date, datetime

log = logging.getLogger("desktopcat.store")

SCHEMA_VERSION = 2


def _v1_vers_v2(d: dict) -> dict:
    """v2 : « gift_pending » (oui/non) devient « gifts_pending » (nombre). Avec un simple oui/non, le cadeau d'une
    session de concentration finie pendant qu'un cadeau ordinaire attendait était perdu."""
    d["gifts_pending"] = 1 if d.pop("gift_pending", False) is True else 0
    return d


# Migrations : {version de départ: fonction(dict brut) -> dict brut à la version suivante}.
# Pour passer à la version N+1 : SCHEMA_VERSION = N+1 et MIGRATIONS[N] = fonction.
MIGRATIONS: dict = {1: _v1_vers_v2}
KEEP_CORRUPT = 3        # copies de fichiers illisibles conservées
KEEP_DAILY = 7          # copies quotidiennes conservées
MAX_PENDING_GIFTS = 99  # cadeaux en attente au plus (un fichier modifié à la main ne fait pas exploser le compteur)
REPLACE_RETRIES = 3     # un antivirus ou un outil de synchronisation peut verrouiller le fichier un instant

DEFAULTS = {
    "version": SCHEMA_VERSION,
    "name": "Miso",
    "fur": "ecaille",
    "hats": {},                 # {id_chapeau: quantité}
    "equipped": None,
    "fish": 0,                  # croquettes gagnées en vendant des doublons et en finissant des sessions
    "mood": 50,                 # humeur du chat, de 0 (affamé) à 100 (repu) : voir game.py
    "gift_progress": 0,         # secondes d'activité depuis le dernier cadeau
    "gifts_pending": 0,         # cadeaux gagnés pas encore ouverts
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
        "track_apps": True,             # note le nom de l'exécutable actif pour les statistiques
        "hunt_cursor": True,            # guette la souris immobile et bondit dessus
        "focus_breaks": True,           # pause après chaque session de concentration réussie
        "break_min": 5,                 # durée de cette pause
        "hotkey": True,                 # Ctrl+Alt+C affiche ou cache le chat
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
    d["mood"] = min(100, _nat(d.get("mood"), DEFAULTS["mood"]))
    d["gift_progress"] = _nat(d.get("gift_progress"))
    d["gifts_pending"] = min(MAX_PENDING_GIFTS, _nat(d.get("gifts_pending")))
    days = d.get("days")
    d["days"] = {k: _clean_day(v) for k, v in days.items() if isinstance(k, str)} if isinstance(days, dict) else {}
    f = d.get("focus")
    ok = isinstance(f, dict) and _num(f.get("ends_at")) and _num(f.get("total_min")) and 1 <= f["total_min"] <= 180
    d["focus"] = {"ends_at": float(f["ends_at"]), "total_min": int(f["total_min"])} if ok else None
    if ok and "active" in f:                       # secondes de présence réelle (ajouté après la 1re version)
        d["focus"]["active"] = _nat(f["active"])
    return d


def _today() -> str:
    return date.today().isoformat()


def _stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def write_json_atomic(path: str, obj) -> None:
    """Écrit `obj` en JSON sans jamais laisser de fichier à moitié écrit, même après une coupure de courant.

    On écrit dans `<path>.tmp`, on force l'écriture sur le disque (`fsync` : sinon Windows peut renommer un fichier
    dont le contenu n'est pas encore écrit, et on retrouve une sauvegarde vide au redémarrage), puis on remplace
    l'ancien fichier. Le remplacement est retenté quelques fois : un antivirus peut verrouiller le fichier un instant.
    Lève OSError si tout échoue."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    for attempt in range(REPLACE_RETRIES):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if attempt == REPLACE_RETRIES - 1:
                raise
            time.sleep(0.05 * (attempt + 1))


def default_path() -> str:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return os.path.join(base, "DesktopCat", "save.json")


class Store:
    def __init__(self, path: str | None = None):
        self.path = path or default_path()
        self._backup_day: str | None = None          # jour de la dernière copie quotidienne
        self.data = copy.deepcopy(DEFAULTS)
        self.load()

    # ───────── lecture / écriture
    @property
    def backup_dir(self) -> str:
        return os.path.join(os.path.dirname(self.path), "backups")

    @staticmethod
    def _read(path: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            saved = json.load(f)
        if not isinstance(saved, dict):
            raise ValueError("la sauvegarde n'est pas un objet JSON")
        return saved

    def load(self) -> None:
        self.recovered_from: str | None = None       # copie quotidienne restaurée, le cas échéant
        try:
            saved = self._read(self.path)
        except FileNotFoundError:
            return
        except (OSError, ValueError):
            log.warning("Sauvegarde illisible : %s", self.path, exc_info=True)
            self._set_aside()
            self._recover_from_daily_backup()
            return
        version = self._version_of(saved)
        if version != SCHEMA_VERSION:
            # Ancien format (on va migrer) ou format d'une version plus récente de l'appli (on va peut-être
            # perdre des champs inconnus) : dans les deux cas, on garde le fichier tel quel avant d'y toucher.
            self._keep_copy(f".v{version}.bak")
            if version > SCHEMA_VERSION:
                log.warning("La sauvegarde est au format v%s, plus récent que cette appli (v%s)", version, SCHEMA_VERSION)
        self._daily_backup()
        self._apply(self._upgrade(saved))

    @staticmethod
    def _version_of(saved: dict) -> int:
        v = saved.get("version")
        return v if isinstance(v, int) and not isinstance(v, bool) and v >= 1 else 1

    def _upgrade(self, saved: dict) -> dict:
        """Applique les migrations une à une, de la version du fichier jusqu'à la version courante."""
        version = self._version_of(saved)
        while version < SCHEMA_VERSION:
            step = MIGRATIONS.get(version)
            try:
                if step is None:
                    raise LookupError(f"aucune migration depuis la version {version}")
                saved = step(copy.deepcopy(saved))
            except Exception:
                log.error("Migration v%s -> v%s impossible : la sauvegarde est chargée telle quelle", version,
                          version + 1, exc_info=True)
                return saved
            version += 1
            saved["version"] = version
            log.info("Sauvegarde migrée en v%s", version)
        return saved

    def _apply(self, saved: dict) -> None:
        merged = copy.deepcopy(DEFAULTS)
        for key, value in saved.items():
            if key == "settings" and isinstance(value, dict):
                for k, v in value.items():
                    if k in DEFAULTS["settings"] and type(v) is type(DEFAULTS["settings"][k]):
                        merged["settings"][k] = v
            elif key in DEFAULTS and key != "version":
                merged[key] = value
        self.data = _sanitize(merged)
        self.data["version"] = SCHEMA_VERSION            # ce qu'on a en mémoire est au format courant

    # ───────── copies de sécurité
    def _keep_copy(self, suffix: str) -> None:
        """Copie le fichier actuel vers `<fichier><suffix>`, sans écraser une copie déjà faite."""
        dest = self.path + suffix
        try:
            if not os.path.exists(dest):
                shutil.copy2(self.path, dest)
        except OSError:
            log.warning("Impossible de copier la sauvegarde vers %s", dest, exc_info=True)

    def _set_aside(self) -> None:
        """Met le fichier illisible de côté sous un nom horodaté, et ne garde que les plus récents."""
        dest = f"{self.path}.{_stamp()}.bak"
        try:
            os.replace(self.path, dest)
            log.warning("Sauvegarde illisible mise de côté : %s", dest)
        except OSError:
            log.warning("Impossible de mettre la sauvegarde de côté", exc_info=True)
            return
        for old in sorted(glob.glob(self.path + ".????-??-??_??-??-??.bak"))[:-KEEP_CORRUPT]:
            try:
                os.remove(old)
            except OSError:
                log.warning("Impossible de supprimer l'ancienne copie %s", old, exc_info=True)

    def _daily_backups(self) -> list:
        return sorted(glob.glob(os.path.join(self.backup_dir, "save-????-??-??.json")))

    def _daily_backup(self) -> None:
        """Au premier lancement du jour, copie la sauvegarde telle qu'elle était à la fin de la veille."""
        self._backup_day = _today()
        dest = os.path.join(self.backup_dir, f"save-{self._backup_day}.json")
        try:
            os.makedirs(self.backup_dir, exist_ok=True)
            if not os.path.exists(dest):
                shutil.copy2(self.path, dest)
            for old in self._daily_backups()[:-KEEP_DAILY]:
                os.remove(old)
        except OSError:
            log.warning("Copie quotidienne impossible", exc_info=True)

    def _recover_from_daily_backup(self) -> None:
        for path in reversed(self._daily_backups()):
            try:
                saved = self._read(path)
            except (OSError, ValueError):
                log.warning("Copie quotidienne inutilisable : %s", path)
                continue
            self._apply(self._upgrade(saved))
            self.recovered_from = path
            log.warning("Sauvegarde restaurée depuis la copie du jour : %s", path)
            return
        log.warning("Aucune copie quotidienne utilisable : on repart d'une sauvegarde neuve")

    def save(self) -> bool:
        self.data["version"] = SCHEMA_VERSION
        if self._backup_day != _today() and os.path.exists(self.path):
            # L'appli peut tourner des jours sans redémarrer (PC mis en veille) : la copie quotidienne se fait aussi
            # au premier enregistrement de chaque nouveau jour, avant d'écraser l'état de la veille.
            self._daily_backup()
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            write_json_atomic(self.path, self.data)
            return True
        except OSError as e:
            log.error("Sauvegarde impossible : %s", e)
            return False

    # ───────── statistiques
    def clear_stats(self) -> int:
        """Efface toutes les statistiques (temps, concentration, cadeaux, applis), y compris dans les copies de
        sécurité lisibles. Renvoie le nombre de copies nettoyées. Une copie illisible (fichier abîmé mis de côté)
        ne peut pas être nettoyée : elle est laissée telle quelle, comme toute copie qu'on n'arrive pas à réécrire."""
        self.data["days"] = {}
        self.save()
        copies = self._daily_backups() + glob.glob(self.path + ".*.bak")
        cleaned = 0
        for path in copies:
            try:
                saved = self._read(path)
                if not saved.get("days"):
                    continue
                saved["days"] = {}
                write_json_atomic(path, saved)
                cleaned += 1
            except (OSError, ValueError):
                log.warning("Copie non nettoyée (illisible ou inaccessible) : %s", path)
        log.info("Statistiques effacées (%d copie(s) de sécurité nettoyée(s))", cleaned)
        return cleaned

    def day(self, key: str | None = None) -> dict:
        key = key or _today()
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
