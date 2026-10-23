# Accessibilité

Français · [English](en/ACCESSIBILITY.md)

[Retour au README](../README.md)

> **Ébauche.** Ce document est un squelette : Desktop Cat est une application de bureau Qt, dont l'accessibilité n'a
> pas encore été auditée. Il se remplira au fur et à mesure. Il existe pour qu'un futur repreneur n'ait pas à tout
> réinvestiguer de zéro.

---

## Ce qui est déjà en place

| Quoi | Où | État |
|---|---|---|
| Bulle de miaou lisible quel que soit le thème Windows | `widgets.py` (`Bubble`) | ✅ Fond dessiné, texte forcé foncé, taille liée à l'échelle du chat |
| Taille du chat réglable (3 à 6 px par « pixel ») | Panneau, Réglages | ✅ |
| Miaous désactivables | Panneau, Réglages (« Il miaule de temps en temps ») | ✅ |
| Notifications désactivables | Panneau, Réglages | ✅ |
| Info-bulles sur certains contrôles | `panel.py` | ✅ Partiel |
| Raccourci clavier global **Ctrl+Alt+C** (afficher / cacher le chat), désactivable | `hotkey.py` | ✅ |
| Chasse à la souris et pause Pomodoro désactivables | Panneau, Réglages | ✅ |
| Visites de Jazz désactivables | Panneau, Réglages (« Jazz rend visite à Cali ») | ✅ |

## Ce qui reste à vérifier

- [ ] **Navigation clavier du panneau** : ordre de tabulation, focus visible, toutes les actions atteignables sans souris.
- [ ] **Chat et menu contextuel** : le chat se pilote surtout à la souris (double-clic, clic droit, glisser-déposer) ;
      les mêmes actions sont dans le menu de l'icône de la zone de notification, et Ctrl+Alt+C affiche ou cache le chat — à confirmer comme équivalent clavier suffisant.
- [ ] **Lecteurs d'écran (NVDA, Narrateur)** : noms accessibles des widgets Qt du panneau (`setAccessibleName`
      n'est utilisé nulle part aujourd'hui).
- [ ] **Contraste** du panneau en thème clair et sombre Windows (la bulle est déjà traitée ; le panneau ne l'est pas forcément).
- [ ] **Taille du texte** indépendante de la taille du chat (point de la [feuille de route](./ROADMAP.md), niveau 4).
- [ ] **Mouvement** : option pour réduire les animations (équivalent de `prefers-reduced-motion`) et pour couper les
      effets de particules (« z », cœurs).
- [ ] **Heures de silence** : pas de miaou ni de notification à certaines heures (feuille de route, niveau 4).
- [ ] **Mode contraste élevé de Windows** : comportement du panneau et de la bulle.
- [ ] **Police emoji de secours** si Segoe UI Emoji manque (feuille de route, niveau 4).
- [ ] **Mise à l'échelle Windows (125 %, 150 %...)** : lisibilité du panneau.

## Ce qui est, par nature, hors de portée des outils automatiques

À consigner ici une fois l'audit commencé : le rendu pixel art, la physique du chat et les fenêtres transparentes
passent à côté de la plupart des outils d'audit.

## Script de vérification manuelle

À rédiger : un parcours court à rejouer à chaque Release (navigation clavier du panneau, NVDA/Narrateur,
thème sombre, contraste élevé, échelle 150 %).

- [ ] Rédiger le script
- [ ] L'exécuter une première fois et noter les écarts ci-dessus
