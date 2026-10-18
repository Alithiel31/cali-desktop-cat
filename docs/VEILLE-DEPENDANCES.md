# Veille des dépendances

[Retour au README](../README.md)

Desktop Cat n'appelle **aucune API externe** (voir [SECURITY.md](../SECURITY.md)). Ce qu'il faut surveiller, ce sont
ses dépendances techniques, qui peuvent casser le rendu ou le packaging sans préavis.

## Ce qu'il faut surveiller

| Dépendance | Usage | Où regarder | Détecté automatiquement ? |
|---|---|---|---|
| [PySide6](https://pypi.org/project/PySide6-Essentials/) (Qt 6) | Toute l'interface, fenêtres transparentes, multi-écrans | [Notes de version Qt for Python](https://doc.qt.io/qtforpython-6/), PyPI | Partiellement : la CI échoue si un test casse (Dependabot `pip`) |
| Python | Interpréteur | [Calendrier des versions](https://devguide.python.org/versions/) | CI sur 3.12 et 3.13 |
| [PyInstaller](https://pyinstaller.org) | Exécutable `DesktopCat.exe` | Notes de version, faux positifs antivirus | Build à blanc sur PR (`release.yml`) |
| API Windows (`user32`, `dwmapi`, `kernel32`) | Fenêtres, fenêtre active, inactivité, plein écran (`winapi.py`) | Évolutions de Windows 11 | ❌ Aucun test automatique : validation manuelle |
| Actions GitHub (`checkout`, `setup-python`, `upload-artifact`...) | CI/CD | Dependabot `github-actions` | ✅ PR hebdomadaire |
| Runners (`windows-latest`, `ubuntu-24.04`) | CI/CD | [Images GitHub](https://github.com/actions/runner-images) | Partiellement |

## Incidents déjà rencontrés

- **Python 3.10 + PySide6 6.12** : plantage. La CI est passée à 3.12 et 3.13, Ubuntu 24.04 épinglé
  (commit `e94e859`).

## À chaque vérification

- [ ] Les PR Dependabot ouvertes sont relues et mergées (ou fermées avec une raison, dans un commentaire de `dependabot.yml`).
- [ ] La dernière version de PySide6 passe les tests localement avant de relever la borne `<7`.
- [ ] L'exécutable fraîchement construit se lance sur une machine Windows propre.
- [ ] Le comportement multi-écrans et DPI mixtes est revérifié sur un vrai double écran après une montée de Qt.

## Ébauche — à compléter

- [ ] Fréquence de vérification retenue (mensuelle ? à chaque montée mineure de Qt ?).
- [ ] Versions de PySide6 et PyInstaller validées « bonnes » pour chaque Release (à noter ici ou dans le CHANGELOG).
- [ ] Fiche de recette manuelle Windows (voir [ACCESSIBILITE.md](./ACCESSIBILITE.md) et [DEVELOPPEMENT.md](./DEVELOPPEMENT.md)).
