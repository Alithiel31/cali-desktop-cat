# Règles du jeu

Français · [English](en/GAMEPLAY.md)

Valeurs par défaut ; la plupart sont réglables dans le panneau (onglet Réglages).

## Activité et sommeil
- Tu es « actif » si ta dernière action clavier/souris date de moins de 60 s.
- Après 5 min d'inactivité (réglable, 1 à 60), le chat s'endort. Il se réveille dès que tu touches la souris.

## Cadeaux
- Un cadeau arrive après 20 min d'activité cumulée (réglable, 5 à 120). La progression ne compte pas tant qu'un cadeau
  attend d'être ouvert.
- Ouvrir le cadeau tire un chapeau au hasard : d'abord la rareté, puis un chapeau de cette rareté.
- Un chapeau jamais obtenu est porté tout de suite. Un doublon augmente le compteur.

| Rareté | Poids | Prix de revente (🐟) |
|---|---|---|
| Commun | 60 % | 5 |
| Peu commun | 22 % | 12 |
| Rare | 11 % | 30 |
| Épique | 5 % | 80 |
| Légendaire | 1,5 % | 250 |
| Exotique | 0,5 % | 800 |

On ne vend que les doublons (il en reste toujours un exemplaire).

Les cadeaux en attente s'additionnent (99 au plus) : un cadeau de concentration ne remplace pas un cadeau ordinaire.

### Chapeaux saisonniers
- **Citrouille** (épique) : seulement du 25 octobre au 2 novembre (Halloween).
- En saison, un cadeau sur cinq donne directement un chapeau de la saison ; les autres suivent le tirage normal.
- Hors saison, la garde-robe le montre en « ??? » avec le nom de sa saison.
- Ajouter une saison : une entrée dans `hats.SEASONS`, et `season="…"` sur le chapeau.

## Humeur et croquettes
- L'humeur va de 0 à 100 (50 pour un nouveau chat). Elle perd 1 point toutes les 3 min d'activité (pas pendant
  l'absence).
- **Nourrir** (panneau, ou clic droit sur le chat) : 5 croquettes pour +25. Impossible au-dessus de 95 (il n'a plus faim).
- Une caresse donne +1, sans dépasser 60 : rien ne remplace un repas.
- **Repu** (70 et plus) : les cadeaux ordinaires arrivent 25 % plus vite. **Affamé** (moins de 25) : il réclame dans ses
  miaous. Entre les deux : content.
- Les croquettes viennent des sessions de concentration et de la revente des doublons.

## Chasse à la souris
- Quand la souris vient de s'arrêter (entre 1,2 et 15 s) à hauteur du chat, sur sa surface et à sa portée, il la guette
  1 à 2 s puis bondit dessus.
- Si la souris bouge pendant l'affût, elle lui échappe (il boude 8 s).
- Entre deux chasses : 25 à 60 s. Jamais pendant une session de concentration ni quand il dort.
- Désactivable (« Chasser la souris »).
- **Elle emporte la souris** : une fois le bond réussi, elle garde le curseur devant ses pattes et l'emmène partout où
  elle va (marche, saut, chute). Elle ne s'endort pas dessus. Elle le lâche dès que tu bouges la souris de plus de 3 px,
  que tu l'attrapes, ou qu'une session de concentration démarre ; elle ne rechasse pas avant 25 s.
- Désactivable séparément (« Emporter la souris après le bond »).

## Jazz, le grand frère de Cali
- Jazz (un Nova Scotia Duck Tolling Retriever) passe de temps en temps : première visite 2 à 5 min après le lancement,
  puis toutes les 6 à 15 min. Il entre par un bord de l'écran, trotte sur le sol de l'écran de Cali (en traversant les
  écrans collés) et ressort de l'autre côté. Il n'est pas cliquable et ne gêne aucune fenêtre.
- **Visite à Cali** (6 fois sur 10, quand elle est au sol et libre) : il s'assoit près d'elle 3,5 à 6 s ; elle se tourne
  vers lui, avec des cœurs et une petite bulle (si les miaous sont activés). Il repart par où il est venu, et Cali le
  suit 7 fois sur 10, pendant 4 à 8 s, avant de décrocher.
- **Sieste à deux** : si Cali fait la sieste, il vient presque toujours (8 fois sur 10) se coucher contre elle sans la
  réveiller ; sa sieste dure alors au moins 12 s. Il repart quand elle se réveille (90 s au plus).
- Sinon il ne fait que passer, avec parfois un arrêt de 2 à 4 s.
- Jamais quand le chat est caché ou endormi (utilisateur absent), ni pendant une session de concentration. Il renonce si
  Cali devient indisponible (au travail, perchée sur une fenêtre, en plein saut, portée à la souris) ou quand elle arrive
  au bout du sol en le suivant.
- Désactivable (« Jazz rend visite à Cali »). Le bouton « Faire venir Jazz maintenant (test) » des Réglages le fait venir
  tout de suite, s'il peut passer à cet instant.

## Concentration
- Session de 1 à 180 min (25 min depuis l'icône ou le menu).
- Pendant la session, le chat va au bout de l'écran (ou sur le bord de la fenêtre où il est perché), s'assoit devant son
  ordinateur portable, entièrement visible, et affiche le temps restant.
- Fin d'une session de **10 min ou plus** : `10 + durée en minutes` croquettes et un cadeau immédiat.
- En dessous de 10 min : aucune récompense.
- Il faut avoir été **présent au moins la moitié de la session** (activité clavier/souris dans les 60 dernières secondes).
  Une session passée loin de l'ordinateur, ou pendant une mise en veille du PC, se termine sans récompense.
- La présence est conservée si l'appli redémarre en cours de session.
- Elle survit à un redémarrage de l'appli. Si elle est finie entre-temps, elle est abandonnée sans récompense.

### Pause (méthode Pomodoro)
- Après chaque session **récompensée**, une pause de 5 min (réglable, 1 à 30) : minuteur ☕ dans la bulle, et le chat
  te rappelle de te lever. À la fin, il propose de reprendre.
- Relancer une session ou « Passer la pause » l'arrête. Désactivable (« Pause après chaque session »).
- La pause n'est pas sauvegardée : un redémarrage de l'appli l'oublie.

## Raccourci clavier
- **Ctrl+Alt+C** affiche ou cache le chat, depuis n'importe quelle application. Désactivable.
- Si une autre application utilise déjà ce raccourci, il reste inactif (message dans le journal).
- Sur un clavier où AltGr+C tape un caractère, ce caractère est capturé : couper le raccourci dans les Réglages.

## Statistiques
- Temps actif, temps de concentration et cadeaux ouverts par jour, sur 60 jours conservés.
- Applis les plus utilisées du jour (40 maximum), d'après le nom de l'exécutable de la fenêtre active.
  Désactivable dans les Réglages (« Noter les applications utilisées ») : le temps d'écran continue de compter.
- **Effacer mes statistiques** (onglet Statistiques, avec confirmation) : vide l'historique, y compris dans les copies
  quotidiennes et les copies de migration. Chapeaux, croquettes et réglages sont conservés. Une copie illisible
  (`save.json.<date>.bak`) ne peut pas être nettoyée : la supprimer à la main si besoin.
- Tout reste dans `%APPDATA%/DesktopCat/save.json` (et ses copies de sécurité, voir [TROUBLESHOOTING.md](TROUBLESHOOTING.md)) ;
  rien n'est envoyé nulle part.

## Plein écran
Une appli plein écran (jeu, vidéo) cache le chat sur **son** écran seulement.
