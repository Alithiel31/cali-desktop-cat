# Règles du jeu

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

## Statistiques
- Temps actif, temps de concentration et cadeaux ouverts par jour, sur 60 jours conservés.
- Applis les plus utilisées du jour (40 maximum), d'après le nom de l'exécutable de la fenêtre active.
- Tout reste dans `%APPDATA%/DesktopCat/save.json` (et ses copies de sécurité, voir [TROUBLESHOOTING.md](TROUBLESHOOTING.md)) ;
  rien n'est envoyé nulle part.

## Plein écran
Une appli plein écran (jeu, vidéo) cache le chat sur **son** écran seulement.
