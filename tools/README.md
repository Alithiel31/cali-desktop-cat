# Outils de développement

Français · [English](README.en.md)

| Fichier | Rôle |
|---|---|
| `run_test_instance.bat` | Lance l'appli avec une sauvegarde temporaire isolée (miaous coupés, 50 croquettes, chat affamé) : la vraie sauvegarde n'est pas touchée. Voir [docs/TEST-MANUEL.md](../docs/TEST-MANUEL.md). |
| `make_icon.py` | Régénère `assets/desktopcat.ico` (icône de l'exe) à partir du sprite du chat. À relancer si son dessin change. |
| `make_version_file.py` | Écrit les métadonnées Windows de l'exe (`build/version_info.txt`) à partir de `desktopcat.__version__`. Utilisé par le build, voir [docs/DISTRIBUTION.md](../docs/DISTRIBUTION.md). |
| `preview_panel.py` | Génère des captures du panneau dans `tools/out/` (sans écran, mode Qt `offscreen`). |
| `demo_backups.py` | Rejoue le scénario « sauvegarde abîmée » dans un dossier temporaire : mise de côté, copie quotidienne, restauration. |
| `spikes/` | Prototypes historiques qui ont servi à choisir la techno (fluidité, transparence, perchage). Conservés pour mémoire, **non maintenus**. |

`spike_pywebview.py` est la première piste (Python + pywebview) ; `spike_qt.py` est celle retenue (PySide6).
