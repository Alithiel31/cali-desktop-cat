# Outils de développement

| Fichier | Rôle |
|---|---|
| `run_test_instance.bat` | Lance l'appli avec une sauvegarde temporaire isolée (miaous coupés) : la vraie sauvegarde n'est pas touchée. |
| `preview_panel.py` | Génère des captures du panneau dans `tools/out/` (sans écran, mode Qt `offscreen`). |
| `demo_backups.py` | Rejoue le scénario « sauvegarde abîmée » dans un dossier temporaire : mise de côté, copie quotidienne, restauration. |
| `spikes/` | Prototypes historiques qui ont servi à choisir la techno (fluidité, transparence, perchage). Conservés pour mémoire, **non maintenus**. |

`spike_pywebview.py` est la première piste (Python + pywebview) ; `spike_qt.py` est celle retenue (PySide6).
