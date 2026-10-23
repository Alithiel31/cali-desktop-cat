# CHANGELOG

Français · [English](docs/en/CHANGELOG.md)

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) ; versions selon [SemVer](https://semver.org/lang/fr/).
Catégories : `Added`, `Changed`, `Fixed`, `Security`.

## [Non publié]

### Added

- **Jazz, le grand frère de Cali** : un Nova Scotia Duck Tolling Retriever en pixel art (`desktopcat/dog.py` et
  `dog_sprite.py`) rend visite à Cali de temps en temps (première visite 2 à 5 min après le lancement, puis toutes les
  6 à 15 min). Il traverse l'écran, vient la saluer (elle se tourne vers lui, cœurs et bulle, puis le suit souvent
  quelques secondes quand il repart) ou, si elle fait la sieste, se couche contre elle sans la réveiller. Fenêtre
  transparente sans souris, hasard séparé de celui du chat ; jamais pendant une session de concentration, ni quand le
  chat est caché ou endormi. Réglage « Jazz rend visite à Cali » (actif par défaut) et bouton de test dans les
  Réglages ; `tools/preview_jazz.py` génère un aperçu de son dessin.
- **Documentation en anglais** : `README.en.md`, `tools/README.en.md` et `docs/en/` (une version de chaque document de `docs/`,
  plus `CONTRIBUTING`, `SECURITY`, `SUPPORT`, `CODE_OF_CONDUCT` et `CHANGELOG`). Chaque document français renvoie à sa
  version anglaise, et inversement.

### Changed

- **Distribution** : la candidature SignPath Foundation est refusée ; la voie retenue est le Microsoft Store. Documentation
  (README, distribution, feuille de route, sécurité, guide de reprise) mise à jour, section « Code signing policy »
  du README et bloc SignPath commenté de `release.yml` retirés.
- CI : `actions/download-artifact` passe en v8, aligné sur `upload-artifact` v7.
- **Builds reproductibles** : `requirements-build.txt` fige PySide6 (6.12.0) et PyInstaller (6.22.3) pour fabriquer l'exe ;
  `release.yml` l'utilise à la place d'un `pip install pyinstaller` sans version.
- **Linter ruff** : `pyproject.toml` (120 colonnes, règles E, F, W, I, B, UP), job `lint` bloquant dans `ci.yml`,
  `requirements-dev.txt`. Code mis en conformité : imports triés, variables `l` renommées, lambdas assignés remplacés par des
  `def`, `zip(strict=…)`, lignes coupées ; aucun changement de comportement. Pas de formateur automatique.
- **`DesktopCat.spec` versionné** : les options du build (icône, métadonnées, sans console, UPX désactivé) vivent dans le
  `.spec`, utilisé par le build local et par `release.yml`. `*.spec` quitte le `.gitignore`.
- Rangement du dépôt : prototypes historiques déplacés de `tools/spikes/` vers `archive/spikes/` ; règle globale `*.png`
  retirée du `.gitignore` (seul `tools/out/` reste ignoré), pour pouvoir versionner captures et images.
- Documentation remise à jour pour la 0.4.1 : architecture (boucle ralentie, modules, tableau des tests),
  feuille de route (chiffres, niveaux, `pet.py`), distribution (exemples, signature), dépannage (overlays, Ctrl+Alt+C,
  `StartupApproved`), guide de reprise, contribution, sécurité (raccourci global, registre).

## [0.4.1] - 2026-10-19

Préparation de la signature de code (SignPath Foundation).

### Added

- **Icône** de l'exécutable (`assets/desktopcat.ico`, générée par `tools/make_icon.py` à partir du sprite : chat entier en
  grand, tête seule à 48 px et moins) et du panneau.
- **Métadonnées de l'exe** (Propriétés > Détails : Desktop Cat, version, auteur), générées par
  `tools/make_version_file.py` à partir de `desktopcat.__version__`.
- Numéro de version dans le titre du panneau, en bas des Réglages et dans l'infobulle de l'icône.
- README : sections **Installer**, **Désinstaller** et **Code signing policy** ; avertissement Smart App Control.
- `release.yml` : bloc de signature SignPath prêt, commenté jusqu'à l'acceptation du projet.

## [0.4.0] - 2026-10-19

