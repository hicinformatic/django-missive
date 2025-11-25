"""Admin for virtual address backend diagnostics."""

from __future__ import annotations

from django.conf import settings
from django.contrib import admin
from django.core.exceptions import (
    MultipleObjectsReturned,
    ObjectDoesNotExist,
    PermissionDenied,
)
from django.http import Http404, JsonResponse
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from ..models.address_backend import AddressBackendInfo


@admin.register(AddressBackendInfo)
class AddressBackendInfoAdmin(admin.ModelAdmin):
    change_list_template = "admin/missive/addressbackendinfo/change_list.html"
    ordering = ["name"]
    list_display = [
        "name",
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
        config = getattr(settings, "MISSIVE_ADDRESS_BACKENDS", None)
        return list(config or [])

    def _get_backend_config_for_path(self, class_path: str | None):
        if not class_path:
            return None
        for backend in self._all_backend_configs():
            if backend.get("class") == class_path:
                return backend
        return None

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
        if not config_list or not term:
            return []
        try:
            from python_missive.helpers import get_address_from_backends
        except ImportError:
            return []

        try:
            result = get_address_from_backends(
                config_list,
                operation="validate",
                address_line1=term,
            )
        except Exception as exc:  # pragma: no cover - defensive
            return [{"label": str(exc), "raw": {"error": str(exc)}}]

        suggestions = result.get("suggestions") or []
        if suggestions:
            rows = []
            for suggestion in suggestions:
                label = (
                    suggestion.get("formatted_address")
                    or suggestion.get("normalized_address")
                    or term
                )
                rows.append({"label": label, "raw": suggestion})
            return rows

        normalized = result.get("normalized_address") or {}
        label = normalized.get("formatted_address") or term
        return [{"label": label, "raw": result}]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "test/",
                self.admin_site.admin_view(self.address_test_view),
                name="missive_address_backends_test",
            ),
            path(
                "test/autocomplete/",
                self.admin_site.admin_view(self.address_test_autocomplete_view),
                name="missive_address_backends_autocomplete",
            ),
            path(
                "<str:backend_name>/test/",
                self.admin_site.admin_view(self.address_backend_test_view),
                name="missive_address_backend_test",
            ),
            path(
                "<str:backend_name>/test/autocomplete/",
                self.admin_site.admin_view(self.address_backend_test_autocomplete_view),
                name="missive_address_backend_autocomplete",
            ),
        ]
        return custom_urls + urls

    # List display helpers ---------------------------------------------
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

    def address_test_view(self, request):
        if not self.has_view_permission(request):
            raise PermissionDenied

        has_backends = bool(self._all_backend_configs())
        context = {
            **self.admin_site.each_context(request),
            "title": _("Test address API"),
            "backend": None,
            "backend_configured": has_backends,
            "can_test": has_backends,
            "autocomplete_url": reverse("admin:missive_address_backends_autocomplete"),
            "diagnostics_url": reverse("missive:address-backends-status"),
            "opts": AddressBackendInfo._meta,
        }
        return TemplateResponse(
            request, "admin/missive/addressbackendinfo/test.html", context
        )

    def address_backend_test_view(self, request, backend_name):
        if not self.has_view_permission(request):
            raise PermissionDenied

        backend = self._get_backend_info(backend_name)
        if backend is None:
            raise Http404(_("Backend not found"))

        backend_config = self._get_backend_config_for_path(backend.class_path)
        context = {
            **self.admin_site.each_context(request),
            "title": _("Test address API"),
            "backend": backend,
            "backend_configured": bool(backend_config),
            "can_test": bool(backend_config),
            "autocomplete_url": reverse(
                "admin:missive_address_backend_autocomplete", args=[backend_name]
            ),
            "diagnostics_url": reverse("missive:address-backends-status"),
            "opts": AddressBackendInfo._meta,
        }
        return TemplateResponse(
            request, "admin/missive/addressbackendinfo/test.html", context
        )

    def address_test_autocomplete_view(self, request, backend_name=None):
        if not self.has_view_permission(request):
            raise PermissionDenied

        term = (request.GET.get("term") or "").strip()
        config: list[dict] = []
        if backend_name:
            backend = self._get_backend_info(backend_name)
            class_path = backend.class_path if backend else None
            entry = self._get_backend_config_for_path(class_path)
            if entry:
                config = [entry]
        else:
            config = self._all_backend_configs()
        results = self._build_results(config, term)
        return JsonResponse({"results": results})

    def address_backend_test_autocomplete_view(self, request, backend_name):
        return self.address_test_autocomplete_view(request, backend_name=backend_name)


__all__ = ["AddressBackendInfoAdmin"]
