# Contribuer

Merci de ton intérêt pour ce projet. Desktop Cat est un compagnon de bureau Windows (PySide6 / Qt 6) ; toute contribution qui corrige un bug, améliore la fiabilité, le comportement du chat ou la documentation est bienvenue.

## Avant de commencer

- Ouvrir une issue pour discuter du changement envisagé, sauf correction triviale (typo, lien cassé).
- Consulter la [feuille de route](./docs/ROADMAP.md) : le sujet y est peut-être déjà classé, avec une décision à prendre (c'est le cas des croquettes, par exemple).
- Vérifier que le changement n'est pas déjà en cours dans la section `[Non publié]` de [`CHANGELOG.md`](./CHANGELOG.md).

## Environnement de développement

```bash
git clone https://github.com/Alithiel31/cali-desktop-cat.git
cd cali-desktop-cat
python -m venv .venv
.venv\Scripts\activate          # Windows ; source .venv/bin/activate ailleurs
pip install -r requirements.txt
python main.py
```

Python **3.12 ou 3.13** (la CI teste les deux ; 3.10 plante avec PySide6 6.12).

## Tester

```bash
python -m unittest discover -s tests -v
```

Les tests tournent aussi hors Windows : Qt en mode `offscreen`, faux écrans, fausse souris, faux bureau. Sous Linux, il faut les bibliothèques système de Qt (`libegl1 libgl1 libxkbcommon0 libdbus-1-3 libfontconfig1 libglib2.0-0`).

**Règle d'or : un test ne doit jamais dépendre de ta machine.** Une garde dans `GameTestCase` fait échouer tout test qui lirait les vrais écrans. Utiliser `ScreenInfo` et `FixedCursor` (voir [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md#tests)).

Tester à la main **sans toucher à ta vraie sauvegarde** : `tools\run_test_instance.bat`.

## Reproduire la CI en local

| Job | Commande |
|---|---|
| `tests` (`ci.yml`) | `set QT_QPA_PLATFORM=offscreen` puis `python -m unittest discover -s tests -v` |
| `build-windows` (`release.yml`) | `pip install pyinstaller` puis `pyinstaller --noconsole --onefile --name DesktopCat main.py` |

Le build de l'exécutable se déclenche sur une PR qui touche `main.py`, `requirements.txt`, `desktopcat/**` ou le workflow lui-même.

## Ouvrir une Pull Request

1. Créer une branche depuis `main` (`git checkout -b fix/mon-changement`).
2. Committer avec un message clair, au format `type: description` (`fix:`, `feat:`, `docs:`, `ci:`, `test:`, `chore:`).
3. Ajouter ou adapter un test pour tout changement de comportement (un bug corrigé = un test qui l'aurait attrapé).
4. Mettre à jour [`CHANGELOG.md`](./CHANGELOG.md) dans `[Non publié]` (`Added`, `Changed`, `Fixed`, `Security`) si le changement se voit côté utilisateur.
5. Si une règle du jeu change, mettre à jour [docs/GAMEPLAY.md](./docs/GAMEPLAY.md) ; si la structure change, [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md).
6. Vérifier que le job `tests` passe, puis ouvrir la PR contre `main`.

## Recettes courantes

Voir « Points d'extension » dans [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md#points-dextension) : nouveau chapeau, nouveau réglage, changement du format de sauvegarde (version + migration), nouvelle phrase, nouvel état du chat.

## Publier une version

Voir [docs/DISTRIBUTION.md](./docs/DISTRIBUTION.md).

## Signaler un problème

Ouvrir une issue depuis l'onglet Issues. Joindre les dernières lignes de `desktopcat.log` — voir [docs/TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md#signaler-un-bug).

## Secrets et données personnelles

Ne jamais committer une sauvegarde réelle (`save.json`), un journal complet ou une capture montrant des fenêtres privées. Les `*.png` sont ignorés par `.gitignore` ; `tools/out/` aussi.
