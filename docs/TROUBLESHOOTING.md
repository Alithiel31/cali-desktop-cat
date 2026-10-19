# Dépannage

Français · [English](en/TROUBLESHOOTING.md)

Ce document grandit avec le projet : chaque problème rencontré et résolu y a sa place.

## Où sont les fichiers ?

Tout est dans `%APPDATA%\DesktopCat\` (dans Git Bash : `$APPDATA/DesktopCat/`).

| Fichier | Contenu |
|---|---|
| `save.json` | Ta progression : chapeaux, croquettes, réglages, statistiques des 60 derniers jours. |
| `save.json.AAAA-MM-JJ_HH-MM-SS.bak` | Un `save.json` illisible, mis de côté automatiquement (les 3 plus récents sont gardés). |
| `backups/save-AAAA-MM-JJ.json` | Copie quotidienne, faite au premier lancement du jour (les 7 plus récentes sont gardées). |
| `save.json.vN.bak` | Copie faite avant une migration du format (ou si la sauvegarde vient d'une version plus récente de l'appli). Jamais écrasée. |
| `desktopcat.log` | Le journal : démarrages, avertissements, erreurs. 1 Mo maximum, 2 anciens fichiers conservés (`.log.1`, `.log.2`). |
| `desktopcat.log.crash` | Trace d'un plantage fatal de l'interpréteur (très rare). Vide si tout va bien. |

Le verrou qui empêche de lancer deux chats est `%TEMP%\desktopcat.lock`.

## Lire le journal

- Clic droit sur l'icône de la zone de notification, puis **Ouvrir le journal**.
- Ou en ligne de commande : `notepad "$APPDATA/DesktopCat/desktopcat.log"` / `tail -50 "$APPDATA/DesktopCat/desktopcat.log"`.

Chaque ligne a la forme `date niveau module: message`. Les niveaux utiles :
`WARNING` (quelque chose d'anormal mais géré), `ERROR` (une action a échoué, par exemple une sauvegarde),
`CRITICAL` (exception non gérée, avec la trace complète).

Les lignes `Qt : ...` sont des messages de la bibliothèque graphique.

## Signaler un bug

Joins, si possible :
1. les dernières lignes de `desktopcat.log` (et `desktopcat.log.crash` s'il n'est pas vide) ;
2. ta version de Windows et de Python (la première ligne `Démarrage : ...` du journal les contient) ;
3. ta configuration d'écrans (nombre, échelle d'affichage) si le bug concerne le déplacement du chat ;
4. ce que tu faisais juste avant.

Dépôt : https://github.com/Alithiel31/cali-desktop-cat/issues

---

## Le chat ne démarre pas

### « Desktop Cat est déjà lancé »
Une instance tourne déjà : cherche l'icône dans la zone de notification (flèche ^ si elle est masquée).
Sinon, termine le processus `pythonw.exe` / `DesktopCat.exe` dans le Gestionnaire des tâches.

Après un plantage ou une extinction brutale, le verrou est repris tout seul au bout de **30 secondes**.
Si ça ne suffit pas : supprime `%TEMP%\desktopcat.lock`.

### Rien ne s'affiche, aucune erreur
Ouvre le journal. Lancée avec `pythonw` ou sans console, l'appli n'affiche jamais ses erreurs à l'écran : elles
sont toutes dans `desktopcat.log`. Pour voir les erreurs de démarrage en direct, lance `python main.py` dans une console.

## Le chat est invisible

- Menu de l'icône : si l'entrée est **Afficher le chat**, tu l'avais caché. Clique dessus.
- Une appli en **plein écran** (jeu, vidéo) cache le chat, mais seulement sur son écran.
- Un écran vient d'être branché ou débranché : le chat se replace tout seul en quelques instants.

## Le chat ne se perche pas sur mes fenêtres

- Vérifie les réglages : « Il marche sur le bord haut des fenêtres » doit être coché.
- Sont ignorées : les fenêtres **maximisées**, **réduites**, **sans titre**, plus petites que 250 × 120 px, les fenêtres
  d'outils, et celles d'un autre bureau virtuel.
- Il faut de la place au-dessus de la fenêtre pour que le chat tienne debout.
- Sont aussi ignorés les faux-semblants de fenêtres : overlays transparents aux clics (Steam, NVIDIA, Discord),
  fenêtres impossibles à activer, fenêtres superposées d'opacité nulle. Si le chat marche « dans le vide » au-dessus
  d'une de ces fenêtres, c'est un bug : joindre le journal et le nom de l'application.

## Pas de cadeau après une concentration

Une session ne rapporte rien si :
- elle dure **moins de 10 minutes** ;
- tu as été **présent moins de la moitié du temps** (pas de clavier ni de souris), ou le PC était en veille ;
- l'appli a été fermée, et la session s'est terminée pendant l'absence.

Quand la session se termine appli ouverte, une notification explique pourquoi (si « Notifications de fin de session » est coché). Voir [GAMEPLAY.md](GAMEPLAY.md).

## Le chat s'endort pendant que je regarde un film

Il s'endort après 5 minutes sans clavier ni souris (réglage « Il s'endort après », de 1 à 60 min). Regarder une vidéo
sans toucher à rien compte comme une absence. Limite connue, voir la [feuille de route](ROADMAP.md).

## Ctrl+Alt+C ne fait rien

- Réglages : « Raccourci clavier » doit être coché ; le menu de l'icône affiche alors « Cacher le chat   Ctrl+Alt+C ».
- Si une autre application utilise déjà ce raccourci, il reste inactif ; le journal le dit (« Raccourci Ctrl+Alt+C … »).
- Sur un clavier où AltGr+C tape un caractère, ce caractère est capturé : décocher le réglage.

## Pas de notifications

Panneau, onglet Réglages : « Notifications de fin de session » doit être coché.

## Le démarrage avec Windows ne marche plus

La commande est enregistrée dans `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` (valeur `DesktopCat`) et
actualisée à chaque lancement. Si Windows refuse la modification, vérifie que ton compte peut modifier cette clé, puis
réessaie d'activer « Lancer avec Windows » dans le panneau.

Le registre fait foi : si tu désactives Desktop Cat dans le Gestionnaire des tâches (onglet Démarrage), la case du
panneau se décoche d'elle-même ; la recocher le réactive. Si tu déplaces ou remplaces l'exe, le chemin est réécrit
au lancement suivant.

## Ma sauvegarde est perdue ou illisible

- Si `save.json` est corrompu, l'appli le met de côté (`save.json.<date>.bak`) puis **restaure automatiquement la copie
  quotidienne la plus récente** et te prévient par une notification. Tu perds au plus la progression du jour.
- Si aucune copie n'est utilisable, elle repart d'une sauvegarde neuve ; le fichier illisible reste récupérable à la main.
- Restaurer à la main : quitte l'appli, copie un fichier de `backups/` par-dessus `save.json`, relance.
- Le journal raconte tout (`Sauvegarde illisible`, `Sauvegarde restaurée depuis la copie du jour`).
- Pour repartir de zéro volontairement : quitte l'appli, supprime `save.json`.
- `Sauvegarde impossible` dans le journal : le disque est plein ou le dossier est protégé en écriture.

## Les emojis s'affichent en carrés

La police emoji de Windows (Segoe UI Emoji) est introuvable. Sur un Windows récent elle est toujours présente ;
sur un autre système (tests, Linux), c'est normal.

## Les tests échouent

- Les tests sont validés en CI avec **Python 3.12 et 3.13** et PySide6 6.x : utilise l'une de ces versions (3.10 plante).
- Lance-les depuis la racine du projet : `python -m unittest discover -s tests`.
- Sous Linux, il faut les bibliothèques système de Qt (par exemple `libegl1`).
- Les tests ne dépendent ni de tes écrans ni de ta souris (faux écrans, fausse souris). Si un test échoue chez toi
  et pas ailleurs, c'est une piste sérieuse : joins le nom du test et la sortie complète.
