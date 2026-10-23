# Test manuel avant une Release

Français · [English](en/MANUAL-TESTING.md)

Ce que la CI ne peut pas vérifier : le vrai Windows (fenêtres, overlays, raccourci, plusieurs écrans) et l'exécutable.
Compter 20 à 30 min. Noter chaque point ✅ / ❌ ; pour un ❌, joindre `desktopcat.log` (menu de l'icône > Ouvrir le journal).

## 0. Avant de commencer
- [ ] La CI de `main` est verte (onglet *Actions* du dépôt), en particulier les jobs **Windows**.
- [ ] Lancer l'instance de test : double-clic sur `tools\run_test_instance.bat`
  (sauvegarde isolée dans `%TEMP%\desktopcat_test`, 50 croquettes, chat affamé, miaous coupés).
  Pour retrouver le journal : `%TEMP%\desktopcat_test\DesktopCat\desktopcat.log`.

## 1. Démarrage
- [ ] Le chat apparaît en bas de l'écran, sans rectangle autour ; l'icône est dans la zone de notification.
- [ ] Relancer le `.bat` : pas de 2e chat.
- [ ] Le journal contient « Démarrage » et « Raccourci Ctrl+Alt+C actif », sans ligne `ERROR`.

## 2. Fenêtres et perchage
- [ ] Ouvrir le Bloc-notes, attendre : le chat finit par sauter sur son bord haut et y marcher.
- [ ] Déplacer la fenêtre : il suit, sans téléportation.
- [ ] Réduire / fermer la fenêtre : il tombe et atterrit au sol (ou sur une fenêtre en dessous).
- [ ] Le porter à la souris et le lâcher au-dessus d'une fenêtre : il s'y pose.
- [ ] **Overlays** : ouvrir Steam et/ou Discord (overlay en jeu activé si possible). Le chat ne marche jamais « dans le vide ».
- [ ] Une fenêtre qui « ne répond pas » (optionnel) : le chat continue de bouger normalement.

## 3. Interactions
- [ ] Clic : cœurs. Double-clic : le panneau s'ouvre.
- [ ] **Repas** : clic droit > « Donner des croquettes » : « Miam ! », cœurs ; en-tête du panneau : 🐟 45, humeur 45.
  Répéter jusqu'à 95+ : l'option devient grisée.
- [ ] **Chasse** : bouger la souris près du chat (même hauteur, sur le sol à côté de lui), puis la lâcher. En quelques
  secondes, il la guette (yeux grands ouverts) puis bondit dessus. Recommencer en bougeant pendant l'affût : il abandonne.
- [ ] **Souris emportée** : après le bond, ne pas toucher à la souris : le curseur reste devant les pattes de Cali et la
  suit quand elle marche ou saute. Bouger la souris d'une dizaine de pixels : elle la lâche et ne la reprend pas.
  Décocher « Emporter la souris après le bond » : elle bondit toujours mais ne garde plus le curseur.
- [ ] **Jazz** : Réglages > « Faire venir Jazz maintenant (test) » : un chien roux entre par un bord de l'écran et trotte
  sur le sol. Recommencer plusieurs fois : tantôt il traverse (parfois assis un instant), tantôt il vient s'asseoir près
  de Cali, qui se tourne vers lui (cœurs), puis il repart, souvent suivi par elle. Un clic sur lui passe à travers.
- [ ] **Sieste à deux** : laisser Cali s'endormir (sieste au sol, sans bouger), puis faire venir Jazz : il se couche contre
  elle sans la réveiller, et repart quand elle se réveille. Cacher le chat (Ctrl+Alt+C) pendant une visite : Jazz
  disparaît aussi. Décocher « Jazz rend visite à Cali » : le bouton de test n'a plus d'effet.
- [ ] **Raccourci** : dans une autre appli (navigateur), Ctrl+Alt+C cache le chat, encore une fois le réaffiche.
  Le menu de l'icône affiche « Cacher le chat   Ctrl+Alt+C ». Décocher le réglage : le raccourci ne fait plus rien.

## 4. Cadeaux et concentration
- [ ] Réglages > « Recevoir un cadeau maintenant » deux fois : le chat pose un cadeau ; en l'ouvrant, la bulle du chapeau
  reste lisible, puis le 2e cadeau arrive.
- [ ] Session de **10 min** (onglet Concentration, champ libre) en restant devant l'écran : le chat s'installe à son
  ordinateur, ⏱ dans la bulle. À la fin : notification, cadeau, « Pause de 5 min », ☕ dans la bulle,
  bouton « Passer la pause » dans le panneau et dans le menu de l'icône.
- [ ] Laisser la pause aller au bout (ou mettre 1 min dans les Réglages avant la session) : « Pause finie ! ».

## 5. Plein écran et sommeil
- [ ] Une vidéo YouTube en plein écran : le chat disparaît de cet écran, revient à la sortie.
- [ ] Ne plus toucher à rien 5 min : il s'endort (« z »). Bouger la souris : « Te revoilà ! ».

## 6. Plusieurs écrans (si disponible)
- [ ] Il passe d'un écran à l'autre (à pied si les bas sont alignés, sinon en sautant ou en tombant).
- [ ] Échelles différentes (100 % / 125 %) : bulle et particules restent au-dessus de sa tête.
- [ ] Débrancher l'écran où il se trouve : il réapparaît sur l'autre.

## 7. L'exécutable (sur un PC sans Python si possible)
- [ ] Télécharger l'artefact `DesktopCat-windows` du dernier build (Actions > Release > Artifacts), vérifier le SHA256.
- [ ] Il démarre (SmartScreen : « Informations complémentaires » > « Exécuter quand même »).
- [ ] Journal et sauvegarde créés dans `%APPDATA%\DesktopCat`.
- [ ] Réglages > « Lancer avec Windows » coché, fermer la session Windows et la rouvrir : le chat revient.
- [ ] Gestionnaire des tâches > Démarrage : « Désactiver » Desktop Cat, puis rouvrir le panneau : la case est décochée.
  La recocher : le Gestionnaire des tâches (F5) le montre « Activé ».

## 8. Chapeau saisonnier (optionnel)
- [ ] Avancer la date de Windows au 31 octobre, relancer, ouvrir une dizaine de cadeaux de test : une Citrouille sort
  (≈ 1 sur 5). Remettre la date.

## Résultat
Tout est ✅ : mettre à jour la version (`desktopcat/__init__.py`), la section du CHANGELOG, puis taguer
(voir [DISTRIBUTION.md](DISTRIBUTION.md)).
