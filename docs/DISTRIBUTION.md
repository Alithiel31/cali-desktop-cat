# Distribution (exécutable Windows)

[Retour au README](../README.md)

Desktop Cat est distribué sous forme d'un exécutable unique `DesktopCat.exe`, fabriqué par **PyInstaller** dans
GitHub Actions (`.github/workflows/release.yml`).

## Fabriquer l'exécutable en local

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --name DesktopCat main.py
```

Résultat : `dist/DesktopCat.exe`. `build/`, `dist/` et `*.spec` sont ignorés par Git.

## Publier une version

1. Mettre à jour `__version__` dans `desktopcat/__init__.py` (ex. `"0.4.0"`).
2. Déplacer le contenu de `[Non publié]` du [CHANGELOG](../CHANGELOG.md) sous un nouvel en-tête `[0.4.0] - AAAA-MM-JJ`.
3. Committer sur `main`, la CI doit être verte.
4. Poser et pousser le tag :

   ```bash
   git tag v0.4.0
   git push --tags
   ```

Le workflow `release.yml` :

| Étape | Ce qu'elle fait |
|---|---|
| Vérifier tag/version | Échoue si le tag (`v0.4.0`) ne correspond pas à `desktopcat.__version__` (`0.4.0`). |
| Tests | Rejoue toute la suite avant de packager. |
| Build | `pyinstaller --noconsole --onefile --name DesktopCat main.py` sur `windows-latest`. |
| Empreinte | Écrit `DesktopCat.exe.sha256`. |
| Publication | Job séparé, seul à avoir `contents: write` : `gh release create` avec l'exe, l'empreinte et des notes générées. |

Sur une PR qui touche `main.py`, `requirements.txt`, `desktopcat/**` ou le workflow, le build tourne **à blanc**
(sans publication) pour attraper une régression de packaging avant le merge.

## Vérifier un téléchargement

```powershell
(Get-FileHash .\DesktopCat.exe -Algorithm SHA256).Hash.ToLower()
```

Comparer avec le contenu de `DesktopCat.exe.sha256` publié dans la même Release.

## Limites connues

- **L'exécutable n'est pas signé** : Windows SmartScreen affiche « Windows a protégé votre ordinateur ». Cliquer sur
  *Informations complémentaires* puis *Exécuter quand même*. Des antivirus peuvent aussi signaler à tort un exécutable
  PyInstaller (faux positif fréquent avec `--onefile`).
- Le démarrage avec Windows met à jour le chemin enregistré à chaque lancement. Si Windows refuse la modification,
  l'option revient à son état précédent et le panneau affiche un avertissement.
  (À vérifier avec la version empaquetée, voir ci-dessous.)

## Ébauche — à compléter

- [ ] Première Release `v0.4.0` publiée et testée sur une machine propre (sans Python).
- [ ] Icône de l'exécutable et numéro de version affiché dans le panneau (niveau 3 de la [feuille de route](./ROADMAP.md)).
- [ ] Fichier `.spec` versionné au lieu de la ligne de commande.
- [ ] Démarrage automatique vérifié avec l'exécutable empaqueté (chemin dans le registre).
- [ ] Signature de code, ou à défaut une note dans le README sur SmartScreen.
- [ ] Dépendances figées (`pyproject.toml` + fichier de verrouillage) pour des builds reproductibles.
- [ ] Mise à jour : décider si l'appli prévient d'une nouvelle Release (aujourd'hui, aucun accès réseau — à ne pas casser à la légère, cf. [SECURITY.md](../SECURITY.md)).
