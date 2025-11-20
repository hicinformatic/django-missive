"""Compatibility helpers for python_missive providers."""

from __future__ import annotations

PYTHON_MISSIVE_PROVIDER_PREFIX = "python_missive.providers."
LEGACY_PROVIDER_PREFIX = "missive.providers."


def normalize_provider_path(path: str) -> str:
    """Replace `missive.providers.` prefix with `python_missive.providers.`."""
    if path.startswith(LEGACY_PROVIDER_PREFIX):
        return PYTHON_MISSIVE_PROVIDER_PREFIX + path[len(LEGACY_PROVIDER_PREFIX) :]
    return path
