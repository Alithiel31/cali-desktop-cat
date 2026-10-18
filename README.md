# Desktop Cat 🐱

[![CI](https://github.com/Alithiel31/cali-desktop-cat/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Alithiel31/cali-desktop-cat/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12%20|%203.13-blue?logo=python)](https://www.python.org/)
[![Qt](https://img.shields.io/badge/PySide6-Qt%206-green?logo=qt)](https://doc.qt.io/qtforpython-6/)
[![Windows](https://img.shields.io/badge/Windows-10%20|%2011-0078D6?logo=windows)](https://github.com/Alithiel31/cali-desktop-cat/releases)

Un chat écaille qui vit sur ton bureau Windows : il se promène, se perche sur le bord des fenêtres,
tombe quand elles disparaissent, saute d'une fenêtre à l'autre, dort quand tu es absent,
miaule de temps en temps dans une bulle, te rapporte des cadeaux (chapeaux de 6 raretés) et travaille avec toi
pendant tes sessions de concentration. Il se promène sur tous tes écrans.

## Lancer
    pip install -r requirements.txt
    python main.py

## Tests
    python -m unittest discover -s tests -v
Tournent aussi hors Windows (Qt en mode `offscreen`, faux bureau et faux écrans).

Icône dans la zone de notification : panneau, concentration 25 min, cacher le chat, quitter.
Double-clic sur le chat = panneau ; clic droit = menu ; on peut l'attraper et le lâcher.

## Panneau
Garde-robe (porter, vendre les doublons), Concentration, Statistiques (7 jours + applis du jour), Réglages
(dont « Il miaule de temps en temps »).

## Plusieurs écrans
Un sol par écran (le bas de sa zone utile, barre des tâches exclue). Des écrans collés dont les bas sont à moins
de 80 px d'écart se traversent à pied ; sinon il saute ou tombe de l'un à l'autre. Il se perche sur les fenêtres
de tous les écrans, même à échelles d'affichage différentes. Une appli plein écran ne cache le chat que sur son
écran. Brancher ou débrancher un écran est géré à chaud.

## Concentration
Une session de moins de 10 min ne rapporte ni cadeau ni croquettes. Elle survit à un redémarrage de l'appli
(si elle est finie entre-temps, elle est abandonnée sans récompense).

## Limites connues
- Écrit sans accès à Windows : la logique (dont le multi-écrans, avec de faux écrans) est testée hors écran,
  mais l'API Windows réelle et les échelles d'affichage mixtes restent à valider chez toi.
- Une fenêtre à cheval sur deux écrans d'échelles différentes est convertie avec l'échelle d'un seul des deux.
- Sauvegarde : `%APPDATA%/DesktopCat/save.json`.

## Exécutable
    pip install pyinstaller
    pyinstaller --noconsole --onefile --name DesktopCat main.py

## Structure du projet
    main.py          point d'entrée
    desktopcat/      le code de l'appli (voir docs/ARCHITECTURE.md)
    tests/           tests unitaires (Qt hors écran)
    docs/            architecture et règles du jeu
    tools/           outils de développement (captures du panneau, lanceur de test, anciens prototypes)

## Vie privée
Tout reste sur ton ordinateur : l'appli n'envoie rien nulle part et n'a aucun accès réseau. Pour les statistiques,
elle note chaque seconde le **nom de l'exécutable** de la fenêtre active (40 applis par jour, 60 jours) dans
`%APPDATA%/DesktopCat/save.json`. Un interrupteur « ne pas suivre les applis » et un bouton « effacer mes statistiques »
sont prévus (voir la [feuille de route](docs/ROADMAP.md)). Détail : [SECURITY.md](SECURITY.md).

## Documentation
- [Architecture](docs/ARCHITECTURE.md) : modules, boucles, coordonnées, points d'extension.
- [Règles du jeu](docs/GAMEPLAY.md) : cadeaux, raretés, concentration, statistiques.
- [Développement](docs/DEVELOPPEMENT.md) : installer, tester, conventions.
- [Distribution](docs/DISTRIBUTION.md) : fabriquer l'exécutable, publier une Release, SmartScreen.
- [Dépannage](docs/TROUBLESHOOTING.md) : où sont les fichiers, lire le journal, problèmes courants.
- [Feuille de route](docs/ROADMAP.md) : ce qui est fait et ce qui reste, du plus critique au plus anecdotique.
- [Accessibilité](docs/ACCESSIBILITE.md) *(ébauche)*.
- [Veille des dépendances](docs/VEILLE-DEPENDANCES.md) : PySide6, PyInstaller, API Windows.
- [Guide de reprise](docs/GUIDE-DE-REPRISE.md) : reprendre le projet sans le mainteneur.
- [Outils](tools/README.md) : lanceur de test isolé, captures du panneau.
- [Changelog](CHANGELOG.md).

## Développement
- Tester sans toucher à ta vraie sauvegarde : `tools\run_test_instance.bat`.
- Captures du panneau : `python tools/preview_panel.py` (écrites dans `tools/out/`).

## Contribuer
Environnement, tests, convention de commit : [CONTRIBUTING.md](CONTRIBUTING.md). Aide : [SUPPORT.md](SUPPORT.md).
Code de conduite : [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Sécurité
Pour signaler une vulnérabilité, voir [SECURITY.md](SECURITY.md) — pas d'issue publique.

## Licence
MIT, voir [LICENSE](LICENSE).

---

Fait par **Jacques Duchamplecheval** ([alithiel31](https://github.com/Alithiel31)) — [alithiel31.dev](https://alithiel31.dev) · [contact@alithiel31.dev](mailto:contact@alithiel31.dev)
