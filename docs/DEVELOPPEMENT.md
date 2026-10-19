# Développement local

Français · [English](en/DEVELOPMENT.md)

[Retour au README](../README.md)

## Prérequis

- **Python 3.12 ou 3.13** (3.10 plante avec PySide6 6.12). Validé en CI sur ces deux versions.
- **Windows** pour exécuter l'appli réellement (`winapi.py` n'a de sens que là). Les tests, eux, tournent partout.
- Git. PyInstaller uniquement pour fabriquer l'exécutable.

## Installer et lancer

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

`requirements.txt` ne contient qu'une ligne : `PySide6-Essentials>=6.6,<7` (Qt sans les modules inutiles ici).

## Tests

```bash
python -m unittest discover -s tests -v
```

| Environnement | Détail |
|---|---|
| Windows | `set QT_QPA_PLATFORM=offscreen` si tu ne veux voir aucune fenêtre. |
| Linux | Bibliothèques système nécessaires : `libegl1 libgl1 libxkbcommon0 libdbus-1-3 libfontconfig1 libglib2.0-0`. |
| CI | `ci.yml` : Windows + Ubuntu 24.04 × Python 3.12 et 3.13. |

Description des fichiers de tests et de la garde « pas de vrais écrans » : [ARCHITECTURE.md](./ARCHITECTURE.md#tests).

## Tester à la main sans risquer sa sauvegarde

`tools\run_test_instance.bat` redéfinit `APPDATA` vers `%TEMP%\desktopcat_test`, y écrit une sauvegarde neuve
(miaous et notifications coupés) et lance l'appli. Ta vraie sauvegarde n'est pas touchée.
Détail des autres outils : [tools/README.md](../tools/README.md).

## Où l'appli écrit

| Quoi | Où |
|---|---|
| Sauvegarde, copies, journal | `%APPDATA%\DesktopCat\` (ailleurs : `$XDG_DATA_HOME` ou `~/.local/share`) |
| Verrou d'instance | `%TEMP%\desktopcat.lock` |
| Démarrage avec Windows | `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`, valeur `DesktopCat` |

Voir [TROUBLESHOOTING.md](./TROUBLESHOOTING.md#où-sont-les-fichiers-) pour le détail des fichiers.

## Variables d'environnement

L'appli n'a **aucune variable de configuration** propre. Celles qui comptent sont des variables du système :

| Variable | Effet |
|---|---|
| `APPDATA` | Dossier de la sauvegarde (redéfini par `run_test_instance.bat`). |
| `XDG_DATA_HOME` | Idem hors Windows. |
| `QT_QPA_PLATFORM` | `offscreen` pour les tests et `tools/preview_panel.py`. |

## Conventions

- Messages de commit : `type: description` (`fix:`, `feat:`, `docs:`, `ci:`, `test:`, `chore:`), en français.
- Documentation : chaque fichier a sa version anglaise (`docs/en/`, `README.en.md`) ; modifier l'un, c'est mettre l'autre à jour.
- Fins de ligne : LF pour `.py` et `.md`, CRLF pour `.bat` (voir `.gitattributes`).
- Le hasard et l'heure sont passés en paramètre dès que possible (cf. `phrases.py`) pour rester testables.
- Toute nouvelle logique pure va dans un module sans Qt ni Windows (comme `screens.py`, `surfaces.py`, `hats.py`) :
  c'est ce qui la rend testable partout.

## Ébauche — à compléter

- [ ] Linter / formateur (ruff) et typage progressif — prévu au niveau 3 de la [feuille de route](./ROADMAP.md).
- [ ] Hook de pré-commit ou pré-push qui rejoue les tests (équivalent du hook Husky de QcWeather).
- [ ] Mesure de couverture de tests.
- [ ] Procédure pour valider l'API Windows réelle et les échelles d'affichage mixtes (aujourd'hui : à la main, sur un vrai double écran).
