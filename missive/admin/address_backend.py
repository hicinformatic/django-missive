"""Admin for virtual address backend diagnostics."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from django.conf import settings
from django.contrib import admin
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

try:
    from python_missive.helpers import get_address_from_backends as pm_get_address_from_backends
except ImportError:  # pragma: no cover - optional dependency
    pm_get_address_from_backends = None

from ..models.address_backend import AddressBackendInfo, AddressBackendInfoQuerySet
from ..models.address_lookup import AddressLookup, AddressLookupQuerySet


def get_backend_configs() -> list[Dict[str, Any]]:
    config = getattr(settings, "MISSIVE_ADDRESS_BACKENDS", None)
    return list(config or [])


def get_backend_config_for_path(class_path: Optional[str]) -> Optional[Dict[str, Any]]:
    if not class_path:
        return None
    for backend in get_backend_configs():
        if backend.get("class") == class_path:
            return backend
    return None


def build_address_suggestions(
    config_list: list[Dict[str, Any]], term: str
) -> list[Dict[str, Any]]:
    if not config_list or not term or pm_get_address_from_backends is None:
        return []

    try:
        result = pm_get_address_from_backends(
            config_list,
            operation="validate",
            address_line1=term,
        )
    except Exception as exc:  # pragma: no cover - defensive
        return [{"label": str(exc), "raw": {"error": str(exc)}}]

    backend_name = result.get("backend_used") or ""
    backend_reference = result.get("backend_reference") or ""

    suggestions = result.get("suggestions") or []
    if suggestions:
        rows = []
        for suggestion in suggestions:
            raw = dict(suggestion or {})
            if backend_name and not raw.get("backend_used"):
                raw["backend_used"] = backend_name
            if backend_reference and not raw.get("backend_reference"):
                raw["backend_reference"] = backend_reference
            label = (
                raw.get("formatted_address")
                or raw.get("normalized_address")
                or term
            )
            rows.append({"label": label, "raw": raw})
        return rows

    normalized = result.get("normalized_address") or {}
    label = normalized.get("formatted_address") or term
    raw_result = dict(result)
    if backend_name and not raw_result.get("backend_used"):
        raw_result["backend_used"] = backend_name
    if backend_reference and not raw_result.get("backend_reference"):
        raw_result["backend_reference"] = backend_reference
    return [{"label": label, "raw": raw_result}]


@admin.register(AddressBackendInfo)
class AddressBackendInfoAdmin(admin.ModelAdmin):
    change_list_template = "admin/missive/addressbackendinfo/change_list.html"
    ordering = ["name"]
    actions = None
    list_display = [
        "display_name_column",
        "status_display",
        "selected_display",
        "documentation_link",
        "site_link",
    ]

    change_form_template = "admin/missive/addressbackendinfo/change_form.html"
    search_fields = ["name", "class_path", "status"]
    readonly_fields = [
        "name",
        "class_path",
        "status_display",
        "selected_display",
        "documentation_link",
        "site_link",
        "packages_display",
        "config_display_detail",
        "error_display",
    ]

    def get_queryset(self, request):
        qs = AddressBackendInfo.objects.all()
        return qs

    def get_actions(self, request):
        """Disable bulk actions/selection like Provider admin."""
        return {}

    def get_search_results(self, request, queryset, search_term):
        if not search_term:
            return queryset, False
        term = search_term.strip().lower()
        if not term:
            return queryset, False

        def _matches(obj: AddressBackendInfo) -> bool:
            candidates = [
                obj.display_name,
                obj.name,
                obj.class_path,
                obj.status,
            ]
            diag = obj.diagnostic
            candidates.append(str(diag.get("backend_name", "")))
            candidates.append(str(diag.get("backend_display_name", "")))
            candidates.append(str(diag.get("class", "")))
            for value in candidates:
                if value and term in str(value).lower():
                    return True
            return False

        filtered = [obj for obj in queryset if _matches(obj)]
        return AddressBackendInfoQuerySet(model=self.model, data=filtered), False

    def has_add_permission(self, request):
        return False

    def get_object(self, request, object_id, from_field=None):
        """Récupère l'objet address backend par son name (qui est maintenant le pk)."""
        if object_id is None:
            return None

        try:
            # Le pk est maintenant le name, donc on peut chercher directement
            queryset = self.get_queryset(request)
            try:
                # Essayer de trouver par pk (qui est le name)
                return queryset.get(pk=object_id)
            except (ObjectDoesNotExist, MultipleObjectsReturned):
                # Fallback: chercher par name (insensible à la casse) ou slug
                for backend in queryset:
                    if backend.name.lower() == object_id.lower():
                        return backend
                    if backend.slug == object_id.lower():
                        return backend
                return None
        except Exception:
            # Fallback vers le comportement par défaut
            return super().get_object(request, object_id, from_field)

    # Helpers ----------------------------------------------------------
    def _all_backend_configs(self):
        return get_backend_configs()

    def _get_backend_config_for_path(self, class_path: str | None):
        return get_backend_config_for_path(class_path)

    def _get_backend_info(self, backend_name: str):
        """Récupère le backend par son name."""
        try:
            queryset = self.get_queryset(None)
            try:
                # Essayer de trouver par pk (qui est le name)
                return queryset.get(pk=backend_name)
            except (ObjectDoesNotExist, MultipleObjectsReturned):
                # Fallback: chercher par name (insensible à la casse) ou slug
                for backend in queryset:
                    if backend.name.lower() == backend_name.lower():
                        return backend
                    if backend.slug == backend_name.lower():
                        return backend
                return None
        except Exception:
            return None

    def _build_results(self, config_list, term):
        return build_address_suggestions(config_list, term)

    # List display helpers ---------------------------------------------
    @admin.display(description=_("Backend"))
    def display_name_column(self, obj: AddressBackendInfo):
        return obj.display_name

    @admin.display(description=_("Status"))
    def status_display(self, obj: AddressBackendInfo):
        status = (obj.status or "").lower()
        if status == "working":
            return format_html(
                '<span style="background-color: #d1e7dd; color: #0f5132; padding: 5px 12px; '
                'border-radius: 4px; font-size: 12px; font-weight: bold; white-space: nowrap;">✅ {}</span>',
                _("Working"),
            )
        if status == "missing_config":
            return format_html(
                '<span style="background-color: #fff3cd; color: #664d03; padding: 5px 12px; '
                'border-radius: 4px; font-size: 12px; font-weight: bold; white-space: nowrap;">⚠️ {}</span>',
                _("Config Required"),
            )
        if status == "missing_packages":
            return format_html(
                '<span style="background-color: #f8d7da; color: #842029; padding: 5px 12px; '
                'border-radius: 4px; font-size: 12px; font-weight: bold; white-space: nowrap;">❌ {}</span>',
                _("Packages Missing"),
            )
        return format_html(
            '<span style="background-color: #f8d7da; color: #842029; padding: 5px 12px; '
            'border-radius: 4px; font-size: 12px; font-weight: bold; white-space: nowrap;">❌ {}</span>',
            _("Unavailable"),
        )

    @admin.display(description=_("Selected"))
    def selected_display(self, obj: AddressBackendInfo):
        return _("Yes") if obj.is_selected else _("No")

    @admin.display(description=_("Documentation"))
    def documentation_link(self, obj: AddressBackendInfo):
        if not obj.documentation_url:
            return "—"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener">{}</a>',
            obj.documentation_url,
            obj.documentation_url,
        )

    @admin.display(description=_("Website"))
    def site_link(self, obj: AddressBackendInfo):
        if not obj.site_url:
            return "—"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener">{}</a>',
            obj.site_url,
            obj.site_url,
        )

    # Readonly details -------------------------------------------------
    @admin.display(description=_("Packages"))
    def packages_display(self, obj: AddressBackendInfo):
        packages = obj.packages_summary
        if not packages:
            return "—"
        rows = []
        for name, installed in packages:
            icon = "✓" if installed else "✗"
            color = "#198754" if installed else "#dc3545"
            rows.append((color, icon, name))
        return format_html_join(
            "<br>",
            '<span style="color:{};">{}</span> <code>{}</code>',
            rows,
        )

    @admin.display(description=_("Configuration"))
    def config_display(self, obj: AddressBackendInfo):
        """Simple config display for list view."""
        entries = obj.config_summary
        if not entries:
            return "—"
        configured = sum(1 for _, present, _ in entries if present)
        total = len(entries)
        if configured == total:
            return format_html(
                '<span style="color: #198754;">✓ {} configured</span>', total
            )
        return format_html(
            '<span style="color: #dc3545;">✗ {} / {} configured</span>',
            configured,
            total,
        )

    @admin.display(description=_("Configuration Variables"))
    def config_display_detail(self, obj: AddressBackendInfo):
        """Displays all config variables in edit page with table."""
        entries = obj.config_summary
        if not entries:
            return format_html(
                '<p style="color: #666;">No specific configuration required for this backend.</p>'
            )

        # Keys that are not sensitive (public URLs, user agents, etc.)
        non_sensitive_keys = {
            "NOMINATIM_BASE_URL",
            "NOMINATIM_USER_AGENT",
            "PHOTON_BASE_URL",
        }

        backend_config = self._get_backend_config_for_path(obj.class_path)
        config_dict = backend_config.get("config", {}) if backend_config else {}

        rows = []
        for key, present, preview in entries:
            # Get actual value from config
            actual_value = config_dict.get(key)

            # Check if value is actually set (not None, not empty string)
            is_configured = present and actual_value is not None and str(actual_value).strip() != ""

            if is_configured:
                icon = format_html(
                    '<span style="color: #198754; font-weight: bold;">✓</span>'
                )
                status_text = format_html(
                    '<span style="color: #198754;">Configured</span>'
                )

                if key in non_sensitive_keys:
                    # For non-sensitive keys, show full value directly
                    value_html = format_html('<code>{}</code>', str(actual_value))
                else:
                    # For sensitive keys, show masked value with eye button
                    value_html = format_html(
                        '<span class="config-eye" data-var="{}" style="cursor: pointer; color: #6c757d; margin-right: 8px;" '
                        'title="Click to show/hide">👁️</span>'
                        '<span class="config-value-masked" data-var="{}" style="color: #6c757d;">••••••••</span>'
                        '<span class="config-value-revealed" data-var="{}" style="display: none;"><code>{}</code></span>',
                        key,
                        key,
                        key,
                        str(actual_value),
                    )
            else:
                icon = format_html(
                    '<span style="color: #dc3545; font-weight: bold;">✗</span>'
                )
                status_text = format_html(
                    '<span style="color: #dc3545;">Missing</span>'
                )
                value_html = format_html(
                    '<code style="color: #6c757d;">Not defined</code>'
                )

            rows.append(
                format_html(
                    "<tr>"
                    '<td style="padding: 8px; border-bottom: 1px solid #ddd;">{}</td>'
                    '<td style="padding: 8px; border-bottom: 1px solid #ddd;"><code>{}</code></td>'
                    '<td style="padding: 8px; border-bottom: 1px solid #ddd;">{}</td>'
                    '<td style="padding: 8px; border-bottom: 1px solid #ddd;">{}</td>'
                    "</tr>",
                    icon,
                    key,
                    status_text,
                    value_html,
                )
            )

        table_html = format_html(
            """
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
            <strong>💡 To configure:</strong> Edit the <code>MISSIVE_ADDRESS_BACKENDS</code> setting in your Django settings file.
        </p>
        """,
            mark_safe("".join(str(row) for row in rows)),  # nosec
        )

        return table_html

    @admin.display(description=_("Error"))
    def error_display(self, obj: AddressBackendInfo):
        return obj.error or "—"


