# Feuille de route

Classée du plus urgent au plus anecdotique. `[x]` = fait. L'ordre à l'intérieur d'un niveau est l'ordre conseillé.
Revue complète du 19/10/2026 : 159 tests, 85 % de couverture ; le point faible est ce qui n'a jamais tourné sur un
vrai Windows (`winapi.py` couvert à 27 %).

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

## Niveau 1 — Urgent : avant de taguer v0.3.0
- [ ] **Valider sur un vrai Windows.** Test rapide limité à Windows en CI : `list_windows`, `foreground`,
  `idle_seconds`, `window_rect` tournent sans erreur ctypes et renvoient les bons types. Plus une vérification à la main :
  perchage, saut, chute, double écran, échelles d'affichage mixtes. Ensuite, retirer « Écrit sans accès à Windows » du README.
- [ ] **Tester l'exe avant le tag** : artefact d'un build de PR, essayé sur une machine sans Python (démarrage, journal,
  sauvegarde, lancement avec Windows).
- [x] **Vie privée** : réglage « Noter les applications utilisées » + bouton « Effacer mes statistiques » (copies de
  sécurité lisibles comprises).
- [x] **Batterie** : plus de `timeBeginPeriod(1)` ; boucle à 10 passages/s quand le chat est caché ou endormi
  (utilisateur absent).
- [ ] **Mesure CPU** sur la vraie machine (au repos, endormi, en marche) pour décider de la suite : cache `exe` par pid,
  scan des fenêtres moins fréquent.

## Niveau 2 — Important : v0.3.1
- [ ] **Lancement avec Windows** : réécrire la clé de registre à chaque démarrage (exe déplacé ou mis à jour) et tenir
  compte de l'échec de `autostart.set_enabled` (aujourd'hui la case reste cochée même si l'écriture échoue).
- [ ] **Plein écran et vidéo** : seule la fenêtre active est examinée (une vidéo plein écran sur l'autre écran ne cache
  pas le chat s'il y va). Et un film regardé sans toucher la souris endort le chat.
- [ ] **Builds reproductibles** : versions figées (PySide6, PyInstaller), `.spec` versionné, icône, numéro de version
  dans le panneau ; envisager `--onedir` (démarrage plus rapide, moins de faux positifs antivirus).

## Niveau 3 — Moyen
- [ ] **Deuxième lancement visible** : le message « déjà lancé » part dans `print()`, invisible sans console. Ouvrir
  plutôt le panneau de l'instance en cours (`QLocalServer`).
- [ ] **Statistiques de concentration cohérentes** : le temps de concentration compte aussi l'absence, alors que la
  récompense exige la présence.
- [ ] **Croquettes.** Elles s'accumulent sans servir : boutique de chapeaux, nourrir le chat, ou les deux. *À décider.*
- [ ] Rythme des cadeaux : 20 min passif contre 10 min en concentration, à rééquilibrer une fois les croquettes utiles.
- [ ] Objectif de long terme : collection complète, succès, saisons. Plus d'interactions (curseur, humeur).
- [ ] Qualité du code : découper `pet.py` (~780 lignes, couvert à 94 %), rendre `winapi` injectable dans `Game`,
  typage progressif et ruff.

## Niveau 4 — Anecdotique
- [ ] `.gitignore` : retirer la règle globale `*.png` (elle bloquera captures du README et icône ; `tools/out/` reste exclu).
- [ ] Supprimer le dossier vide `framerate test/` ; la section « Exécutable » du README renvoie aux Releases.
- [ ] Captures ou GIF dans le README.
- [ ] Heures de silence ; taille du texte indépendante de la taille du chat.
- [ ] Sons optionnels, nouvelles phrases, nom du chat modifiable depuis le chat ; plusieurs chats, nouveaux pelages.
- [ ] Police emoji de secours si Segoe UI Emoji manque.
- [ ] Panneau : ne reconstruire que les cartes de chapeaux qui changent (si le catalogue grossit).
