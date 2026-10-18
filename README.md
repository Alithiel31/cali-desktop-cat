# Desktop Cat 🐱

Un chat écaille qui vit sur ton bureau Windows : il se promène, se perche sur le bord des fenêtres,
tombe quand elles disparaissent, saute d'une fenêtre à l'autre, dort quand tu es absent,
miaule de temps en temps dans une bulle, te rapporte des cadeaux (chapeaux de 6 raretés) et travaille avec toi
pendant tes sessions de concentration. Il se promène sur tous tes écrans.

## Lancer
    pip install -r requirements.txt
    python main.py

## Tests
    python -m unittest discover -s tests -v
Tournent aussi hors Windows (Qt en mode `offscreen`, faux bureau et faux écrans).

Icône dans la zone de notification : panneau, concentration 25 min, cacher le chat, quitter.
Double-clic sur le chat = panneau ; clic droit = menu ; on peut l'attraper et le lâcher.

## Panneau
Garde-robe (porter, vendre les doublons), Concentration, Statistiques (7 jours + applis du jour), Réglages
(dont « Il miaule de temps en temps »).

## Plusieurs écrans
Un sol par écran (le bas de sa zone utile, barre des tâches exclue). Des écrans collés dont les bas sont à moins
de 80 px d'écart se traversent à pied ; sinon il saute ou tombe de l'un à l'autre. Il se perche sur les fenêtres
de tous les écrans, même à échelles d'affichage différentes. Une appli plein écran ne cache le chat que sur son
écran. Brancher ou débrancher un écran est géré à chaud.

## Concentration
Une session de moins de 10 min ne rapporte ni cadeau ni croquettes. Elle survit à un redémarrage de l'appli
(si elle est finie entre-temps, elle est abandonnée sans récompense).

## Limites connues
- Écrit sans accès à Windows : la logique (dont le multi-écrans, avec de faux écrans) est testée hors écran,
  mais l'API Windows réelle et les échelles d'affichage mixtes restent à valider chez toi.
- Une fenêtre à cheval sur deux écrans d'échelles différentes est convertie avec l'échelle d'un seul des deux.
- Sauvegarde : `%APPDATA%/DesktopCat/save.json`.

## Exécutable
    pip install pyinstaller
    pyinstaller --noconsole --onefile --name DesktopCat main.py

## Structure du projet
    main.py          point d'entrée
    desktopcat/      le code de l'appli (voir docs/ARCHITECTURE.md)
    tests/           tests unitaires (Qt hors écran)
    docs/            architecture et règles du jeu
    tools/           outils de développement (captures du panneau, lanceur de test, anciens prototypes)

## Documentation
- [Architecture](docs/ARCHITECTURE.md) : modules, boucles, coordonnées, points d'extension.
- [Règles du jeu](docs/GAMEPLAY.md) : cadeaux, raretés, concentration, statistiques.
- [Outils](tools/README.md) : lanceur de test isolé, captures du panneau.

## Développement
- Tester sans toucher à ta vraie sauvegarde : `tools\run_test_instance.bat`.
- Captures du panneau : `python tools/preview_panel.py` (écrites dans `tools/out/`).

## Licence
MIT, voir [LICENSE](LICENSE).
