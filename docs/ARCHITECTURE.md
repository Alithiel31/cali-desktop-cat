# Architecture

Français · [English](en/ARCHITECTURE.md)

Desktop Cat est une appli PySide6 (Qt 6) pour Windows. Une seule règle guide le découpage :
**la logique pure (maths, règles du jeu) est séparée de ce qui touche à Qt et à Windows**, ce qui permet de
tester l'essentiel sur n'importe quel système.

## Vue d'ensemble

```
main.py ── crée et relie ──►  Store ──► Game ──► Pet ◄── Bubble / GiftBox / FxLayer
                                          │        │
                                          │        ├── motion.py, pet_layout.py, pet_input.py, pet_companion.py
                                          │        ├── hunt.py      (chasse à la souris)
                                          │        ├── screens.py   (géométrie multi-écrans)
                                          │        ├── surfaces.py  (bords de fenêtres praticables)
                                          │        ├── dog.py       (Jazz, le chien visiteur) ◄── dog_sprite.py
                                          │        └── sprite.py    (dessin pixel art) ◄── hats.py
                                          ├── winapi.py             (tout ce qui parle à Windows)
                                          ├── autostart.py          (lancement avec Windows)
                                          └── hotkey.py             (raccourci global Ctrl+Alt+C)
                                   Panel (fenêtre de contrôle) ◄── Game
```

## Modules (`desktopcat/`)

