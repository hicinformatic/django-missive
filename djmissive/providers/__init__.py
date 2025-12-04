"""Compatibility helpers for pymissive providers."""

from __future__ import annotations

PYTHON_MISSIVE_PROVIDER_PREFIX = "pymissive.providers."
LEGACY_PROVIDER_PREFIX = "djmissive.providers."


def normalize_provider_path(path: str) -> str:
    """Replace `djmissive.providers.` prefix with `pymissive.providers.`."""
    if path.startswith(LEGACY_PROVIDER_PREFIX):
        return PYTHON_MISSIVE_PROVIDER_PREFIX + path[len(LEGACY_PROVIDER_PREFIX) :]
    return path
