# Guide de reprise

Français · [English](en/HANDOVER-GUIDE.md)

[Retour au README](../README.md)

Desktop Cat a un seul mainteneur réel (**Jacques Duchamplecheval**, alias GitHub `Alithiel31`). Ce document existe
pour qu'une autre personne — ou Jacques lui-même après une longue coupure — puisse reprendre le projet sans devoir
tout reconstituer. Il pointe vers la documentation existante plutôt que de la dupliquer.

Le projet est volontairement léger : application locale, pas de serveur, pas de base de données, pas de compte tiers
obligatoire. La reprise est donc bien plus simple que celle d'un service hébergé.

---

## 1. Comprendre le projet — ordre de lecture recommandé

1. [README.md](../README.md) — ce que fait le chat, comment le lancer
2. [docs/GAMEPLAY.md](./GAMEPLAY.md) — les règles du jeu (cadeaux, raretés, concentration)
3. [docs/ARCHITECTURE.md](./ARCHITECTURE.md) — modules, boucles, coordonnées, points d'extension
4. [docs/DEVELOPPEMENT.md](./DEVELOPPEMENT.md) — lancer, tester, conventions
5. [docs/DISTRIBUTION.md](./DISTRIBUTION.md) — fabriquer et publier l'exécutable
6. [docs/ROADMAP.md](./ROADMAP.md) — ce qui est fait, ce qui reste, dans l'ordre conseillé
7. [docs/TEST-MANUEL.md](./TEST-MANUEL.md) — la checklist à passer sur un vrai Windows avant une Release
8. [docs/TROUBLESHOOTING.md](./TROUBLESHOOTING.md), [SECURITY.md](../SECURITY.md), [CONTRIBUTING.md](../CONTRIBUTING.md)
9. [docs/VEILLE-DEPENDANCES.md](./VEILLE-DEPENDANCES.md), [docs/ACCESSIBILITE.md](./ACCESSIBILITE.md)
10. [CHANGELOG.md](../CHANGELOG.md) — historique des décisions

La documentation existe aussi en anglais (`docs/en/`, `README.en.md`) : les deux versions vont ensemble.

---

## 2. Ce qui existe, et où

| Composant | Où | Comment y accéder |
|---|---|---|
| Code source | GitHub, [`Alithiel31/cali-desktop-cat`](https://github.com/Alithiel31/cali-desktop-cat) (public) | Compte GitHub du mainteneur |
| Intégration continue | `.github/workflows/ci.yml` | Se déclenche sur push `main` et PR |
| Releases | `.github/workflows/release.yml` | Se déclenche sur tag `v*` ; aucun secret requis (`GITHUB_TOKEN` suffit) |
| Données utilisateur | `%APPDATA%\DesktopCat\` sur le poste de chaque utilisateur | Locales, jamais centralisées |

Pas d'hébergement, pas de domaine, pas de base de données, pas de service tiers : il n'y a rien à « garder en
marche » côté serveur.

---

## 3. Secrets et accès nécessaires pour agir

Aucun secret réel n'est nécessaire au fonctionnement du projet ni stocké dans le dépôt.

- **Accès administrateur au dépôt GitHub** (réglages des branches, Releases, Dependabot).
- Le workflow de release n'utilise que le `GITHUB_TOKEN` fourni automatiquement.

La signature de code (SignPath Foundation) est en préparation (voir [DISTRIBUTION.md](./DISTRIBUTION.md)). Une fois le
projet accepté, le secret `SIGNPATH_API_TOKEN` et la variable `SIGNPATH_ORGANIZATION_ID` du dépôt, ainsi que le compte
SignPath (qui approuve chaque Release), deviendront les éléments **critiques** de cette liste — à consigner ici à ce
moment-là.

---

## 4. Remettre le projet en marche à partir de zéro

1. Cloner le dépôt, créer un environnement Python 3.12 ou 3.13, `pip install -r requirements.txt`.
2. `python -m unittest discover -s tests` — tout doit passer.
3. `python main.py` sur une machine Windows pour valider à la main (de préférence via `tools\run_test_instance.bat`,
   puis la checklist de [TEST-MANUEL.md](./TEST-MANUEL.md)).
4. Pour publier : voir [DISTRIBUTION.md](./DISTRIBUTION.md).

---

## 5. Risques connus à garder en tête

- **Mainteneur unique** — ce document réduit le risque mais ne le supprime pas.
- **Écrit sans accès à Windows au départ** : l'API Windows réelle (`winapi.py`) et les échelles d'affichage mixtes
  ne sont validées qu'à la main (voir le README, « Limites connues »).
- **Dépendance à PySide6/Qt** : une montée de version peut changer le rendu ou casser sur certaines versions de Python
  (déjà arrivé avec Python 3.10). Voir [VEILLE-DEPENDANCES.md](./VEILLE-DEPENDANCES.md).
- **Format de sauvegarde** : toute évolution passe par `SCHEMA_VERSION` + une migration (voir
  [ARCHITECTURE.md](./ARCHITECTURE.md#points-dextension)) ; oublier la migration, c'est perdre la progression des
  utilisateurs.

---

## À compléter par le mainteneur

Ces champs sont volontairement laissés vides — ils touchent à des informations personnelles qui n'ont pas leur place
dans un dépôt public :

- [ ] Où est conservé le compte GitHub (gestionnaire de mots de passe, double authentification) et qui d'autre y a accès en cas d'urgence
- [ ] Personne(s) de confiance à contacter en cas d'indisponibilité prolongée du mainteneur
- [ ] Où sont les sauvegardes locales du dossier de travail (autre que GitHub), s'il y en a
