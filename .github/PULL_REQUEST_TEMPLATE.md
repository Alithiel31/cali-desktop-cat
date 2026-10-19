## Description

<!-- Que fait cette PR, et pourquoi ? -->

## Checklist

- [ ] `python -m unittest discover -s tests` passe en local (`QT_QPA_PLATFORM=offscreen`)
- [ ] Un test couvre le changement de comportement (ou une raison est donnée ci-dessous)
- [ ] `CHANGELOG.md` mis à jour dans la section `[Non publié]`, si le changement se voit côté utilisateur —
      voir [CONTRIBUTING.md](../CONTRIBUTING.md#ouvrir-une-pull-request)
- [ ] `docs/GAMEPLAY.md` / `docs/ARCHITECTURE.md` mis à jour si une règle ou la structure change, avec leur version anglaise (`docs/en/`)
- [ ] Si le format de sauvegarde change : `SCHEMA_VERSION` incrémenté, migration ajoutée et testée
- [ ] Aucune sauvegarde réelle, journal complet ou capture privée dans le diff

## Contexte additionnel

<!-- Issue liée, captures d'écran, décisions de conception... -->
