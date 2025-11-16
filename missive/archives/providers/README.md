Archived legacy providers
=========================

This directory preserves the old Django-native provider implementations.
The project now relies on `python-missive` providers instead.

- Do not import from `missive.providers.*` anymore.
- Use dynamic loading via `python_missive.providers.load_provider_class` with `MISSIVE_PROVIDERS` settings.


