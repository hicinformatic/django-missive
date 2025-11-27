"""Administration du modèle virtuel ProviderInfo."""

import importlib
import json
from decimal import Decimal, InvalidOperation
from typing import Optional

from django.conf import settings
from django.contrib import admin
from django.core.exceptions import (
    MultipleObjectsReturned,
    ObjectDoesNotExist,
    PermissionDenied,
)
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html, format_html_join
from django.utils.translation import gettext_lazy as _

from ..decorators import library_presence_warning, sandbox_warning
from ..helpers import _normalize_providers_config, _provider_error_logger
from ..models import MissiveType, ProviderInfo
from ..models.provider import ProviderInfoQuerySet
from ..providers import normalize_provider_path

# Shared postal attachment limit fields
_POSTAL_ATTACHMENT_LIMIT_FIELDS = [
    {
        "suffix": "max_pages",
        "label": _("Max pages per document"),
        "attr": "max_postal_pages",
    },
    {
        "suffix": "allowed_mime_types",
        "label": _("Allowed MIME types"),
        "attr": "allowed_attachment_mime_types",
        "empty_label": _("No restriction"),
    },
    {
        "suffix": "allowed_page_formats",
        "label": _("Allowed page formats"),
        "attr": "allowed_page_formats",
        "empty_label": _("No restriction"),
    },
]

ATTACHMENT_LIMIT_FIELDS = {
    "EMAIL": [
        {
            "suffix": "max_size_bytes",
            "label": _("Max attachment size"),
            "attr": "max_email_attachment_size_bytes",
            "unit": _("bytes"),
        },
        {
            "suffix": "allowed_mime_types",
            "label": _("Allowed MIME types"),
            "attr": "allowed_attachment_mime_types",
            "empty_label": _("No restriction"),
        },
    ],
    "POSTAL": _POSTAL_ATTACHMENT_LIMIT_FIELDS,
    "POSTAL_REGISTERED": _POSTAL_ATTACHMENT_LIMIT_FIELDS,
    "BRANDED": [
        {
            "suffix": "max_size_bytes",
            "label": _("Max attachment size"),
            "attr": "max_attachment_size_bytes",
            "unit": _("bytes"),
        },
        {
            "suffix": "allowed_mime_types",
            "label": _("Allowed MIME types"),
            "attr": "allowed_attachment_mime_types",
            "empty_label": _("No restriction"),
        },
    ],
}

# Shared postal fields configuration
_POSTAL_SUMMARY_FIELDS = [
    {
        "name": "postal_price",
        "label": _("Unit price (€)"),
        "attr": "postal_price",
        "formatter": "currency",
    },
    {
        "name": "postal_page_limit",
        "label": _("Page limit"),
        "attr": "postal_page_limit",
        "formatter": "integer",
    },
    {
        "name": "postal_page_price_color",
        "label": _("Price per page (color) (€)"),
        "attr": "postal_page_price_color",
        "formatter": "currency",
    },
    {
        "name": "postal_page_price_black_white",
        "label": _("Price per page (B&W) (€)"),
        "attr": "postal_page_price_black_white",
        "formatter": "currency",
    },
    {
        "name": "postal_page_price_single_sided",
        "label": _("Price per page (single-sided) (€)"),
        "attr": "postal_page_price_single_sided",
        "formatter": "currency",
    },
    {
        "name": "postal_page_price_duplex",
        "label": _("Price per page (duplex) (€)"),
        "attr": "postal_page_price_duplex",
        "formatter": "currency",
    },
    {
        "name": "postal_color_printing_available",
        "label": _("Color printing"),
        "attr": "postal_color_printing_available",
        "formatter": "boolean",
    },
    {
        "name": "postal_duplex_printing_available",
        "label": _("Recto/Verso"),
        "attr": "postal_duplex_printing_available",
        "formatter": "boolean",
    },
]

TYPE_SUMMARY_FIELDS = {
    "EMAIL": [
        {
            "name": "email_price",
            "label": _("Unit price (€)"),
            "attr": "email_price",
            "formatter": "currency",
        },
        {
            "name": "email_max_attachment_size_mb",
            "label": _("Max attachment size"),
            "attr": "email_max_attachment_size_mb",
            "formatter": "megabytes",
        },
        {
            "name": "email_allowed_attachment_mime_types",
            "label": _("Allowed MIME types"),
            "attr": "email_allowed_attachment_mime_types",
            "formatter": "list",
        },
    ],
    "EMAIL_MARKETING": [
        {
            "name": "email_marketing_price",
            "label": _("Unit price (€)"),
            "attr": "email_marketing_price",
            "formatter": "currency",
        },
        {
            "name": "email_marketing_max_attachment_size_mb",
            "label": _("Max attachment size"),
            "attr": "email_marketing_max_attachment_size_mb",
            "formatter": "megabytes",
        },
        {
            "name": "email_marketing_allowed_attachment_mime_types",
            "label": _("Allowed MIME types"),
            "attr": "email_marketing_allowed_attachment_mime_types",
            "formatter": "list",
        },
    ],
    "POSTAL": _POSTAL_SUMMARY_FIELDS,
    "POSTAL_REGISTERED": _POSTAL_SUMMARY_FIELDS,
    "POSTAL_SIGNATURE": _POSTAL_SUMMARY_FIELDS,
    "SMS": [
        {
            "name": "sms_price",
            "label": _("Unit price (€)"),
            "attr": "sms_price",
            "formatter": "currency",
        },
        {
            "name": "sms_character_limit",
            "label": _("Characters / SMS"),
            "attr": "sms_character_limit",
            "formatter": "integer",
        },
        {
            "name": "sms_unicode_character_limit",
            "label": _("Unicode characters / SMS"),
            "attr": "sms_unicode_character_limit",
            "formatter": "integer",
        },
    ],
    "LRE": _POSTAL_SUMMARY_FIELDS,
    "LRE_QUALIFIED": _POSTAL_SUMMARY_FIELDS,
    "ERE": [
        {
            "name": "ere_price",
            "label": _("Unit price (€)"),
            "attr": "ere_price",
            "formatter": "currency",
        },
        {
            "name": "ere_archiving_duration",
            "label": _("Archiving duration (days)"),
            "attr": "ere_archiving_duration",
            "formatter": "integer",
        },
    ],
}

