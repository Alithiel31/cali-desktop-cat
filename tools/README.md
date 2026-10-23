# Outils de développement

Français · [English](README.en.md)

| Fichier | Rôle |
|---|---|
| `run_test_instance.bat` | Lance l'appli avec une sauvegarde temporaire isolée (miaous coupés, 50 croquettes, chat affamé) : la vraie sauvegarde n'est pas touchée. Voir [docs/TEST-MANUEL.md](../docs/TEST-MANUEL.md). |
| `make_icon.py` | Régénère `assets/desktopcat.ico` (icône de l'exe) à partir du sprite du chat. À relancer si son dessin change. |
| `make_version_file.py` | Écrit les métadonnées Windows de l'exe (`build/version_info.txt`) à partir de `desktopcat.__version__`. Utilisé par le build, voir [docs/DISTRIBUTION.md](../docs/DISTRIBUTION.md). |
| `preview_panel.py` | Génère des captures du panneau dans `tools/out/` (sans écran, mode Qt `offscreen`). |
| `preview_jazz.py` | Génère `tools/out/jazz_preview.png` : Jazz (assis, content, au trot, couché) à côté de Cali, pour vérifier son dessin (sans écran, mode Qt `offscreen`). |
| `demo_backups.py` | Rejoue le scénario « sauvegarde abîmée » dans un dossier temporaire : mise de côté, copie quotidienne, restauration. |

Les prototypes historiques (`spike_pywebview.py`, première piste Python + pywebview ; `spike_qt.py`, celle retenue,
PySide6) sont rangés dans [`archive/spikes/`](../archive/spikes/), non maintenus, gardés pour mémoire.
