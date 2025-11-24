"""Django Missive views."""

from django.conf import settings
from django.db import models
from django.http import JsonResponse

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
    geo_attr_map = {
        "EMAIL": "email_geo",
        "SMS": "sms_geo",
        "POSTAL": "postal_geo",
        "POSTAL_REGISTERED": "postal_geo",
        "LRE": "lre_geo",
        "RCS": "rcs_geo",
        "VOICE_CALL": "voice_call_geo",
        "NOTIFICATION": "notification_geo",
        "PUSH_NOTIFICATION": "push_notification_geo",
        "BRANDED": "branded_geo",
    }

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
                geo_attr = geo_attr_map.get(missive_type)
                if geo_attr:
                    geo_value = None
                    # Search through MRO to find the attribute
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

                    # Format the value
                    if geo_value is None:
                        geo_value = "*"
                    elif isinstance(geo_value, str):
                        if geo_value == "*":
                            provider_data["geographic_coverage"][missive_type] = "*"
                        else:
                            provider_data["geographic_coverage"][missive_type] = [geo_value]
                    elif isinstance(geo_value, (list, tuple)):
                        provider_data["geographic_coverage"][missive_type] = list(geo_value) if geo_value else "*"
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


__all__ = [
    "WebhookView",
    "webhook_status_view",
    "webhook_test_view",
    "system_status_view",
]
