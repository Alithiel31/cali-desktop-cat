# Feuille de route

Français · [English](en/ROADMAP.md)

Classée du plus urgent au plus anecdotique. `[x]` = fait. L'ordre à l'intérieur d'un niveau est l'ordre conseillé.
Dernière mise à jour : 20/10/2026, version 0.4.1 (environ 240 tests). Le point faible reste ce qui n'a jamais tourné
sur un vrai Windows (`winapi.py`, raccourci global, exécutable). La couverture de tests est à remesurer (la dernière
mesure, 85 %, date de la revue du 19/10/2026).

## Déjà fait — fiabilité de base
- [x] Verrou d'instance repris après un plantage (vérifié : il n'est pas repris tant que la 1re instance tourne).
- [x] Temps réellement écoulé et plafonné : une veille ne fausse plus statistiques ni cadeaux.
- [x] Récompense de concentration conditionnée à la présence (≥ 50 %).
- [x] Bulle lisible quel que soit le thème Windows ; sa pointe vise la tête du chat.
- [x] Chat au travail entièrement visible, replacé si un écran est débranché.
- [x] Journal d'erreurs (`desktopcat/log.py`), voir [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
- [x] Plus de téléportation à l'atterrissage sur une fenêtre déplacée.
- [x] Sauvegarde : copies horodatées, copie quotidienne avec restauration, version du format et migrations.
- [x] Tests indépendants de la machine (faux écrans, fausse souris, garde contre les vrais écrans).
- [x] CI GitHub Actions (Windows + Ubuntu, Python 3.12 et 3.13) ; CD : build de l'exe et Release sur tag `v*`.
- [x] `CHANGELOG.md`, `CONTRIBUTING.md` et documentation de projet.

## Niveau 1 — Urgent : distribution (Microsoft Store), puis v0.4.x
- [ ] **Distribution via le Microsoft Store** : Smart App Control bloque l'exe non signé sans recours, y compris sur
  la machine de dev. La candidature SignPath Foundation a été refusée (projet pas encore assez connu) ; le Store, qui
  signe les paquets qu'il publie, est la voie retenue. Reste : compte développeur, paquet MSIX, certification.
  Détail : [DISTRIBUTION.md](DISTRIBUTION.md#signature-et-microsoft-store).
- [x] **Valider sur un vrai Windows** : tests Windows en CI et sur la machine de dev (236 tests), checklist manuelle
  ([TEST-MANUEL.md](TEST-MANUEL.md)) passée avec Python le 19/10/2026.
- [ ] **Tester l'exe** sur une machine sans Smart App Control (ou une fois publié sur le Store) : démarrage, journal, sauvegarde,
  lancement avec Windows, Gestionnaire des tâches.
- [x] **Vie privée** : réglage « Noter les applications utilisées » + bouton « Effacer mes statistiques » (copies de
  sécurité lisibles comprises).
- [x] **Batterie** : plus de `timeBeginPeriod(1)` ; boucle à 10 passages/s quand le chat est caché ou endormi
  (utilisateur absent).
- [x] **Cadeaux cumulables** : la récompense de concentration ne se perd plus si un cadeau attendait (sauvegarde v2).
- [x] **Sauvegarde** : copie quotidienne aussi quand l'appli tourne plusieurs jours ; `fsync` et nouvelles tentatives.
- [x] **Fenêtres invisibles** : overlays, fenêtres non activables ou d'opacité nulle exclues du perchage ; titres lus
  sans message (pas de gel sur une fenêtre bloquée). *À vérifier sur un vrai Windows avec Steam/Discord ouverts.*
- [ ] **Mesure CPU** sur la vraie machine (au repos, endormi, en marche) pour décider de la suite : cache `exe` par pid,
  scan des fenêtres moins fréquent.

## Niveau 2 — Important : suite de la 0.4.x
- [x] **Lancement avec Windows** : le registre fait foi (y compris `StartupApproved`, écrit par le Gestionnaire des
  tâches) ; chemin réécrit au démarrage ; recocher la case réactive le démarrage.
- [ ] **Faux plein écran** : vérifier qu'une fenêtre maximisée avec barre des tâches masquée ne cache pas le chat
  (`IsZoomed` / `WS_CAPTION` dans `is_fullscreen`).
- [ ] **Plein écran et vidéo** : seule la fenêtre active est examinée (une vidéo plein écran sur l'autre écran ne cache
  pas le chat s'il y va). Et un film regardé sans toucher la souris endort le chat : piste,
  `CallNtPowerInformation(SystemExecutionState)` et le drapeau `ES_DISPLAY_REQUIRED` posé par les lecteurs vidéo.
- [ ] **Builds reproductibles** : versions figées (PySide6, PyInstaller), `.spec` versionné ; envisager `--onedir`
  (démarrage plus rapide, moins de faux positifs antivirus, et peut-être nécessaire pour Smart App Control).
  Icône et numéro de version : faits (v0.4.1).

## Niveau 3 — Moyen
- [ ] **Deuxième lancement visible** : le message « déjà lancé » part dans `print()`, invisible sans console. Ouvrir
  plutôt le panneau de l'instance en cours (`QLocalServer`).
- [ ] **Statistiques de concentration cohérentes** : le temps de concentration compte aussi l'absence, alors que la
  récompense exige la présence.
- [x] **Croquettes** : nourrir le chat (humeur, bonus de cadeaux quand il est repu). Boutique de chapeaux : plus tard.
- [x] Chapeau saisonnier (Halloween), chasse à la souris, pause Pomodoro, raccourci Ctrl+Alt+C.
  *À vérifier sur un vrai Windows : le raccourci (`RegisterHotKey` + filtre natif) et la chasse multi-écrans.*
- [ ] Rythme des cadeaux : 20 min passif contre 10 min en concentration, à revoir avec le bonus « repu » (+25 %).
- [ ] Objectif de long terme : collection complète, succès, autres saisons (Noël…), boutique.
- [ ] Qualité du code : continuer à découper `pet.py` (~700 lignes ; la physique, le placement, les entrées et les réactions en sont déjà sortis), rendre `winapi` injectable dans `Game`,
  typage progressif et ruff.

## Niveau 4 — Anecdotique
- [x] `.gitignore` : règle globale `*.png` retirée (`tools/out/` reste exclu).
- [x] Dossier vide `framerate test/` supprimé. [ ] La section « Exécutable » du README devrait renvoyer aux Releases.
- [ ] Captures ou GIF dans le README.
- [x] Documentation traduite en anglais (`README.en.md`, `docs/en/`).
- [ ] Heures de silence ; taille du texte indépendante de la taille du chat.
- [ ] Sons optionnels, nouvelles phrases, nom du chat modifiable depuis le chat ; plusieurs chats, nouveaux pelages.
- [ ] Police emoji de secours si Segoe UI Emoji manque.
- [ ] Panneau : ne reconstruire que les cartes de chapeaux qui changent (si le catalogue grossit).