| Module | Rôle | Dépend de Qt ? | Dépend de Windows ? |
|---|---|---|---|
| `store.py` | Sauvegarde JSON (`%APPDATA%/DesktopCat/save.json`), valeurs par défaut, nettoyage d'un fichier abîmé, statistiques par jour. Écriture atomique (`.tmp` puis `os.replace`). Copies de sécurité, copie quotidienne avec restauration automatique, migrations de format. | non | non |
| `game.py` | Règles du jeu : minuterie d'une seconde, cadeaux, chapeaux, concentration, temps d'écran, réglages validés (`SETTING_RULES`). Émet des signaux ; aucune interface. | oui (`QObject`, signaux) | via `winapi` |
| `pet.py` | Le chat : fenêtre transparente, états (idle, walk, nap, sleep, work, wait, drag, fall, jump), souris, bulle, cadeau et orchestration des mouvements. | oui | via `world.py` |
| `motion.py` | Calculs physiques de la marche, des sauts et des chutes, indépendants de Qt et de Windows. | non | non |
| `world.py` | Convertit les fenêtres Windows en surfaces praticables en coordonnées Qt. | non | via `winapi` |
| `pet_layout.py` | Calcule la position du chat, du cadeau et de la bulle dans la zone visible, sans Qt. | non | non |
| `pet_input.py` | Traduit les événements souris et le menu contextuel en actions sur le chat. | oui | non |
| `pet_companion.py` | Réactions expressives aux cadeaux, aux bulles, au sommeil et aux sessions de concentration. | oui | non |
| `dog.py` | Jazz, le chien qui rend visite à Cali : fenêtre transparente sans souris, états away / walk / sit / greet / lie, visite, suivi par Cali et sieste à deux. Sa bulle et ses aboiements (cri de Toller). Son hasard est séparé de celui du chat, et ses phrases d'un troisième (`voice`). | oui | non |
| `dog_sprite.py` | Dessin de Jazz (assis, au trot, couché), même principe que `sprite.py`, sur une grille de 48 × 40. | oui | non |
| `screens.py` | Géométrie multi-écrans (conversion pixels physiques ↔ logiques, sols, chaînes d'écrans collés). Fonctions pures. | non | non |
| `surfaces.py` | Calcule les bords hauts de fenêtres sur lesquels le chat peut marcher, en retirant les parties masquées par les fenêtres au-dessus. Fonctions pures. | non | non |
| `winapi.py` | `ctypes` vers `user32`/`dwmapi`/`kernel32` : liste des fenêtres, fenêtre active, inactivité, plein écran. Sur un autre système, renvoie des valeurs neutres. | non | oui (isolé ici) |
| `sprite.py` | Dessin du chat et du cadeau, case par case, sur une grille. Pelages, poses, yeux, chapeaux. | oui | non |
| `hats.py` | Catalogue des chapeaux, raretés, tirage pondéré. | non | non |
| `hunt.py` | Règles de la chasse à la souris (souris au repos, à portée). Fonctions pures. | non | non |
| `hotkey.py` | Raccourci global Ctrl+Alt+C (`RegisterHotKey` + filtre d'événements natifs de Qt). | oui | oui |
| `phrases.py` | Textes des miaous, aboiements de Jazz et délai aléatoire (le hasard est passé en paramètre). | non | non |
| `widgets.py` | `Bubble` (bulle), `GiftBox` (cadeau), `FxLayer` (cœurs, étoiles, « z »). | oui | non |
| `panel.py` | Fenêtre de contrôle : garde-robe, concentration, statistiques, réglages. | oui | non |
| `log.py` | Journal d'erreurs : fichier tournant, capture des exceptions (dont celles des slots Qt), des messages Qt et des plantages fatals. | oui (messages Qt) | non |
| `autostart.py` | Clé de registre `HKCU\...\Run`. | non | oui |

## Boucles et temps

- **`Game.tick(dt)`** : environ une fois par seconde. Le temps compté est le temps réellement écoulé (horloge monotone),
  plafonné à 5 s par passage : une veille ou un gel de l'appli ne fausse donc ni les statistiques ni la progression des
  cadeaux. Compte l'activité, fait avancer la progression du prochain cadeau, le temps
  d'écran par application, la session de concentration, détecte l'absence (endormissement) et le plein écran.
  Sauvegarde toutes les 30 s.
- **`Pet.step(dt)`** : environ 60 fois par seconde (minuterie de 16 ms, `LOOP_MS`). Quand le chat est caché ou endormi
  parce que l'utilisateur est absent, la minuterie passe à 100 ms (`LOOP_SLOW_MS`, 10 passages par seconde) pour ménager
  la batterie ; la sieste (« nap ») garde le rythme normal. `dt` est plafonné (2,5 fois l'intervalle de la minuterie).
  C'est cette méthode que les tests appellent directement.
- **`Dog.step(dt)`** : appelée juste après `Pet.step` par la minuterie du chat, mais pas par `step` lui-même : les tests du
  chat n'en voient donc jamais Jazz. Les tests de Jazz l'appellent directement.
- **Scan des fenêtres** : toutes les 0,2 s dans `step` (`_refresh_surfaces`), qui reconstruit la liste des surfaces.
- **Animation** : repeinture toutes les 80 ms.

## Coordonnées

Deux systèmes coexistent :

- **physique** : pixels natifs Windows (rectangles de fenêtres, détection du plein écran) ;
- **logique** : pixels de Qt (positions des widgets du chat).

`screens.to_logical` convertit écran par écran à partir de l'origine de l'écran de référence (milieu du bord haut de la
fenêtre). Le chat ne travaille qu'en logique ; seuls `winapi` et `screens` voient du physique.

## Modèle physique du chat

Le chat a une position `(fx, fy)` : `fx` est le bord gauche du sprite, `fy` l'ordonnée des pieds. Il se tient sur une
**surface** : le sol d'un écran (le bas de sa zone utile) ou le bord haut d'une fenêtre. Des sols d'écrans collés
(écart horizontal ≤ 2 px, dénivelé ≤ 80 px) forment une **chaîne** qu'il traverse à pied ; sinon il saute ou tombe.
Si la surface disparaît (fenêtre fermée, réduite, déplacée), il tombe jusqu'à la prochaine.

## Flux de données

1. `Game.tick` met à jour `Store.data` puis émet `changed`.
2. `Pet` et `Panel` écoutent `changed` et se rafraîchissent.
3. Les actions du chat (menu, double-clic) remontent par des signaux (`open_panel`, `start_focus`, ...) reliés dans
   `main.py`, qui est le seul endroit où tout est câblé.

## Tests

`python -m unittest discover -s tests -v`. Les tests utilisent Qt en mode `offscreen`, de faux écrans et un faux bureau.

| Fichier | Couvre |
|---|---|
| `test_logic.py` | Store, règles du jeu, chapeaux, surfaces. |
| `test_screens.py` | Géométrie multi-écrans. |
| `test_features.py` | Comportement du chat et du panneau (états, sauts, plein écran, miaous, bulle...). |
| `test_log.py` | Journal d'erreurs : exceptions, slots Qt, fils, messages Qt, échecs de sauvegarde. |
| `test_gameplay.py` | Chapeaux saisonniers, humeur et croquettes, pauses, chasse à la souris, raccourci. |
| `test_store_backups.py` | Sauvegarde : copies horodatées, copie quotidienne, restauration, migrations de format. |
| `test_autostart.py` | Lancement avec Windows, sur un faux registre (le vrai n'est jamais touché). |
| `test_motion.py` | Trajectoires des sauts et des chutes, marche (sans Qt). |
| `test_pet_layout.py` | Placement visuel du chat, du cadeau et de la bulle (sans Qt). |
| `test_world.py` | Pont entre les fenêtres natives et les surfaces praticables. |
| `test_tools.py` | Outils de build : métadonnées Windows de l'exécutable. |

Les tests sont **indépendants de la machine** : faux écrans (`ScreenInfo`), fausse souris (`FixedCursor`), faux bureau.
Une garde dans `GameTestCase` fait échouer tout test qui lirait les vrais écrans.

Les appels réels à l'API Windows (`winapi.py`) ne sont testés que sous Windows (jobs Windows de la CI) ; les échelles
d'affichage mixtes, le raccourci global et le perchage avec Steam/Discord se valident à la main :
[TEST-MANUEL.md](TEST-MANUEL.md) et `tools/run_test_instance.bat`.

## Points d'extension

- **Nouveau chapeau** : ajouter une entrée dans `HATS` (`hats.py`). Aucun autre fichier à modifier.
- **Nouveau réglage** : valeur par défaut dans `store.DEFAULTS["settings"]`, règle de validation dans
  `game.SETTING_RULES`, contrôle dans `Panel._build_settings`.
- **Changer le format de la sauvegarde** : incrémenter `store.SCHEMA_VERSION` et ajouter dans `store.MIGRATIONS` la
  fonction `{ancienne_version: fonction(dict) -> dict}` qui transforme l'ancien format. Le fichier est copié en
  `save.json.v<N>.bak` avant migration. Ajouter un test dans `tests/test_store_backups.py`.
- **Nouvelle phrase** : `phrases.MEOWS`.
- **Nouvel état du chat** : voir `Pet.step` / `_step_stand` ; penser à la pose correspondante dans `paintEvent`.
