"""Django Missive views."""

from django.conf import settings
from django.db import models
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from ..address_backends import build_address_backends_payload
from ..models import Missive
from ..models.provider import ProviderInfo
from .webhooks import WebhookView, webhook_status_view, webhook_test_view


def system_status_view(request):
    """
    JSON view exposing high-level missive and provider status.

    - Missives: counts by status and type.
    - Providers: installation/configuration status per provider.
    """
    # Missive stats
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

    # Provider stats via ProviderInfo virtual model
    providers_payload = []
    for provider in ProviderInfo.objects.all().order_by("name"):
        provider_data = {
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

        # Get geographic coverage for each supported missive type
        provider_class = provider._get_provider_class()
        if provider_class:
            for missive_type in provider.missive_types_list:
                normalized = missive_type.strip().lower()
                geo_attr = f"{normalized}_geographic_coverage"
                legacy_attr = f"{normalized}_geo"
                geo_value = None

                for cls in provider_class.__mro__:
                    if geo_attr in cls.__dict__:
                        attr_value = cls.__dict__[geo_attr]
                        if not callable(attr_value):
                            geo_value = attr_value
                            break
                    elif hasattr(cls, geo_attr):
                        attr_value = getattr(cls, geo_attr)
                        if not callable(attr_value):
                            geo_value = attr_value
                            break
                    elif legacy_attr in cls.__dict__:
                        attr_value = cls.__dict__[legacy_attr]
                        if not callable(attr_value):
                            geo_value = attr_value
                            break
                    elif hasattr(cls, legacy_attr):
                        attr_value = getattr(cls, legacy_attr)
                        if not callable(attr_value):
                            geo_value = attr_value
                            break

                if geo_value is None:
                    provider_data["geographic_coverage"][missive_type] = "*"
                elif isinstance(geo_value, str):
                    if geo_value == "*":
                        provider_data["geographic_coverage"][missive_type] = "*"
                    else:
                        provider_data["geographic_coverage"][missive_type] = [geo_value]
                elif isinstance(geo_value, (list, tuple)):
                    provider_data["geographic_coverage"][missive_type] = (
                        list(geo_value) if geo_value else "*"
                    )
                else:
                    provider_data["geographic_coverage"][missive_type] = str(geo_value)

        providers_payload.append(provider_data)

    payload = {
        "sandbox_mode": getattr(settings, "MISSIVE_SANDBOX", False),
        "missives": {
            "total": missives_qs.count(),
            "by_status": by_status,
            "by_type": by_type,
        },
        "providers": {
            "count": len(providers_payload),
            "items": providers_payload,
        },
    }

    return JsonResponse(payload, json_dumps_params={"indent": 2})


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


__all__ = [
    "WebhookView",
    "webhook_status_view",
    "webhook_test_view",
    "system_status_view",
    "address_backends_status_view",
]
