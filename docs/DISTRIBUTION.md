# Distribution (exécutable Windows)

Français · [English](en/DISTRIBUTION.md)

[Retour au README](../README.md)

Desktop Cat est distribué sous forme d'un exécutable unique `DesktopCat.exe`, fabriqué par **PyInstaller** dans
GitHub Actions (`.github/workflows/release.yml`).

## Fabriquer l'exécutable en local

```bash
pip install -r requirements-build.txt
python tools/make_version_file.py
pyinstaller --noconsole --onefile --name DesktopCat --icon assets/desktopcat.ico --version-file build/version_info.txt main.py
```

`requirements-build.txt` fige les versions de PySide6 et de PyInstaller utilisées pour fabriquer l'exe (celles du dernier
build testé) : les relever ensemble, après un build validé. Dependabot propose les montées via `requirements.txt` ;
la CI de tests les valide, puis on reporte la version retenue dans `requirements-build.txt`.

Résultat : `dist/DesktopCat.exe`. `build/`, `dist/` et `*.spec` sont ignorés par Git.
`tools/make_version_file.py` écrit les métadonnées Windows (nom du produit, version tirée de `desktopcat.__version__`,
auteur) visibles dans Propriétés > Détails. Quitter le chat avant de reconstruire : un exe en cours d'exécution ne
peut pas être remplacé (« Accès refusé »).

## Publier une version

1. Mettre à jour `__version__` dans `desktopcat/__init__.py` (ex. `"0.4.2"`).
2. Déplacer le contenu de `[Non publié]` du [CHANGELOG](../CHANGELOG.md) (et de [docs/en/CHANGELOG.md](en/CHANGELOG.md)) sous un nouvel en-tête `[0.4.2] - AAAA-MM-JJ`.
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

Sur une PR qui touche `main.py`, `requirements.txt`, `requirements-build.txt`, `desktopcat/**` ou le workflow, le build tourne **à blanc**
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
  peuvent aussi signaler à tort un exécutable PyInstaller (faux positif fréquent avec `--onefile`). La voie retenue pour y remédier est le Microsoft Store (voir plus bas).
- Le démarrage avec Windows met à jour le chemin enregistré à chaque lancement. Si Windows refuse la modification,
  l'option revient à son état précédent et le panneau affiche un avertissement.
  (À vérifier avec la version empaquetée, voir « Ébauche » ci-dessous.)

## Signature et Microsoft Store

La candidature à SignPath Foundation (signature gratuite pour l'open source) a été **refusée** en octobre 2026 : le
projet n'est pas encore assez connu (peu d'interactions sur le dépôt). Elle pourra être retentée quand il aura plus de
traction.

Voie retenue : le **Microsoft Store**. Les paquets publiés sur le Store sont signés par le Store, ce qui doit lever
l'avertissement SmartScreen et le blocage de Smart App Control (à vérifier sur une machine où Smart App Control est
actif, une fois le paquet disponible). Les Releases GitHub continuent de fournir l'exe non signé.

À faire (rien n'est encore engagé) :
- [ ] Créer un compte développeur Microsoft (Partner Center) et réserver le nom « Desktop Cat ».
- [ ] Étudier le paquet : MSIX à partir de l'exe PyInstaller (ou de `--onedir`), icônes et métadonnées demandées.
- [ ] Automatiser le build du paquet dans `release.yml`, ou fixer une procédure manuelle de soumission.
- [ ] Préparer la fiche du Store (description, captures, politique de confidentialité : aucune donnée transmise, voir
  [SECURITY.md](../SECURITY.md)).
- [ ] Vérifier dans l'environnement du paquet : démarrage avec Windows (clé `Run`), raccourci global, dossier
  `%APPDATA%\DesktopCat` (sauvegarde, journal).
- [ ] Passer la certification, puis tester sur une machine avec Smart App Control actif. S'il bloque encore,
  l'Observateur d'événements (Microsoft > Windows > CodeIntegrity > Operational, événement 3077) nomme le fichier refusé.

## Ébauche — à compléter

- [x] Premières Releases `v0.4.0` et `v0.4.1` publiées (testées avec Python ; l'exe est bloqué par Smart App Control sur la machine de dev).
- [x] Icône de l'exécutable (`assets/desktopcat.ico`, voir `tools/make_icon.py`).
- [x] Numéro de version affiché dans le panneau, l'infobulle de l'icône et les métadonnées de l'exe.
- [ ] Fichier `.spec` versionné au lieu de la ligne de commande (aujourd'hui `*.spec` est dans `.gitignore`, le `DesktopCat.spec` local est un résidu de PyInstaller).
- [ ] Démarrage automatique vérifié avec l'exécutable empaqueté (chemin dans le registre).
- [x] Candidature SignPath : refusée (octobre 2026) ; voie retenue : Microsoft Store (voir ci-dessus). Note SmartScreen / Smart App Control dans le README : faite.
- [x] Versions de build figées (`requirements-build.txt`). Fichier de verrouillage complet avec empreintes : écarté pour l'instant (deux dépendances, un mainteneur).
- [ ] Mise à jour : décider si l'appli prévient d'une nouvelle Release (aujourd'hui, aucun accès réseau — à ne pas casser à la légère, cf. [SECURITY.md](../SECURITY.md)).
