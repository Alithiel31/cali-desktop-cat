# Distribution (exécutable Windows)

Français · [English](en/DISTRIBUTION.md)

[Retour au README](../README.md)

Desktop Cat est distribué sous forme d'un exécutable unique `DesktopCat.exe`, fabriqué par **PyInstaller** dans
GitHub Actions (`.github/workflows/release.yml`).

## Fabriquer l'exécutable en local

```bash
pip install pyinstaller
python tools/make_version_file.py
pyinstaller --noconsole --onefile --name DesktopCat --icon assets/desktopcat.ico --version-file build/version_info.txt main.py
```

Résultat : `dist/DesktopCat.exe`. `build/`, `dist/` et `*.spec` sont ignorés par Git.
`tools/make_version_file.py` écrit les métadonnées Windows (nom du produit, version tirée de `desktopcat.__version__`,
auteur) visibles dans Propriétés > Détails. Quitter le chat avant de reconstruire : un exe en cours d'exécution ne
peut pas être remplacé (« Accès refusé »).

## Publier une version

1. Mettre à jour `__version__` dans `desktopcat/__init__.py` (ex. `"0.4.2"`).
2. Déplacer le contenu de `[Non publié]` du [CHANGELOG](../CHANGELOG.md) (et de [CHANGELOG.en.md](../CHANGELOG.en.md)) sous un nouvel en-tête `[0.4.2] - AAAA-MM-JJ`.
3. Committer sur `main`, la CI doit être verte.
4. Poser et pousser le tag :

   ```bash
   git tag v0.4.2
   git push --tags
   ```

Le workflow `release.yml` :

| Étape | Ce qu'elle fait |
|---|---|
| Vérifier tag/version | Échoue si le tag (`v0.4.2`) ne correspond pas à `desktopcat.__version__` (`0.4.2`). |
| Tests | Rejoue toute la suite avant de packager. |
| Métadonnées | `tools/make_version_file.py` -> `build/version_info.txt`. |
| Build | `pyinstaller --noconsole --onefile --name DesktopCat --icon assets/desktopcat.ico --version-file build/version_info.txt main.py` sur `windows-latest`. |
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
  *Informations complémentaires* puis *Exécuter quand même*. **Smart App Control** (Windows 11), s'il est actif, le
  bloque sans recours (« bloqué par la stratégie Device Guard »), y compris un exe construit en local. Des antivirus
  peuvent aussi signaler à tort un exécutable PyInstaller (faux positif fréquent avec `--onefile`).
- Le démarrage avec Windows met à jour le chemin enregistré à chaque lancement. Si Windows refuse la modification,
  l'option revient à son état précédent et le panneau affiche un avertissement.
  (À vérifier avec la version empaquetée, voir « Ébauche » ci-dessous.)

## Signature (SignPath Foundation)

Signature gratuite pour les projets open source : le certificat est au nom de SignPath Foundation (c'est l'éditeur
affiché par Windows), qui a déjà une réputation auprès de SmartScreen et Smart App Control.

Conditions remplies (voir <https://signpath.org/terms>) : licence MIT, aucun code propriétaire, projet publié
(v0.4.0, puis v0.4.1), fonctionnement décrit dans le README, aucune donnée transmise, désinstallation documentée, section
**Code signing policy** dans le README, builds faits par GitHub Actions depuis le dépôt, nom et version du produit
dans les métadonnées de l'exe (`tools/make_version_file.py`).

Étapes :
1. 2FA activée sur GitHub (et sur SignPath à la création du compte).
2. Candidature sur <https://signpath.org/apply> : dépôt, Release la plus récente (v0.4.1), licence, lien vers la Code signing policy.
3. Une fois accepté : créer le secret `SIGNPATH_API_TOKEN` et la variable `SIGNPATH_ORGANIZATION_ID` dans le dépôt,
   puis décommenter le bloc « Signature » de `release.yml` (vérifier les noms de projet et de politique).
4. À chaque Release : approuver la demande de signature sur signpath.io.
5. Vérifier sur une machine avec Smart App Control actif. S'il bloque encore (DLL Qt non signées extraites par
   `--onefile`), l'Observateur d'événements (Microsoft > Windows > CodeIntegrity > Operational, événement 3077)
   nomme le fichier refusé ; envisager alors `--onedir`.

## Ébauche — à compléter

- [x] Premières Releases `v0.4.0` et `v0.4.1` publiées (testées avec Python ; l'exe est bloqué par Smart App Control sur la machine de dev).
- [x] Icône de l'exécutable (`assets/desktopcat.ico`, voir `tools/make_icon.py`).
- [x] Numéro de version affiché dans le panneau, l'infobulle de l'icône et les métadonnées de l'exe.
- [ ] Fichier `.spec` versionné au lieu de la ligne de commande (aujourd'hui `*.spec` est dans `.gitignore`, le `DesktopCat.spec` local est un résidu de PyInstaller).
- [ ] Démarrage automatique vérifié avec l'exécutable empaqueté (chemin dans le registre).
- [ ] Signature de code : candidature SignPath (voir ci-dessus). Note SmartScreen / Smart App Control dans le README : faite.
- [ ] Dépendances figées (`pyproject.toml` + fichier de verrouillage) pour des builds reproductibles.
- [ ] Mise à jour : décider si l'appli prévient d'une nouvelle Release (aujourd'hui, aucun accès réseau — à ne pas casser à la légère, cf. [SECURITY.md](../SECURITY.md)).
