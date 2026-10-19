# CHANGELOG

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) ; versions selon [SemVer](https://semver.org/lang/fr/).
Catégories : `Added`, `Changed`, `Fixed`, `Security`.

## [Non publié]

## [0.4.0] - 2026-10-19

Première Release publiée (la 0.3.0 n'a jamais été taguée : son contenu est inclus ici).

### Added

- **Nourrir le chat** : humeur de 0 à 100, repas à 5 croquettes (panneau, clic droit, icône). Repu, il rapporte les
  cadeaux 25 % plus vite ; affamé, il réclame. Les caresses aident un peu.
- **Chapeau saisonnier** « Citrouille », du 25 octobre au 2 novembre.
- **Chasse à la souris** : il guette la souris qui vient de s'arrêter près de lui, puis bondit dessus (désactivable).
- **Pause Pomodoro** après chaque session réussie (5 min réglables), minuteur ☕ dans la bulle, bouton « Passer la pause ».
- **Raccourci Ctrl+Alt+C** pour afficher ou cacher le chat (désactivable).
- **Icône** de l'exécutable (`assets/desktopcat.ico`, générée par `tools/make_icon.py` à partir du sprite : chat entier en
  grand, tête seule à 48 px et moins) et du panneau.

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
