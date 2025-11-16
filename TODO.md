# TODO - Django Missive

## Améliorations de qualité de code

### Installation de stubs de type pour Django
- [ ] Installer `django-stubs` pour réduire les erreurs mypy `[import-untyped]`
  - Commande : `pip install django-stubs[compatible-mypy]`
  - Impact attendu : Réduction de ~96 erreurs mypy liées aux imports Django
  - Note : Les stubs permettent à mypy de vérifier les types des appels Django (ORM, QuerySet, etc.)

## Notes

- Les erreurs mypy restantes sont principalement :
  - `[import-untyped]` : Django n'a pas de stubs de type par défaut (normal)
  - `[attr-defined]` : Attributs dynamiques des mixins (attendu dans cette architecture)