Première Release publiée (la 0.3.0 n'a jamais été taguée : son contenu est inclus ici).

### Added

- **Nourrir le chat** : humeur de 0 à 100, repas à 5 croquettes (panneau, clic droit, icône). Repu, il rapporte les
  cadeaux 25 % plus vite ; affamé, il réclame. Les caresses aident un peu.
- **Chapeau saisonnier** « Citrouille », du 25 octobre au 2 novembre.
- **Chasse à la souris** : il guette la souris qui vient de s'arrêter près de lui, puis bondit dessus (désactivable).
- **Pause Pomodoro** après chaque session réussie (5 min réglables), minuteur ☕ dans la bulle, bouton « Passer la pause ».
- **Raccourci Ctrl+Alt+C** pour afficher ou cacher le chat (désactivable).

- Réglage « Noter les applications utilisées » pour couper le suivi des exécutables actifs.
- Bouton « Effacer mes statistiques » (avec confirmation) : vide l'historique, copies de sécurité lisibles comprises.

- Documentation de projet : `CONTRIBUTING.md`, `SECURITY.md`, `SUPPORT.md`, `CODE_OF_CONDUCT.md`, ce `CHANGELOG.md`,
  modèles d'issues et de PR, `CODEOWNERS`, Dependabot, et dans `docs/` : `DEVELOPPEMENT.md`, `DISTRIBUTION.md`,
  `GUIDE-DE-REPRISE.md`, `ACCESSIBILITE.md` (ébauche), `VEILLE-DEPENDANCES.md`.

### Changed

- Batterie : plus de `timeBeginPeriod(1)` (minuterie système forcée à 1 ms en permanence) ; la boucle du chat passe
  de ~60 à 10 passages par seconde quand il est caché ou endormi parce que l'utilisateur est absent.
- Sauvegarde au format v2 : `gift_pending` (oui/non) devient `gifts_pending` (nombre de cadeaux en attente).
  Les sauvegardes v1 sont migrées automatiquement (copie `save.json.v1.bak` gardée).
- Un cadeau en attente laisse finir la bulle en cours (« Te revoilà ! », chapeau qu'on vient d'ouvrir) avant
  d'apparaître.

### Fixed

- Le cadeau d'une session de concentration n'est plus perdu quand un cadeau ordinaire attendait déjà : ils s'additionnent.
- Copie quotidienne de la sauvegarde aussi quand l'appli tourne plusieurs jours sans redémarrer (PC mis en veille).
- Sauvegarde forcée sur le disque (`fsync`) avant le remplacement : une coupure de courant ne laisse plus de fichier vide.
  Le remplacement est retenté si un antivirus verrouille le fichier un instant.
- Le chat ne se perche plus sur les fenêtres invisibles : overlays transparents aux clics (Steam, NVIDIA, Discord),
  fenêtres impossibles à activer, fenêtres superposées d'opacité nulle.
- Lecture des titres de fenêtres sans leur envoyer de message (`InternalGetWindowText`) : une fenêtre qui « ne répond
  pas » ne peut plus geler le chat.
- Lancement avec Windows : le registre fait foi. La case suit une désactivation faite dans le Gestionnaire des tâches
  (`StartupApproved`), la recocher réactive vraiment le démarrage, et le chemin de l'exe est réécrit au lancement s'il
  a changé (exe déplacé ou mis à jour).
- `tools/run_test_instance.bat` utilise le Python du `.venv` du projet en priorité.

## [0.3.0] - 2026-10-18

Première version complète, jamais taguée ni publiée : tout son contenu fait partie de la 0.4.0.

### Added

- Chat en pixel art (pelage écaille) qui se promène sur le bureau Windows, se perche sur le bord des fenêtres, tombe
  quand elles disparaissent, saute d'une fenêtre à l'autre et s'endort après une période d'inactivité.
- Multi-écrans : un sol par écran, traversée à pied des écrans collés, saut ou chute entre les autres, branchement et
  débranchement à chaud, plein écran qui ne cache le chat que sur son écran.
- Cadeaux et chapeaux : 6 raretés, tirage pondéré, revente des doublons contre des croquettes.
- Sessions de concentration (1 à 180 min), récompense conditionnée à la durée (≥ 10 min) et à la présence (≥ 50 %),
  reprise après redémarrage de l'appli.
- Panneau de contrôle : garde-robe, concentration, statistiques (7 jours + applis du jour), réglages.
- Icône dans la zone de notification, bulles de miaou, démarrage avec Windows (optionnel).
- Journal d'erreurs (`desktopcat.log`, rotation 1 Mo) accessible depuis le menu de l'icône.
- Sauvegarde robuste : écriture atomique, copies horodatées d'un fichier illisible (3 gardées), copie quotidienne
  (7 gardées) avec restauration automatique et notification, version du format et migrations.
- Tests indépendants de la machine (faux écrans, fausse souris, faux bureau) et garde contre les vrais écrans.
- CI GitHub Actions (Windows et Ubuntu 24.04, Python 3.12 et 3.13) ; CD : build de `DesktopCat.exe` et publication
  d'une Release avec empreinte SHA256 sur tag `v*`.
- Documentation : README, architecture, règles du jeu, dépannage, feuille de route, outils de développement.

### Changed

- La pointe de la bulle de miaou vise désormais la tête du chat.
- Le temps compté par le jeu est le temps réellement écoulé, plafonné à 5 s par passage.

### Fixed

- Le verrou d'instance laissé par un plantage est repris au bout de 30 s.
- Une veille du PC ne fausse plus les statistiques ni la progression des cadeaux.
- Bulle illisible en thème sombre Windows : fond dessiné, texte forcé foncé, taille liée à l'échelle du chat.
- Au travail, le chat reste entièrement visible (l'ordinateur sortait de l'écran).
- Le chat ne se téléporte plus en atterrissant sur une fenêtre déplacée pendant le saut.
- Particules (« z », cœurs) décalées sur le second écran : une fenêtre d'effets par écran.
- CI : Python 3.10 retiré (plante avec PySide6 6.12), Ubuntu 24.04 épinglé.