TYPE_SUMMARY_FIELD_LOOKUP = {
    spec["name"]: spec for specs in TYPE_SUMMARY_FIELDS.values() for spec in specs
}


def _format_bytes_human_readable(bytes_value: int) -> str:
    """Convert bytes to human-readable format (B, KB, MB, GB)."""
    if bytes_value is None:
        return "-"
    if bytes_value < 1024:
        return f"{bytes_value} B"
    elif bytes_value < 1024 * 1024:
        return f"{bytes_value / 1024:.1f} KB"
    elif bytes_value < 1024 * 1024 * 1024:
        return f"{bytes_value / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_value / (1024 * 1024 * 1024):.1f} GB"


def _format_attachment_limit_value(value, *, unit=None, empty_label=None):
    if value is None:
        return _("Not configured")
    if isinstance(value, (list, tuple, set)):
        if not value:
            return empty_label or _("No restriction")
        # Display list items with line breaks for better readability
        return format_html("<br>".join(str(item) for item in value))
    if isinstance(value, dict):
        return json.dumps(value, indent=2, ensure_ascii=False)
    if unit:
        # Convert bytes to human-readable format
        if unit == _("bytes") or unit == "bytes":
            try:
                bytes_value = int(value)
                return _format_bytes_human_readable(bytes_value)
            except (ValueError, TypeError):
                return f"{value} {unit}"
        return f"{value} {unit}"
    return str(value)


def _build_attachment_limit_field_name(missive_type: str, suffix: str) -> str:
    return f"attachment_limits_{missive_type.lower()}_{suffix}_display"


class MissiveTypeFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour afficher les types avec leurs labels traduits.

    Utilise get_providers_for_type avec les options d'ordonnancement configurées
    dans MISSIVE_PROVIDER_ORDERING pour trier les providers.

    Configuration dans settings.py:

    # Option 1: Ordonnancement par attributs de classe (ex: postal_page_limit)
    MISSIVE_PROVIDER_ORDERING = {
        'POSTAL': ['postal_page_limit'],  # Tri croissant par nombre de pages max
        'POSTAL_REGISTERED': ['-postal_page_limit'],  # Tri décroissant
        'EMAIL': ['email_price'],  # Tri par prix
    }

    # Option 2: Avec métadonnées dans MISSIVE_PROVIDERS
    MISSIVE_PROVIDERS = {
        'python_missive.providers.laposte.LaPosteProvider': {
            'postal_price': 0.50,
            'postal_page_limit': 200,
        },
        'python_missive.providers.maileva.MailevaProvider': {
            'postal_price': 0.30,
            'postal_page_limit': 100,
        },
    }
    MISSIVE_PROVIDER_ORDERING = {
        'POSTAL_REGISTERED': ['postal_price'],  # Trier par prix croissant
    }

    Les colonnes dynamiques utilisent les attributs exposés par python-missive
    (email_max_attachment_size_mb, sms_price, postal_page_limit, etc.), déclarés
    dans les mixins de base via les listes *_config_fields.
    """

    title = _("Missive Type")
    parameter_name = "missive_type"

    def lookups(self, request, model_admin):
        return [(choice.value, choice.label) for choice in MissiveType]

    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        missive_type = self.value()

        # Get provider configuration from settings
        try:
            from python_missive.helpers import get_providers_for_type

            providers_config = getattr(settings, "MISSIVE_PROVIDERS", None)

            # Normalize config: handle both list and dict formats
            if isinstance(providers_config, dict):
                # Dict format: {provider_path: metadata_dict}
                provider_metadata = {}
                provider_paths = []
                for provider_path, metadata in providers_config.items():
                    normalized_path = normalize_provider_path(provider_path)
                    provider_paths.append(normalized_path)
                    if isinstance(metadata, dict):
                        provider_metadata[normalized_path] = metadata
                providers_config = provider_paths
            else:
                # List format: [provider_path, ...]
                normalized_config = _normalize_providers_config()
                providers_config = normalized_config or []
                provider_metadata = None

            # Get ordering configuration from settings
            ordering_config = getattr(settings, "MISSIVE_PROVIDER_ORDERING", {})
            ordering = ordering_config.get(missive_type)

            # Get ordered providers for this type
            ordered_provider_names = get_providers_for_type(
                providers_config,
                missive_type,
                ordering=ordering,
                provider_metadata=provider_metadata,
                on_error=_provider_error_logger,
            )

            # Build a mapping from normalized provider names to ProviderInfo objects
            # Since ProviderInfoManager now uses get_provider_name_from_path,
            # provider.name should match the normalized names from get_providers_for_type
            provider_dict = {p.name.lower(): p for p in queryset}

            filtered = []

            # Add providers in the order returned by get_providers_for_type
            for provider_name in ordered_provider_names:
                # Match by case-insensitive comparison
                provider = provider_dict.get(provider_name.lower())
                if provider and missive_type in provider.missive_types_list:
                    if provider not in filtered:
                        filtered.append(provider)

            # Add any remaining providers that support this type but weren't in the ordered list
            for provider in queryset:
                if (
                    missive_type in provider.missive_types_list
                    and provider not in filtered
                ):
                    filtered.append(provider)

            return ProviderInfoQuerySet(
                model=queryset.model,
                data=filtered,
                query=queryset.query,
                using=queryset._db,
                hints=queryset._hints,
            )
        except Exception:
            # Fallback to original behavior if get_providers_for_type fails
            filtered = []
            for provider in queryset:
                if missive_type in provider.missive_types_list:
                    filtered.append(provider)
            return ProviderInfoQuerySet(
                model=queryset.model,
                data=filtered,
                query=queryset.query,
                using=queryset._db,
                hints=queryset._hints,
            )


@sandbox_warning
@library_presence_warning
@admin.register(ProviderInfo)
class ProviderInfoAdmin(admin.ModelAdmin):
    """Administration en lecture seule pour consulter le statut des providers."""

    class Media:
        js = ("admin/js/config_vars_toggle.js",)

    ordering = ["name"]

    list_display = [
        "name_display",
        "missive_type_display",
        "brands_display",
        "status_display",
        "usage_display",
        "requirements_file",
    ]

    change_form_template = "admin/missive/providerinfo/change_form.html"

    list_filter = [MissiveTypeFilter]

    _provider_metadata_cache: Optional[dict[str, dict]] = None

    search_fields = ["name", "missive_type"]

    readonly_fields = [
        "name",
        "missive_type_display_detail",
        "brands_display",
        "status_display_detail",
        "config_vars_display_detail",
        "installation_display",
        "configuration_display",
        "webhook_urls_display",
        "site_url_display",
        "status_url_display",
        "documentation_url_display",
        "usage_count",
        "requirements_file",
    ]

    def get_list_display(self, request):
        base = list(super().get_list_display(request))
        missive_type = (request.GET.get("missive_type") or "").upper()
        for spec in TYPE_SUMMARY_FIELDS.get(missive_type, []):
            field_name = spec["name"]
            if field_name not in base:
                base.append(field_name)
        return tuple(base)

    def get_fieldsets(self, request, obj=None):
        """Génère les fieldsets dynamiquement selon les types de missive."""
        if obj is None:
            return [
                (_("General Information"), {"fields": ("name",)}),
            ]

        fieldsets = [
            (
                _("General Information"),
                {
                    "fields": (
                        "name",
                        "site_url_display",
                        "missive_type_display_detail",
                        "brands_display",
                        "status_display_detail",
                    )
                },
            ),
        ]

        # Add service info fieldsets for each supported missive type
        missive_types = obj.missive_types_list

        for missive_type in missive_types:
            try:
                label = MissiveType(missive_type).label
            except ValueError:
                label = missive_type

            service_info_field = f"service_info_{missive_type.lower()}_display"
            geo_field = f"geo_{missive_type.lower()}_display"

            fields = [service_info_field, geo_field]

            attachment_configs = ATTACHMENT_LIMIT_FIELDS.get(missive_type.upper(), [])
            for config in attachment_configs:
                attachment_field = _build_attachment_limit_field_name(
                    missive_type, config["suffix"]
                )
                fields.append(attachment_field)

            fieldsets.append(
                (
                    label,
                    {
                        "fields": tuple(fields),
                        "description": f"Service information for {label}",
                    },
                )
            )

        fieldsets.extend(
            [
                (
                    _("Configuration"),
                    {
                        "fields": (
                            "documentation_url_display",
                            "config_vars_display_detail",
                            "webhook_urls_display",
                        ),
                        "description": _(
                            "Environment variables and webhook URLs for this provider"
                        ),
                    },
                ),
                (
                    _("Service Status"),
                    {
                        "fields": (
                            "installation_display",
                            "configuration_display",
                            "status_url_display",
                        )
                    },
                ),
                (_("Statistics"), {"fields": ("usage_count", "requirements_file")}),
            ]
        )

        return fieldsets

    def get_readonly_fields(self, request, obj=None):
        """Ajoute dynamiquement les champs readonly pour chaque type de missive."""
        readonly = list(self.readonly_fields)

        if obj:
            for missive_type in obj.missive_types_list:
                service_info_field = f"service_info_{missive_type.lower()}_display"
                geo_field = f"geo_{missive_type.lower()}_display"
                if service_info_field not in readonly:
                    readonly.append(service_info_field)
                if geo_field not in readonly:
                    readonly.append(geo_field)

                attachment_configs = ATTACHMENT_LIMIT_FIELDS.get(
                    missive_type.upper(), []
                )
                for config in attachment_configs:
                    attachment_field = _build_attachment_limit_field_name(
                        missive_type, config["suffix"]
                    )
                    if attachment_field not in readonly:
                        readonly.append(attachment_field)

        return readonly

    def __getattr__(self, name):
        """Génère dynamiquement les méthodes service_info_{type}_display."""
        if name.startswith("service_info_") and name.endswith("_display"):
            missive_type = name[14:-8].upper()

            def service_info_method(obj):
                try:
                    provider_class = obj._get_provider_class()
                    if provider_class:
                        provider_instance = provider_class()

                        method_name = f"get_{missive_type.lower()}_service_info"

                        if method_name and hasattr(provider_instance, method_name):
                            service_info = getattr(provider_instance, method_name)()
                            # Return raw response as JSON string
                            return json.dumps(
                                service_info, indent=2, ensure_ascii=False
                            )
                        else:
                            return json.dumps(
                                {
                                    "error": f"Method {method_name} not implemented for {provider_instance.name}"
                                },
                                indent=2,
                                ensure_ascii=False,
                            )
                    else:
                        return json.dumps(
                            {"error": "Provider not loaded"},
                            indent=2,
                            ensure_ascii=False,
                        )

                except Exception as e:
                    return json.dumps({"error": str(e)}, indent=2, ensure_ascii=False)

            return admin.display(description=_("Service Information"))(
                service_info_method
            )

        summary_spec = TYPE_SUMMARY_FIELD_LOOKUP.get(name)
        if summary_spec:
            description = summary_spec.get("label", name)

            def summary_method(obj, spec=summary_spec):
                return self._render_type_summary_field(obj, spec)

            return admin.display(description=description)(summary_method)

        if name.startswith("geo_") and name.endswith("_display"):
            missive_type = name[4:-8].upper()

            def geo_method(obj):
                try:
                    provider_class = obj._get_provider_class()
                    if provider_class:
                        provider_instance = provider_class()

                        normalized = missive_type.strip().lower()
                        geo_attr = f"{normalized}_geographic_coverage"

                        # Search through MRO and __dict__ to find the attribute
                        for cls in provider_class.__mro__:
                            if hasattr(cls, "__dict__") and geo_attr in cls.__dict__:
                                geo_value = cls.__dict__[geo_attr]
                                try:
                                    return ", ".join(str(v) for v in geo_value)
                                except (TypeError, ValueError):
                                    return str(geo_value)
                        # If not found in class, try instance
                        if hasattr(provider_instance, geo_attr):
                            geo_value = getattr(provider_instance, geo_attr)
                            try:
                                return ", ".join(str(v) for v in geo_value)
                            except (TypeError, ValueError):
                                return str(geo_value)
                        return "Not configured"

                    else:
                        return "Provider not loaded"

                except Exception as e:
                    return f"Error: {str(e)}"

            return admin.display(description=_("Geographic Coverage"))(geo_method)

        if name.startswith("attachment_limits_") and name.endswith("_display"):
            core_name = name[18:-8]
            missive_type = None
            suffix = ""

            for candidate in ATTACHMENT_LIMIT_FIELDS.keys():
                candidate_lower = candidate.lower()
                if core_name == candidate_lower:
                    missive_type = candidate
                    break
                prefix = f"{candidate_lower}_"
                if core_name.startswith(prefix):
                    missive_type = candidate
                    suffix = core_name[len(prefix) :]
                    break

            if missive_type is None:
                missive_type = core_name.upper()
            else:
                missive_type = missive_type.upper()

            if suffix:
                config = next(
                    (
                        cfg
                        for cfg in ATTACHMENT_LIMIT_FIELDS.get(missive_type, [])
                        if cfg["suffix"] == suffix
                    ),
                    None,
                )

                if not config:
                    raise AttributeError(
                        f"No attachment limit config for {missive_type}.{suffix}"
                    )

                def attachment_limit_method(
                    obj, missive_type=missive_type, config=config
                ):
                    try:
                        provider_class = obj._get_provider_class()
                        if not provider_class:
                            return _("Provider not loaded")

                        provider_instance = provider_class()
                        value = None
                        attr_name = config.get("attr")
                        if attr_name:
                            value = getattr(provider_instance, attr_name, None)
                        value_getter = config.get("value_getter")
                        if value_getter:
                            value = value_getter(provider_instance)

                        return _format_attachment_limit_value(
                            value,
                            unit=config.get("unit"),
                            empty_label=config.get("empty_label"),
                        )

                    except Exception as exc:
                        return _("Error: %s") % exc

                return admin.display(description=config["label"])(
                    attachment_limit_method
                )

            def attachment_limits_method(obj, missive_type=missive_type):
                try:
                    provider_class = obj._get_provider_class()
                    if provider_class:
                        provider_instance = provider_class()

                        limits_info = {}

                        # EMAIL attachments
                        if missive_type == "EMAIL":
                            if hasattr(
                                provider_instance, "max_email_attachment_size_mb"
                            ):
                                limits_info["max_size_mb"] = (
                                    provider_instance.max_email_attachment_size_mb
                                )
                                limits_info["max_size_bytes"] = (
                                    provider_instance.max_email_attachment_size_bytes
                                )
                            if hasattr(
                                provider_instance, "allowed_attachment_mime_types"
                            ):
                                limits_info["allowed_mime_types"] = (
                                    provider_instance.allowed_attachment_mime_types
                                )

                        # POSTAL attachments
                        elif missive_type in ("POSTAL", "POSTAL_REGISTERED"):
                            if hasattr(provider_instance, "max_postal_pages"):
                                limits_info["max_pages"] = (
                                    provider_instance.max_postal_pages
                                )
                            if hasattr(
                                provider_instance, "allowed_attachment_mime_types"
                            ):
                                limits_info["allowed_mime_types"] = (
                                    provider_instance.allowed_attachment_mime_types
                                )
                            if hasattr(provider_instance, "allowed_page_formats"):
                                limits_info["allowed_page_formats"] = (
                                    provider_instance.allowed_page_formats
                                )

                        # BRANDED attachments
                        elif missive_type == "BRANDED":
                            if hasattr(provider_instance, "max_attachment_size_mb"):
                                limits_info["max_size_mb"] = (
                                    provider_instance.max_attachment_size_mb
                                )
                                limits_info["max_size_bytes"] = (
                                    provider_instance.max_attachment_size_bytes
                                )
                            if hasattr(
                                provider_instance, "allowed_attachment_mime_types"
                            ):
                                limits_info["allowed_mime_types"] = (
                                    provider_instance.allowed_attachment_mime_types
                                )

                        if limits_info:
                            return json.dumps(limits_info, indent=2, ensure_ascii=False)
                        else:
                            return json.dumps(
                                {"message": "No attachment limits configured"},
                                indent=2,
                                ensure_ascii=False,
                            )

                    else:
                        return json.dumps(
                            {"error": "Provider not loaded"},
                            indent=2,
                            ensure_ascii=False,
                        )

                except Exception as e:
                    return json.dumps({"error": str(e)}, indent=2, ensure_ascii=False)

            return admin.display(description=_("Attachment Limits"))(
                attachment_limits_method
            )

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def get_object(self, request, object_id, from_field=None):
        """Récupère l'objet provider par son name (qui est maintenant le pk)."""
        if object_id is None:
            return None

        try:
            # Le pk est maintenant le name, donc on peut chercher directement
            queryset = self.get_queryset(request)
            try:
                # Essayer de trouver par pk (qui est le name)
                return queryset.get(pk=object_id)
            except (ObjectDoesNotExist, MultipleObjectsReturned):
                # Fallback: chercher par name (insensible à la casse)
                for provider in queryset:
                    if provider.name.lower() == object_id.lower():
                        return provider
                    # Vérifier aussi par display_name si disponible
                    provider_class = provider._get_provider_class()
                    if provider_class:
                        display_name = getattr(provider_class, "display_name", None)
                        if display_name and display_name.lower() == object_id.lower():
                            return provider
                return None
        except Exception:
            # Fallback vers le comportement par défaut
            return super().get_object(request, object_id, from_field)

    def get_search_results(self, request, queryset, search_term):
        """Implémente la recherche manuelle pour le QuerySet personnalisé."""
        if not search_term:
            return queryset, False

        search_term_lower = search_term.lower()
        filtered = []

        for provider in queryset:
            if search_term_lower in provider.name.lower():
                filtered.append(provider)
                continue

            if search_term_lower in provider.missive_type.lower():
                filtered.append(provider)
                continue

            for missive_type in provider.missive_types_list:
                if search_term_lower in missive_type.lower():
                    filtered.append(provider)
                    break

        from ..models.provider import ProviderInfoQuerySet

        filtered_qs = ProviderInfoQuerySet(
            model=queryset.model,
            data=filtered,
            query=queryset.query,
            using=queryset._db,
            hints=queryset._hints,
        )

        return filtered_qs, False

    @admin.display(description=_("Provider"))
    def name_display(self, obj):
        """Displays provider name with description."""
        description = obj.description_text
        if description:
            return format_html(
                '<strong>{}</strong><br><span style="color: #6c757d; font-size: 11px; font-style: italic;">{}</span>',
                obj.name.capitalize(),
                description,
            )
        else:
            return format_html("<strong>{}</strong>", obj.name.capitalize())

    @admin.display(description=_("Types supportés"))
    def missive_type_display(self, obj):
        """Badges colorés pour tous les types supportés."""
        colors = {
            "POSTAL": "#6c757d",
            "POSTAL_REGISTERED": "#495057",
            "LRE": "#495057",
            "EMAIL": "#0d6efd",
            "SMS": "#198754",
            "RCS": "#20c997",
            "VOICE_CALL": "#6f42c1",
            "NOTIFICATION": "#fd7e14",
            "PUSH_NOTIFICATION": "#dc3545",
            "BRANDED": "#9b59b6",
        }

        badges = []
        for missive_type in obj.missive_types_list:
            color = colors.get(missive_type, "#6c757d")

            try:
                label = MissiveType(missive_type).label
            except ValueError:
                label = missive_type

            badges.append(
                '<span style="background-color: {}; color: white; padding: 3px 8px; '
                "border-radius: 3px; font-size: 10px; font-weight: bold; "
                'margin: 2px; display: inline-block; white-space: nowrap;">{}</span>'.format(
                    color, label
                )
            )

        return format_html(" ".join(badges))

    @admin.display(description=_("Types supportés"))
    def missive_type_display_detail(self, obj):
        return self.missive_type_display(obj)

    @admin.display(description=_("Supported Brands"))
    def brands_display(self, obj):
        """Displays supported messaging brands (for BRANDED providers)."""
        brands = obj.brands

        if not brands:
            return format_html(
                '<span style="color: #6c757d; font-style: italic;">—</span>'
            )

        brand_colors = {
            "whatsapp": "#25D366",
            "slack": "#4A154B",
            "teams": "#6264A7",
            "telegram": "#0088cc",
            "messenger": "#0084FF",
            "signal": "#3A76F0",
            "discord": "#5865F2",
        }

        badges_html = format_html_join(
            "",
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            "border-radius: 3px; font-size: 11px; font-weight: bold; margin-right: 4px; "
            'white-space: nowrap;">{}</span>',
            (
                (brand_colors.get(brand.lower(), "#6c757d"), brand.upper())
                for brand in brands
            ),
        )

        return format_html('<span style="white-space: nowrap;">{}</span>', badges_html)

    @admin.display(description=_("Status"))
    def status_display(self, obj):
        """Badge pour le statut global."""
        if obj.status == "ready":
            return format_html(
                '<span style="background-color: #d1e7dd; color: #0f5132; padding: 5px 12px; '
                'border-radius: 4px; font-size: 12px; font-weight: bold; white-space: nowrap;">✅ Ready</span>'
            )
        elif obj.status == "needs_config":
            return format_html(
                '<span style="background-color: #fff3cd; color: #664d03; padding: 5px 12px; '
                'border-radius: 4px; font-size: 12px; font-weight: bold; white-space: nowrap;">⚠️ Config Required</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #f8d7da; color: #842029; padding: 5px 12px; '
                'border-radius: 4px; font-size: 12px; font-weight: bold; white-space: nowrap;">❌ Not Installed</span>'
            )

    @admin.display(description=_("Credits"))
    def credits_display(self, obj):
        """Displays available credits."""
        credits_info = obj.credits_info

        if not credits_info:
            return format_html(
                '<span style="color: #ccc; white-space: nowrap;">-</span>'
            )

        credit_type = credits_info.get("type")
        remaining = credits_info.get("remaining")
        currency = credits_info.get("currency", "")

        if remaining is None:
            return format_html(
                '<span style="color: #ccc; white-space: nowrap;">-</span>'
            )

        if credit_type == "money":
            if remaining < 10:
                color = "#dc3545"  # Red
            elif remaining < 50:
                color = "#ffc107"
            else:
                color = "#198754"

            return format_html(
                '<span style="color: {}; font-weight: bold; white-space: nowrap;">{:.2f} {}</span>',
                color,
                remaining,
                currency,
            )
        elif credit_type == "count" or credit_type == "sms_units":
            if remaining < 100:
                color = "#dc3545"
            elif remaining < 500:
                color = "#ffc107"
            else:
                color = "#198754"

            return format_html(
                '<span style="color: {}; font-weight: bold; white-space: nowrap;">{} SMS</span>',
                color,
                int(remaining),
            )
        elif credit_type == "unlimited":
            return format_html(
                '<span style="color: #198754; font-weight: bold; white-space: nowrap;">∞ Unlimited</span>'
            )
        else:
            return format_html(
                '<span style="white-space: nowrap;">{}</span>', str(remaining)
            )

    @admin.display(description=_("Packages"))
    def installation_display(self, obj):
        """Displays required packages and installation status."""
        packages = obj.required_packages

        if packages:
            package_statuses = []
            for package in packages:
                try:
                    importlib.import_module(package)
                    package_statuses.append(
                        f'<span style="color: #198754;">✓</span> <code>{package}</code>'
                    )
                except ImportError:
                    package_statuses.append(
                        f'<span style="color: #dc3545;">✗ <code style="color: #dc3545;">{package}</code></span>'
                    )

            packages_html = format_html_join(
                ", ", "{}", ((status,) for status in package_statuses)
            )
            return format_html(
                '<span style="white-space: nowrap;">{}</span>',
                packages_html,
            )
        else:
            return format_html(
                '<span style="color: #6c757d; white-space: nowrap; font-style: italic;">None (always available)</span>'
            )

    @admin.display(description=_("Credentials"))
    def configuration_display(self, obj):
        """Indique si les identifiants sont configurés."""
        if obj.is_configured:
            return format_html(
                '<span style="color: #198754; white-space: nowrap;">✓ Configured</span>'
            )
        else:
            return format_html(
                '<span style="color: #ffc107; white-space: nowrap;">✗ Missing</span>'
            )

    @admin.display(description=_("SLA Status"))
    def status_url_display(self, obj):
        """Displays provider status/SLA page link."""
        url = obj.status_url

        if url:
            return format_html(
                '<a href="{}" target="_blank" style="white-space: nowrap;">'
                '<span style="color: #0d6efd;">🔗 Status Page</span>'
                "</a>",
                url,
            )
        else:
            return format_html(
                '<span style="color: #6c757d; font-style: italic; white-space: nowrap;">Not available</span>'
            )

    @admin.display(description=_("Documentation"))
    def documentation_url_display(self, obj):
        """Displays provider API documentation link."""
        url = obj.documentation_url

        if url:
            return format_html(
                '<a href="{}" target="_blank" style="white-space: nowrap;">'
                '<span style="color: #0d6efd;">📖 API Documentation</span>'
                "</a>",
                url,
            )
        else:
            return format_html(
                '<span style="color: #6c757d; font-style: italic; white-space: nowrap;">Not available</span>'
            )

    @admin.display(description=_("Official Site"))
    def site_url_display(self, obj):
        """Displays provider official website link."""
        url = obj.site_url

        if url:
            return format_html(
                '<a href="{}" target="_blank" style="white-space: nowrap;">'
                '<span style="color: #0d6efd;">🌐 Official Site</span>'
                "</a>",
                url,
            )
        else:
            return format_html(
                '<span style="color: #6c757d; font-style: italic; white-space: nowrap;">Not available</span>'
            )

    @admin.display(description=_("Webhook URLs"))
    def webhook_urls_display(self, obj):
        """Displays unique webhook URL for this provider."""
        from django.conf import settings

        types = obj.missive_types_list
        if not types:
            return format_html(
                '<span style="color: #6c757d; font-style: italic;">No service configured</span>'
            )

        base_domain = getattr(
            settings, "MISSIVE_WEBHOOK_BASE_URL", "https://example.com"
        )
        base_domain = base_domain.rstrip("/")

        provider_slug = obj.name.lower().replace(" ", "")
        webhook_url = f"{base_domain}/missive/webhooks/{provider_slug}/"

        html_parts = []

        html_parts.append(
            '<div style="margin-top: 5px; padding: 12px; background: #e7f3ff; border-left: 4px solid #0d6efd; border-radius: 4px;">'
            '<div style="font-weight: 600; color: #0c5b9d; margin-bottom: 8px; font-size: 13px;">🔗 Unique Webhook URL</div>'
            f'<code style="background: #fff; padding: 6px 12px; border-radius: 4px; font-size: 12px; color: #0d6efd; display: block; word-break: break-all;">{webhook_url}</code>'
            '<div style="margin-top: 8px; padding: 6px; background: #fff; border-radius: 3px;">'
            '<small style="color: #6c757d;">✅ One URL for all service types:'
        )

        type_names = [t.replace("_", " ").title() for t in types]
        html_parts.append(f' {", ".join(type_names)}</small>')
        html_parts.append("</div></div>")

        if base_domain == "https://example.com":
            note_color = "#dc3545"
            note_icon = "⚠️"
            note_text = (
                f"{note_icon} <strong>Configuration required:</strong> "
                f"Add <code>MISSIVE_WEBHOOK_BASE_URL = 'https://your-domain.com'</code> "
                f"in settings.py to get real URLs."
            )
        else:
            note_color = "#856404"
            note_icon = "💡"
            note_text = (
                f"{note_icon} <strong>Note:</strong> Configure these URLs in your provider dashboard "
                f"to receive status notifications."
            )

        html_parts.append(
            f'<div style="margin-top: 10px; padding: 8px; background: #fff3cd; border-left: 3px solid #ffc107; border-radius: 3px;">'
            f'<small style="color: {note_color};">{note_text}</small>'
            f"</div>"
        )

        return format_html("".join(html_parts))

    @admin.display(description=_("Usage"))
    def usage_display(self, obj):
        """Displays usage count."""
        count = obj.usage_count
        if count > 0:
            return format_html(
                '<strong style="white-space: nowrap;">{}</strong> use{}',
                count,
                "s" if count > 1 else "",
            )
        else:
            return format_html(
                '<span style="color: #ccc; white-space: nowrap;">Never used</span>'
            )

    @admin.display(description=_("Status"))
    def status_display_detail(self, obj):
        return self.status_display(obj)

    @admin.display(description=_("Variables"))
    def config_vars_display(self, obj):
        """Displays config variables in list."""
        config_vars = obj.required_config_keys

        if not config_vars:
            return format_html(
                '<span style="color: #6c757d; font-style: italic;">None</span>'
            )

        vars_html = format_html_join(
            ", ", "<code>{}</code>", ((var,) for var in config_vars)
        )

        return format_html(
            '<span style="white-space: nowrap;">{}</span>',
            vars_html,
        )

    @admin.display(description=_("Configuration Variables"))
    def config_vars_display_detail(self, obj):
        """Displays all config variables in edit page."""
        config_vars = obj.required_config_keys

        if not config_vars:
            return format_html(
                '<p style="color: #666;">No specific configuration required for this provider.</p>'
            )

        config_status = obj.config_status

        rows = []
        for var_name in config_vars:
            status = config_status.get(var_name, {})
            is_configured = status.get("configured", False)

            if is_configured:
                icon = '<span style="color: #198754; font-weight: bold;">✓</span>'
                status_text = '<span style="color: #198754;">Configured</span>'
                actual_value = str(status.get("value", ""))
                value_html = (
                    '<span class="config-eye" data-var="{}" style="cursor: pointer; color: #6c757d; margin-right: 8px;" '
                    'title="Click to show/hide">👁️</span>'
                    '<span class="config-value-masked" data-var="{}" style="color: #6c757d;">••••••••</span>'
                    '<span class="config-value-revealed" data-var="{}" style="display: none;"><code>{}</code></span>'
                ).format(var_name, var_name, var_name, actual_value)
            else:
                if var_name == "SMSPARTNER_WEBHOOK_IPS":
                    icon = '<span style="color: #0d6efd; font-weight: bold;">ℹ️</span>'
                    status_text = '<span style="color: #0d6efd;">Default</span>'
                    value_html = (
                        '<code style="color: #0d6efd;">185.66.232.0/24</code> '
                        '<small style="color: #6c757d;">(official SMSPartner range)</small>'
                    )
                else:
                    icon = '<span style="color: #dc3545; font-weight: bold;">✗</span>'
                    status_text = '<span style="color: #dc3545;">Missing</span>'
                    value_html = "<code>Not defined</code>"

            rows.append(
                "<tr>"
                '<td style="padding: 8px; border-bottom: 1px solid #ddd;">{}</td>'
                '<td style="padding: 8px; border-bottom: 1px solid #ddd;"><code>{}</code></td>'
                '<td style="padding: 8px; border-bottom: 1px solid #ddd;">{}</td>'
                '<td style="padding: 8px; border-bottom: 1px solid #ddd;">{}</td>'
                "</tr>".format(icon, var_name, status_text, value_html)
            )

        table_html = """
        <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
            <thead>
                <tr style="background-color: #f8f9fa;">
                    <th style="padding: 10px; text-align: left; border-bottom: 2px solid #dee2e6; width: 30px;"></th>
                    <th style="padding: 10px; text-align: left; border-bottom: 2px solid #dee2e6;">Variable</th>
                    <th style="padding: 10px; text-align: left; border-bottom: 2px solid #dee2e6;">Status</th>
                    <th style="padding: 10px; text-align: left; border-bottom: 2px solid #dee2e6;">Value</th>
                </tr>
            </thead>
            <tbody>
                {}
            </tbody>
        </table>
        <p style="margin-top: 15px; padding: 10px; background-color: #cfe2ff; border-left: 4px solid #0d6efd; color: #084298;">
            <strong>💡 To configure:</strong> Edit the <code>.env</code> file at the project root and restart the server.
        </p>
        """.format(
            "".join(rows)
        )

        return format_html(table_html)

    def _render_type_summary_field(self, obj, spec):
        """Resolve a provider config attribute for summary display."""
        attr_name = spec.get("attr") or spec.get("name")
        provider_class = obj._get_provider_class()
        value = None
        if provider_class and attr_name:
            value = getattr(provider_class, attr_name, None)
        if value in (None, ""):
            metadata = self._get_metadata_for_provider(obj.name)
            if metadata and attr_name:
                value = metadata.get(attr_name)
        return self._format_summary_value(value, spec)

    def _format_summary_value(self, value, spec):
        placeholder = format_html(
            '<span style="color: #6c757d; font-style: italic;">—</span>'
        )

        if value in (None, ""):
            return placeholder

        formatter = spec.get("formatter")

        if formatter == "currency":
            try:
                amount = Decimal(str(value))
                return format_html("€{:.2f}", amount)
            except (InvalidOperation, TypeError, ValueError):
                return format_html("{}", value)

        if formatter == "boolean":
            if isinstance(value, str):
                truthy = value.strip().lower() in {"1", "true", "yes", "y", "on"}
            else:
                truthy = bool(value)
            label = _("Yes") if truthy else _("No")
            color = "#198754" if truthy else "#6c757d"
            return format_html('<span style="color: {};">{}</span>', color, label)

        if formatter == "megabytes":
            try:
                mb_value = Decimal(str(value))
                return format_html("{} MB", mb_value.normalize())
            except (InvalidOperation, TypeError, ValueError):
                return format_html("{} MB", value)

        if formatter == "integer":
            try:
                return format_html("{}", int(value))
            except (TypeError, ValueError):
                return format_html("{}", value)

        if formatter == "list":
            if isinstance(value, (list, tuple, set)):
                return format_html_join("<br>", "{}", ((v,) for v in value))
            return format_html("{}", value)

        return format_html("{}", value)

    def _get_metadata_for_provider(self, provider_name: str):
        metadata_map = self._get_provider_metadata_map()
        return metadata_map.get((provider_name or "").lower(), {})

    def _get_provider_metadata_map(self):
        if self._provider_metadata_cache is not None:
            return self._provider_metadata_cache

        metadata_map: dict[str, dict] = {}

        dedicated_metadata = getattr(settings, "MISSIVE_PROVIDER_METADATA", {})
        if isinstance(dedicated_metadata, dict):
            for provider_name, metadata in dedicated_metadata.items():
                if isinstance(metadata, dict):
                    metadata_map[provider_name.lower()] = dict(metadata)

        providers_config = getattr(settings, "MISSIVE_PROVIDERS", None)
        if isinstance(providers_config, dict):
            try:
                from python_missive.providers import get_provider_name_from_path
            except ImportError:

                def get_provider_name_from_path(path: str) -> str:
                    return path.split(".")[-2] if "." in path else path

            for provider_path, metadata in providers_config.items():
                if not isinstance(metadata, dict):
                    continue
                normalized_path = normalize_provider_path(provider_path)
                provider_name = get_provider_name_from_path(normalized_path)
                metadata_map.setdefault(provider_name.lower(), {}).update(metadata)

        self._provider_metadata_cache = metadata_map
        return metadata_map

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<str:provider_name>/test/",
                self.admin_site.admin_view(self.provider_test_view),
                name="missive_provider_test",
            ),
            path(
                "<str:provider_name>/test/send/",
                self.admin_site.admin_view(self.provider_test_send_view),
                name="missive_provider_test_send",
            ),
        ]
        return custom_urls + urls

    def _get_provider_info(self, provider_name: str):
        """Récupère le ProviderInfo par son name."""
        try:
            return ProviderInfo.objects.get(pk=provider_name)
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            return None

    def _get_provider_path(self, provider_name: str):
        """Récupère le chemin du provider depuis la config."""
        providers_config = getattr(settings, "MISSIVE_PROVIDERS", None)
        if not providers_config:
            return None

        try:
            from python_missive.helpers import get_provider_by_attribute

            provider_paths = (
                list(providers_config.keys())
                if isinstance(providers_config, dict)
                else list(providers_config)
            )

            provider_class = get_provider_by_attribute(
                provider_paths,
                "name",
                provider_name,
                on_error=_provider_error_logger,
            )

            if provider_class:
                return f"{provider_class.__module__}.{provider_class.__name__}"

            return None
        except Exception:
            return None

    def provider_test_view(self, request, provider_name):
        """Vue de test pour un provider spécifique."""
        if not self.has_view_permission(request):
            raise PermissionDenied

        provider_info = self._get_provider_info(provider_name)
        if provider_info is None:
            from django.http import Http404

            raise Http404(_("Provider not found"))

        provider_path = self._get_provider_path(provider_name)
        can_test = provider_path is not None and provider_info.status == "ready"

        # Déterminer le type de missive par défaut
        default_type = "EMAIL"
        if provider_info.missive_types_list:
            default_type = provider_info.missive_types_list[0]

        context = {
            **self.admin_site.each_context(request),
            "title": _("Test provider"),
            "provider": provider_info,
            "provider_path": provider_path,
            "provider_configured": can_test,
            "can_test": can_test,
            "default_type": default_type,
            "missive_types": provider_info.missive_types_list,
            "send_url": reverse(
                "admin:missive_provider_test_send", args=[provider_name]
            ),
            "opts": ProviderInfo._meta,
        }
        return TemplateResponse(
            request, "admin/missive/providerinfo/test.html", context
        )

    def provider_test_send_view(self, request, provider_name):
        """Vue AJAX pour envoyer un missive de test avec le provider spécifié."""
        if not self.has_view_permission(request):
            raise PermissionDenied

        if request.method != "POST":
            return JsonResponse({"error": "Method not allowed"}, status=405)

        provider_info = self._get_provider_info(provider_name)
        if provider_info is None:
            return JsonResponse({"error": "Provider not found"}, status=404)

        provider_path = self._get_provider_path(provider_name)
        if not provider_path:
            return JsonResponse({"error": "Provider path not found"}, status=404)

        try:
            from ..shortcuts import send_missive

            missive_type = request.POST.get("missive_type", "EMAIL").upper()
            content = request.POST.get("content", "").strip()
            recipient_email = request.POST.get("recipient_email", "").strip()
            recipient_phone = request.POST.get("recipient_phone", "").strip()
            subject = request.POST.get("subject", "").strip()

            if not content:
                return JsonResponse({"error": "Content is required"}, status=400)

            # Valider selon le type
            if missive_type == "EMAIL":
                if not recipient_email:
                    return JsonResponse(
                        {"error": "Recipient email is required for EMAIL"}, status=400
                    )
                if not subject:
                    return JsonResponse(
                        {"error": "Subject is required for EMAIL"}, status=400
                    )
            elif missive_type in ("SMS", "VOICE_CALL"):
                if not recipient_phone:
                    return JsonResponse(
                        {"error": f"Recipient phone is required for {missive_type}"},
                        status=400,
                    )

            # Envoyer avec le provider spécifié
            # On utilise send_missive mais on force le provider après création
            missive = send_missive(
                missive_type=missive_type,
                content=content,
                recipient_email=recipient_email or None,
                recipient_phone=recipient_phone or None,
                subject=subject or None,
            )
            # Forcer l'utilisation de ce provider uniquement
            missive._provider_path = provider_path  # type: ignore[attr-defined]

            return JsonResponse(
                {
                    "success": True,
                    "missive_id": missive.id,
                    "status": missive.status,
                    "provider_used": missive.provider or provider_path,
                    "error_message": missive.error_message,
                }
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    def changelist_view(self, request, extra_context=None):
        """Ajoute du contexte à la vue liste."""
        self._provider_metadata_cache = None
        extra_context = extra_context or {}

        from ..models import Missive

        extra_context["total_missives"] = Missive.objects.count()

        all_providers = list(ProviderInfo.objects.all())
        extra_context["ready_count"] = sum(
            1 for p in all_providers if p.status == "ready"
        )
        extra_context["needs_config_count"] = sum(
            1 for p in all_providers if p.status == "needs_config"
        )
        extra_context["not_installed_count"] = sum(
            1 for p in all_providers if p.status == "not_installed"
        )

        return super().changelist_view(request, extra_context)
