# Desktop Cat 🐱

Français · [English](README.en.md)

[![CI](https://github.com/Alithiel31/cali-desktop-cat/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Alithiel31/cali-desktop-cat/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12%20|%203.13-blue?logo=python)](https://www.python.org/)
[![Qt](https://img.shields.io/badge/PySide6-Qt%206-green?logo=qt)](https://doc.qt.io/qtforpython-6/)
[![Windows](https://img.shields.io/badge/Windows-10%20|%2011-0078D6?logo=windows)](https://github.com/Alithiel31/cali-desktop-cat/releases)

Un chat écaille qui vit sur ton bureau Windows : il se promène, se perche sur le bord des fenêtres,
tombe quand elles disparaissent, saute d'une fenêtre à l'autre, dort quand tu es absent,
miaule de temps en temps dans une bulle, guette ta souris, a faim (tu le nourris avec des croquettes), te rapporte
des cadeaux (chapeaux de 6 raretés, dont un de saison à Halloween) et travaille avec toi pendant tes sessions de
concentration, suivies d'une pause Pomodoro. Il se promène sur tous tes écrans, et **Ctrl+Alt+C** l'affiche ou le cache.

## Installer
Télécharger `DesktopCat.exe` dans les [Releases](https://github.com/Alithiel31/cali-desktop-cat/releases) et le lancer :
aucune installation, aucun droit administrateur. L'empreinte SHA256 est publiée à côté de l'exe.

> L'exe n'est **pas encore signé** : SmartScreen affiche un avertissement (« Informations complémentaires » >
> « Exécuter quand même »), et **Smart App Control** (Windows 11), s'il est actif, le bloque sans recours.
> Une demande de signature gratuite est en cours (voir [Code signing policy](#code-signing-policy)).
> En attendant, on peut lancer l'appli depuis les sources (ci-dessous).

## Désinstaller
1. Panneau > Réglages : décocher **Lancer avec Windows** (retire l'entrée du registre de démarrage).
2. Quitter le chat (clic droit sur l'icône > Quitter).
3. Supprimer `DesktopCat.exe`, puis le dossier `%APPDATA%\DesktopCat` (sauvegarde, copies, journal).

Aucun autre fichier ni aucune autre clé de registre n'est créé. Si l'exe a déjà été supprimé sans décocher la case,
retirer l'entrée **DesktopCat** dans Gestionnaire des tâches > Applications de démarrage (ou la valeur `DesktopCat`
de `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`).

## Lancer depuis les sources
    pip install -r requirements.txt
    python main.py

## Tests
    python -m unittest discover -s tests -v
Tournent aussi hors Windows (Qt en mode `offscreen`, faux bureau et faux écrans).

Icône dans la zone de notification : panneau, concentration 25 min (ou arrêt), passer la pause, donner des croquettes,
cacher le chat (Ctrl+Alt+C), ouvrir le journal, quitter.
Double-clic sur le chat = panneau ; clic droit = menu (dont « Donner des croquettes ») ; on peut l'attraper et le lâcher.

## Panneau
En-tête : croquettes, humeur du chat et bouton **Nourrir**. Onglets : Garde-robe (porter, vendre les doublons),
Concentration (et pause), Statistiques (7 jours + applis du jour), Réglages (dont « Il miaule de temps en temps »).

## Plusieurs écrans
Un sol par écran (le bas de sa zone utile, barre des tâches exclue). Des écrans collés dont les bas sont à moins
de 80 px d'écart se traversent à pied ; sinon il saute ou tombe de l'un à l'autre. Il se perche sur les fenêtres
de tous les écrans, même à échelles d'affichage différentes. Une appli plein écran ne cache le chat que sur son
écran. Brancher ou débrancher un écran est géré à chaud.

## Concentration
Une session de moins de 10 min ne rapporte ni cadeau ni croquettes. Elle survit à un redémarrage de l'appli
(si elle est finie entre-temps, elle est abandonnée sans récompense).

## Limites connues
- Les échelles d'affichage mixtes (100 % / 125 % sur deux écrans) sont testées avec de faux écrans, peu sur du vrai
  matériel.
- Une fenêtre à cheval sur deux écrans d'échelles différentes est convertie avec l'échelle d'un seul des deux.
- Sauvegarde : `%APPDATA%/DesktopCat/save.json`.

## Exécutable
    pip install pyinstaller
    python tools/make_version_file.py
    pyinstaller --noconsole --onefile --name DesktopCat --icon assets/desktopcat.ico --version-file build/version_info.txt main.py

## Structure du projet
    main.py          point d'entrée
    desktopcat/      le code de l'appli (voir docs/ARCHITECTURE.md)
    tests/           tests unitaires (Qt hors écran)
    docs/            documentation en français ; docs/en/ : la version anglaise
    assets/          icône de l'exécutable
    tools/           outils de développement (icône, métadonnées de l'exe, captures du panneau, lanceur de test)
    .github/         CI/CD, modèles d'issues et de PR, Dependabot

## Vie privée
Tout reste sur ton ordinateur : l'appli n'envoie rien nulle part et ne fait aucun accès réseau. Pour les statistiques,
elle note chaque seconde le **nom de l'exécutable** de la fenêtre active (40 applis par jour, 60 jours) dans
`%APPDATA%/DesktopCat/save.json`. Ce suivi se coupe dans **Réglages** (« Noter les applications utilisées »), et le
bouton **Effacer mes statistiques** (onglet Statistiques) efface tout l'historique, copies de sécurité comprises.
Détail : [SECURITY.md](SECURITY.md).

## Code signing policy
Free code signing provided by [SignPath.io](https://about.signpath.io/), certificate by
[SignPath Foundation](https://signpath.org/) *(application in progress: current releases are not signed yet)*.

- **Product:** Desktop Cat — repository [Alithiel31/cali-desktop-cat](https://github.com/Alithiel31/cali-desktop-cat), MIT License.
- **What is signed:** only `DesktopCat.exe` attached to the GitHub Releases of this repository, built from this
  source code by GitHub Actions (`.github/workflows/release.yml`). Nothing else is signed.
- **Committers and reviewers:** [Jacques Duchamplecheval (alithiel31)](https://github.com/Alithiel31)
- **Approvers:** [Jacques Duchamplecheval (alithiel31)](https://github.com/Alithiel31) — every release is approved
  manually before signing.
- **Privacy policy:** this program will not transfer any information to other networked systems unless specifically
  requested by the user or the person installing or operating it. See [Vie privée](#vie-privée) for what it stores
  locally.

## Documentation
- [Architecture](docs/ARCHITECTURE.md) : modules, boucles, coordonnées, points d'extension.
- [Règles du jeu](docs/GAMEPLAY.md) : cadeaux, raretés, concentration, statistiques.
- [Développement](docs/DEVELOPPEMENT.md) : installer, tester, conventions.
- [Test manuel](docs/TEST-MANUEL.md) : la checklist à passer sur un vrai Windows avant une Release.
- [Distribution](docs/DISTRIBUTION.md) : fabriquer l'exécutable, publier une Release, SmartScreen.
- [Dépannage](docs/TROUBLESHOOTING.md) : où sont les fichiers, lire le journal, problèmes courants.
- [Feuille de route](docs/ROADMAP.md) : ce qui est fait et ce qui reste, du plus critique au plus anecdotique.
- [Accessibilité](docs/ACCESSIBILITE.md) *(ébauche)*.
- [Veille des dépendances](docs/VEILLE-DEPENDANCES.md) : PySide6, PyInstaller, API Windows.
- [Guide de reprise](docs/GUIDE-DE-REPRISE.md) : reprendre le projet sans le mainteneur.
- [Outils](tools/README.md) : lanceur de test isolé, captures du panneau.
- [Changelog](CHANGELOG.md).

Toute la documentation existe aussi **en anglais** : [README.en.md](README.en.md), [docs/en/](docs/en/) et les fichiers
`*.en.md` à la racine. Les deux versions se mettent à jour ensemble.

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
