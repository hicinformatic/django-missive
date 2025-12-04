"""Utilities for resolving provider classes and paths."""

from typing import Any, Iterable, Optional

from django.conf import settings

from .providers import normalize_provider_path


def resolve_provider_path(provider_name: str) -> Optional[str]:
    """Return the fully qualified provider path for a given short name."""
    if not provider_name:
        return None

    providers_config = getattr(settings, "MISSIVE_PROVIDERS", {}) or {}
    provider_path = _match_provider_in_config(provider_name, providers_config)
    if not provider_path:
        provider_path = _fallback_provider_path(provider_name)

    return normalize_provider_path(provider_path) if provider_path else None


def _match_provider_in_config(provider_name: str, providers_config) -> Optional[str]:
    """Search provider name in MISSIVE_PROVIDERS config (dict or list)."""
    name_lower = provider_name.lower()
    if isinstance(providers_config, dict):
        iterables: Iterable[Iterable[Any]] = providers_config.values()
    elif isinstance(providers_config, (list, tuple, set)):
        iterables = [providers_config]
    else:
        return None

    for providers_list in iterables:
        for candidate in providers_list:
            candidate_str = str(candidate)
            if name_lower in candidate_str.lower():
                return candidate_str
    return None


def _fallback_provider_path(provider_name: str) -> Optional[str]:
    """Construct a provider path when it is missing from configuration."""
    if not provider_name:
        return None

    name_lower = provider_name.lower()
    if name_lower == "django_email":
        return "pymissive.providers.django_email.DjangoEmailProvider"
    return (
        f"pymissive.providers.{name_lower}.{provider_name.capitalize()}Provider"
    )
