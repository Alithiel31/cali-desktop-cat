# Feuille de route

Classée du plus critique au plus anecdotique. `[x]` = fait. L'ordre à l'intérieur d'un niveau est l'ordre conseillé.

## Niveau 1 — Critique : ne pas perdre de données, ne pas se bloquer, ne pas mentir
- [x] Verrou d'instance repris après un plantage (`setStaleLockTime(30 s)`).
- [x] Temps réellement écoulé et plafonné : une veille ne fausse plus statistiques ni cadeaux.
- [x] Récompense de concentration conditionnée à la présence (≥ 50 %).
- [x] Bulle lisible quel que soit le thème Windows (fond dessiné, texte forcé foncé, taille liée à l'échelle du chat).
- [x] **Journal d'erreurs** (`desktopcat/log.py`) : exceptions, messages Qt et plantages fatals dans
  `%APPDATA%/DesktopCat/desktopcat.log` (rotation 1 Mo), accessible depuis le menu de l'icône. Voir [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
- [x] **Téléportation à l'atterrissage.** Un chat qui sautait vers une fenêtre déplacée pendant le saut atterrissait
  sur son ancienne position puis la « suivait » d'un bond (parfois hors du bureau). Il relit maintenant la position réelle
  de la fenêtre en se posant. Trouvé grâce à un test qui échouait seulement selon la place de la souris.
- [ ] **Sauvegarde.** Le `.bak` est écrasé à chaque fichier illisible ; garder 3 copies horodatées. Utiliser le champ
  `version` pour des migrations réelles (aujourd'hui il est ignoré).
- [x] **Tests indépendants de la machine.** Faux écrans et fausse souris (`FixedCursor`) partout ; une garde fait échouer
  tout futur test qui lirait les vrais écrans, au lieu de le laisser réussir ou échouer selon l'ordinateur.

## Niveau 2 — Important : fiabilité de l'ensemble et confiance
- [ ] **Intégration continue** (GitHub Actions, runner Windows) : tests à chaque push.
- [ ] **Vie privée.** Interrupteur « ne pas suivre les applis utilisées » + bouton « effacer mes statistiques ».
  Aujourd'hui le nom de l'exécutable actif est enregistré chaque seconde.
- [ ] **Mesure de performance.** CPU du chat au repos, endormi, en marche. Ensuite seulement : boucle ralentie quand il
  dort, cache `exe` par pid, scan des fenêtres moins fréquent.
- [ ] **Vidéo ou film = absence ?** Après 5 min sans toucher la souris, le chat s'endort même si tu regardes un film.
  Ne pas l'endormir si une appli est en plein écran.
- [ ] **Échelles d'affichage mixtes** (limite connue) : à valider sur un vrai double écran avec DPI différents.

## Niveau 3 — Distribution : pouvoir le partager
- [ ] `pyproject.toml`, dépendances figées.
- [ ] Spécification PyInstaller versionnée, icône de l'exécutable, numéro de version affiché dans le panneau.
- [ ] Release GitHub avec le `.exe` (prévoir l'avertissement SmartScreen : exécutable non signé).
- [ ] Démarrage automatique vérifié avec la version empaquetée (chemin de l'exécutable).

## Niveau 4 — Fond de jeu : donner envie de rester
- [ ] **Croquettes.** Elles s'accumulent sans servir : boutique de chapeaux, nourrir le chat, ou les deux. *À décider ensemble.*
- [ ] Objectif de long terme : collection complète, succès, saisons.
- [ ] Rythme des cadeaux : 20 min passif contre 10 min en concentration. À rééquilibrer une fois les croquettes utiles.
- [ ] Plus d'interactions : jouer avec le curseur, humeur du chat.

## Niveau 5 — Qualité du code
- [ ] Découper `pet.py` (~750 lignes) en physique, états/IA et interactions souris, sans changer le comportement.
- [ ] Rendre `winapi` injectable dans `Game` (plus de `mock.patch` global dans les tests).
- [ ] Typage progressif et un linter (ruff).

## Niveau 6 — Anecdotique : le petit plus
- [x] La pointe de la bulle vise la tête du chat.
- [ ] Heures de silence (pas de miaou ni de notification à certaines heures).
- [ ] Réglage « taille du texte » indépendant de la taille du chat.
- [ ] Sons optionnels, nouvelles phrases, nom du chat modifiable depuis le chat.
- [ ] Plusieurs chats, nouveaux pelages.
- [ ] Captures ou GIF dans le README, `CHANGELOG.md`, `CONTRIBUTING.md`.
- [ ] Police emoji de secours si Segoe UI Emoji manque.
