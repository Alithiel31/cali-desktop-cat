# Sécurité

## Signaler une vulnérabilité

Merci de ne **pas** ouvrir d'issue publique pour signaler une faille de sécurité — une issue GitHub classique l'expose à tout le monde avant qu'un correctif n'existe.

Deux façons de signaler, dans l'ordre de préférence :

1. **[Signaler une vulnérabilité](https://github.com/Alithiel31/cali-desktop-cat/security/advisories/new)** via l'onglet Security du dépôt (GitHub Security Advisories) — le rapport reste privé entre toi et le mainteneur.
2. Par courriel à [contact@alithiel31.dev](mailto:contact@alithiel31.dev), avec `SECURITY` dans l'objet, et si possible : le composant concerné, les étapes de reproduction et l'impact envisagé.

### Ce qu'on peut promettre

- Accusé de réception sous **72 heures**.
- Le projet est maintenu par une seule personne, sur son temps libre : pas de SLA formel au-delà de l'accusé de réception, mais une faille confirmée à impact réel passe devant tout le reste.
- Crédit dans le [`CHANGELOG.md`](./CHANGELOG.md) une fois le correctif publié, sauf préférence contraire.
- Pas de programme de bug bounty — c'est un projet personnel.

## Ce qui est exposé (modèle de menace)

Desktop Cat est une application **locale** : aucun serveur, aucun compte, aucune communication réseau. Les surfaces à considérer sont donc différentes d'un service web :

| Surface | Détail |
|---|---|
| Données locales | `%APPDATA%\DesktopCat\` : sauvegarde JSON, journal. Les statistiques contiennent le **nom des exécutables** des fenêtres actives (40 par jour, 60 jours), sauf si le suivi est coupé dans les Réglages. « Effacer mes statistiques » les retire aussi des copies de sécurité lisibles. Rien n'est envoyé nulle part. |
| Appels Windows | `winapi.py` lit la liste des fenêtres, la fenêtre active et l'inactivité via `ctypes`. Lecture seule. |
| Registre | Une seule valeur écrite : `HKCU\Software\Microsoft\Windows\CurrentVersion\Run\DesktopCat` (démarrage avec Windows, désactivable). |
| Fichier de sauvegarde | Lu et nettoyé au démarrage (`store.py`) : un fichier abîmé ou malveillant est écarté, jamais exécuté. |
| Exécutable distribué | `DesktopCat.exe` (PyInstaller) publié dans les Releases, avec son empreinte SHA256. **Non signé** : Windows SmartScreen affichera un avertissement. |

## Périmètre

Dans le périmètre : le code de `desktopcat/` et `main.py`, les workflows GitHub Actions (`.github/workflows/`, en particulier `release.yml` qui produit l'exécutable), l'exécutable publié.

Hors périmètre : une faille de PySide6/Qt, de Python ou de PyInstaller eux-mêmes (à signaler en amont), un accès déjà privilégié à la machine de l'utilisateur, l'ingénierie sociale.

## Ce qui est déjà en place

- **Pas de réseau** : aucune requête sortante dans le code de l'application.
- **Empreinte SHA256** publiée avec chaque exécutable (`DesktopCat.exe.sha256`).
- **Tests avant de packager** : `release.yml` rejoue la suite de tests avant de construire l'exécutable ; seul le job de publication a le droit d'écriture (`contents: write`).
- **Tag et version alignés** : la Release échoue si le tag ne correspond pas à `desktopcat.__version__`.

## Ébauche — à compléter

- [ ] Activer Dependabot et les alertes de sécurité du dépôt (voir [`.github/dependabot.yml`](./.github/dependabot.yml)).
- [ ] Ajouter un scan de secrets (gitleaks) et CodeQL (Python) en CI, comme sur QcWeather.
- [ ] Signer l'exécutable (certificat de signature de code) — aujourd'hui non signé.
- [ ] Épingler les actions GitHub par SHA une fois le pipeline de release stabilisé.

## Versions supportées

Seule la dernière version publiée (et `main`) reçoit des correctifs.
