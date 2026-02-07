"""Django Missive views."""

from typing import Any, Dict

from django.conf import settings
from django.db import models
from django.http import JsonResponse

from ..models import Missive
from ..models.provider import ProviderInfo
from .webhooks import WebhookView, webhook_status_view, webhook_test_view


def system_status_view(request):
    """JSON view exposing high-level missive and provider status."""
    missives_qs, missive_stats = _collect_missive_stats()
    providers_payload = _build_provider_status()

    payload = {
        "sandbox_mode": getattr(settings, "MISSIVE_SANDBOX", False),
        "missives": missive_stats,
        "providers": {"count": len(providers_payload), "items": providers_payload},
    }

    return JsonResponse(payload, json_dumps_params={"indent": 2})


def _collect_missive_stats():
    missives_qs = Missive.objects.all()
    status_counts = (
        missives_qs.values_list("status")
        .order_by("status")
        .annotate(count=models.Count("status"))
    )
    by_status = {status: count for (status, count) in status_counts}

    type_counts = (
        missives_qs.values_list("missive_type")
        .order_by("missive_type")
        .annotate(count=models.Count("missive_type"))
    )
    by_type = {mt: count for (mt, count) in type_counts}

    return missives_qs, {
        "total": missives_qs.count(),
        "by_status": by_status,
        "by_type": by_type,
    }


def _build_provider_status():
    items = []
    for provider in ProviderInfo.objects.all().order_by("name"):
        items.append(_serialize_provider(provider))
    return items


def _serialize_provider(provider: ProviderInfo) -> Dict[str, Any]:
    provider_data: Dict[str, Any] = {
        "name": provider.name,
        "missive_types": provider.missive_types_list,
        "status": provider.status,
        "status_display": provider.status_display,
        "is_installed": provider.is_installed,
        "is_configured": provider.is_configured,
        "required_packages": provider.required_packages,
        "required_config_keys": provider.required_config_keys,
        "geographic_coverage": {},
    }

    provider_class = provider._get_provider_class()
    if provider_class:
        for missive_type in provider.missive_types_list:
            coverage = _resolve_provider_geo(provider_class, missive_type)
            provider_data["geographic_coverage"][missive_type] = _format_geo_value(
                coverage
            )
    else:
        for missive_type in provider.missive_types_list:
            provider_data["geographic_coverage"][missive_type] = "*"
    return provider_data


def _resolve_provider_geo(provider_class, missive_type: str):
    normalized = missive_type.strip().lower()
    candidates = [f"{normalized}_geographic_coverage", f"{normalized}_geo"]
    for attr in candidates:
        for cls in provider_class.__mro__:
            if hasattr(cls, "__dict__") and attr in cls.__dict__:
                value = cls.__dict__[attr]
                if not callable(value):
                    return value
            if hasattr(cls, attr):
                value = getattr(cls, attr)
                if not callable(value):
                    return value
    return None


def _format_geo_value(value):
    if value is None:
        return "*"
    if isinstance(value, str):
        return "*" if value == "*" else [value]
    if isinstance(value, (list, tuple)):
        return list(value) if value else "*"
    return str(value)


__all__ = [
    "WebhookView",
    "webhook_status_view",
    "webhook_test_view",
    "system_status_view",
]