@admin.register(AddressLookup)
class AddressLookupAdmin(admin.ModelAdmin):
    list_display = ["label", "backend_used", "backend_reference", "raw_payload_display"]
    search_fields = ["label", "backend_used", "backend_reference"]
    ordering = ["label"]
    list_per_page = 20
    list_display_links = None
    change_list_template = "admin/change_list.html"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_list_display_links(self, request, list_display):
        return None

    def get_queryset(self, request):
        query = (request.GET.get("q") or "").strip()
        backend_name = (request.GET.get("backend") or "").strip()
        configs = []

        if backend_name:
            try:
                backend = AddressBackendInfo.objects.get(pk=backend_name)
            except AddressBackendInfo.DoesNotExist:
                backend = None
            if backend:
                backend_config = get_backend_config_for_path(backend.class_path)
                if backend_config:
                    configs = [backend_config]
        else:
            configs = get_backend_configs()

        data = []
        if configs and query:
            for entry in build_address_suggestions(configs, query):
                raw = entry.get("raw") or {}
                obj = AddressLookup(
                    label=entry.get("label") or "",
                    backend_used=raw.get("backend_used") or raw.get("backend") or "",
                    backend_reference=raw.get("backend_reference") or "",
                    raw_payload=raw,
                )
                data.append(obj)

        return AddressLookupQuerySet(model=AddressLookup, data=data)

    @admin.display(description=_("Raw payload"))
    def raw_payload_display(self, obj: AddressLookup):
        if not obj.raw_payload:
            return "—"
        payload = json.dumps(obj.raw_payload, indent=2, ensure_ascii=False)
        if len(payload) > 512:
            payload = payload[:512] + "…"
        return format_html(
            '<pre style="white-space: pre-wrap; max-width: 520px;">{}</pre>',
            payload,
        )


__all__ = ["AddressBackendInfoAdmin", "AddressLookupAdmin"]
