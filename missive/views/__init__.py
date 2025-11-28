"""Django Missive views."""

from typing import Any, Dict

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from ..address_backends import build_address_backends_payload
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


@require_GET
def address_backends_status_view(request):
    backends_config = getattr(settings, "MISSIVE_ADDRESS_BACKENDS", None)
    payload = build_address_backends_payload(
        backends_config=backends_config,
        operation=request.GET.get("operation", "validate"),
        address_kwargs={
            "address_line1": request.GET.get("address_line1"),
            "address_line2": request.GET.get("address_line2"),
            "address_line3": request.GET.get("address_line3"),
            "city": request.GET.get("city"),
            "postal_code": request.GET.get("postal_code"),
            "state": request.GET.get("state"),
            "country": request.GET.get("country"),
        },
        extra_kwargs={
            "latitude": request.GET.get("latitude"),
            "longitude": request.GET.get("longitude"),
        },
    )
    return JsonResponse(payload, json_dumps_params={"indent": 2})


@require_GET
def _address_autocomplete_view_impl(request):
    """Internal implementation of address autocomplete view."""
    if not getattr(settings, "MISSIVE_ADDRESS_VIEW_ENABLE", False):
        return JsonResponse(
            {"error": "Address autocomplete view is disabled"}, status=403
        )

    try:
        from python_missive.helpers import search_addresses as pm_search_addresses
    except ImportError:
        return JsonResponse(
            {"error": "python-missive is not installed", "results": [], "total": 0},
            status=503,
        )

    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse({"results": [], "total": 0, "error": "Query is required"})

    backends_config = getattr(settings, "MISSIVE_ADDRESS_BACKENDS", None)
    if not backends_config:
        return JsonResponse(
            {
                "results": [],
                "total": 0,
                "error": "No address backends configured",
            },
            status=503,
        )

    country = request.GET.get("country")
    backend = request.GET.get("backend")
    limit = int(request.GET.get("limit", 10))
    min_confidence = request.GET.get("min_confidence")
    min_confidence_float = float(min_confidence) if min_confidence else None

    try:
        search_result = pm_search_addresses(
            backends_config=backends_config,
            query=query,
            country=country,
            backend=backend,
            limit=limit,
            min_confidence=min_confidence_float,
        )
    except Exception as exc:  # pragma: no cover - defensive
        return JsonResponse(
            {
                "results": [],
                "total": 0,
                "error": str(exc),
                "errors": [str(exc)],
            },
            status=500,
        )

    return JsonResponse(search_result)


def address_autocomplete_view(request):
    """API view for address autocomplete.

    This view provides address search functionality for autocomplete widgets.
    It can be enabled/disabled via MISSIVE_ADDRESS_VIEW_ENABLE setting and
    optionally requires authentication via MISSIVE_ADDRESS_VIEW_AUTH_ENABLE.

    Query parameters:
        q (required): Search query string
        country (optional): ISO country code to filter results
        backend (optional): Specific backend name to use
        limit (optional): Maximum number of results (default: 10)
        min_confidence (optional): Minimum confidence threshold (0.0-1.0)

    Returns:
        JSON response with search results:
        {
            "results": [...],
            "total": int,
            "backend_used": str,
            "error": str (optional),
            "errors": list (optional)
        }
    """
    view_func = _address_autocomplete_view_impl
    if getattr(settings, "MISSIVE_ADDRESS_VIEW_AUTH_ENABLE", False):
        view_func = login_required(view_func)
    return view_func(request)


__all__ = [
    "WebhookView",
    "webhook_status_view",
    "webhook_test_view",
    "system_status_view",
    "address_backends_status_view",
    "address_autocomplete_view",
]
