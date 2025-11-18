"""Administration du modèle virtuel ProviderInfo."""

import importlib
import json

from django.contrib import admin
from django.utils.html import format_html, format_html_join
from django.utils.translation import gettext_lazy as _

from ..decorators import sandbox_warning, library_presence_warning
from ..models import MissiveType, ProviderInfo
from ..models.provider import ProviderInfoQuerySet


class MissiveTypeFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour afficher les types avec leurs labels traduits."""

    title = _("Missive Type")
    parameter_name = "missive_type"

    def lookups(self, request, model_admin):
        return [(choice.value, choice.label) for choice in MissiveType]

    def queryset(self, request, queryset):
        if self.value():
            filtered = []
            for provider in queryset:
                if self.value() in provider.missive_types_list:
                    filtered.append(provider)
            return ProviderInfoQuerySet(
                model=queryset.model,
                data=filtered,
                query=queryset.query,
                using=queryset._db,
                hints=queryset._hints,
            )
        return queryset


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

    list_filter = [MissiveTypeFilter]

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
        attachment_types = {"EMAIL", "POSTAL", "BRANDED"}
        
        for missive_type in missive_types:
            try:
                label = MissiveType(missive_type).label
            except ValueError:
                label = missive_type

            service_info_field = f"service_info_{missive_type.lower()}_display"
            geo_field = f"geo_{missive_type.lower()}_display"
            
            fields = [service_info_field, geo_field]
            
            # Add attachment limits for types that support attachments
            if missive_type in attachment_types:
                attachment_field = f"attachment_limits_{missive_type.lower()}_display"
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
            attachment_types = {"EMAIL", "POSTAL", "BRANDED"}
            for missive_type in obj.missive_types_list:
                service_info_field = f"service_info_{missive_type.lower()}_display"
                geo_field = f"geo_{missive_type.lower()}_display"
                if service_info_field not in readonly:
                    readonly.append(service_info_field)
                if geo_field not in readonly:
                    readonly.append(geo_field)
                
                # Add attachment limits for types that support attachments
                if missive_type in attachment_types:
                    attachment_field = f"attachment_limits_{missive_type.lower()}_display"
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

                        method_map = {
                            "SMS": "get_sms_service_info",
                            "EMAIL": "get_email_service_info",
                            "POSTAL": "get_postal_service_info",
                            "VOICE_CALL": "get_voice_call_service_info",
                            "NOTIFICATION": "get_notification_service_info",
                            "PUSH_NOTIFICATION": "get_push_notification_service_info",
                            "BRANDED": "get_branded_service_info",
                        }

                        method_name = method_map.get(missive_type)

                        if method_name and hasattr(provider_instance, method_name):
                            service_info = getattr(provider_instance, method_name)()
                            # Return raw response as JSON string
                            return json.dumps(service_info, indent=2, ensure_ascii=False)
                        else:
                            return json.dumps({
                                "error": f"Method {method_name} not implemented for {provider_instance.name}"
                            }, indent=2, ensure_ascii=False)
                    else:
                        return json.dumps({"error": "Provider not loaded"}, indent=2, ensure_ascii=False)

                except Exception as e:
                    return json.dumps({"error": str(e)}, indent=2, ensure_ascii=False)

            service_info_method.short_description = _("Service Information")
            return service_info_method

        if name.startswith("geo_") and name.endswith("_display"):
            missive_type = name[4:-8].upper()

            def geo_method(obj):
                try:
                    provider_class = obj._get_provider_class()
                    if provider_class:
                        provider_instance = provider_class()

                        # Map missive type to geo attribute name
                        geo_attr_map = {
                            "SMS": "sms_geo",
                            "EMAIL": "email_geo",
                            "POSTAL": "postal_geo",
                            "VOICE_CALL": "voice_call_geo",
                            "NOTIFICATION": "notification_geo",
                            "PUSH_NOTIFICATION": "push_notification_geo",
                            "BRANDED": "branded_geo",
                            "LRE": "lre_geo",
                        }

                        geo_attr = geo_attr_map.get(missive_type)

                        if geo_attr:
                            # Search through MRO and __dict__ to find the attribute
                            for cls in provider_class.__mro__:
                                if hasattr(cls, "__dict__") and geo_attr in cls.__dict__:
                                    geo_value = cls.__dict__[geo_attr]
                                    # Return raw value directly
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
                            return "Not applicable"

                    else:
                        return "Provider not loaded"

                except Exception as e:
                    return f"Error: {str(e)}"

            geo_method.short_description = _("Geographic Coverage")
            return geo_method

        if name.startswith("attachment_limits_") and name.endswith("_display"):
            missive_type = name[18:-8].upper()

            def attachment_limits_method(obj):
                try:
                    provider_class = obj._get_provider_class()
                    if provider_class:
                        provider_instance = provider_class()

                        limits_info = {}

                        # EMAIL attachments
                        if missive_type == "EMAIL":
                            if hasattr(provider_instance, "max_email_attachment_size_mb"):
                                limits_info["max_size_mb"] = provider_instance.max_email_attachment_size_mb
                                limits_info["max_size_bytes"] = provider_instance.max_email_attachment_size_bytes
                            if hasattr(provider_instance, "allowed_attachment_mime_types"):
                                limits_info["allowed_mime_types"] = provider_instance.allowed_attachment_mime_types

                        # POSTAL attachments
                        elif missive_type == "POSTAL":
                            if hasattr(provider_instance, "max_postal_pages"):
                                limits_info["max_pages"] = provider_instance.max_postal_pages
                            if hasattr(provider_instance, "allowed_attachment_mime_types"):
                                limits_info["allowed_mime_types"] = provider_instance.allowed_attachment_mime_types
                            if hasattr(provider_instance, "allowed_page_formats"):
                                limits_info["allowed_page_formats"] = provider_instance.allowed_page_formats

                        # BRANDED attachments
                        elif missive_type == "BRANDED":
                            if hasattr(provider_instance, "max_attachment_size_mb"):
                                limits_info["max_size_mb"] = provider_instance.max_attachment_size_mb
                                limits_info["max_size_bytes"] = provider_instance.max_attachment_size_bytes
                            if hasattr(provider_instance, "allowed_attachment_mime_types"):
                                limits_info["allowed_mime_types"] = provider_instance.allowed_attachment_mime_types

                        if limits_info:
                            return json.dumps(limits_info, indent=2, ensure_ascii=False)
                        else:
                            return json.dumps({"message": "No attachment limits configured"}, indent=2, ensure_ascii=False)

                    else:
                        return json.dumps({"error": "Provider not loaded"}, indent=2, ensure_ascii=False)

                except Exception as e:
                    return json.dumps({"error": str(e)}, indent=2, ensure_ascii=False)

            attachment_limits_method.short_description = _("Attachment Limits")
            return attachment_limits_method

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return True

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

    name_display.short_description = _("Provider")

    def missive_type_display(self, obj):
        """Badges colorés pour tous les types supportés."""
        colors = {
            "POSTAL": "#6c757d",
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

    missive_type_display.short_description = _("Types supportés")

    def missive_type_display_detail(self, obj):
        return self.missive_type_display(obj)

    missive_type_display_detail.short_description = _("Types supportés")

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

    brands_display.short_description = _("Supported Brands")

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

    status_display.short_description = _("Status")

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

    credits_display.short_description = _("Credits")

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

    installation_display.short_description = _("Packages")

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

    configuration_display.short_description = _("Credentials")

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

    status_url_display.short_description = _("SLA Status")

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

    site_url_display.short_description = _("Official Site")
    documentation_url_display.short_description = _("Documentation")

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

        type_labels = {
            "EMAIL": "Email",
            "SMS": "SMS",
            "VOICE_CALL": "Voice Calls",
            "BRANDED": "Messaging",
            "POSTAL": "Postal",
            "LRE": "LRE",
            "NOTIFICATION": "Notifications",
            "PUSH_NOTIFICATION": "Push",
            "RCS": "RCS",
        }

        type_names = [type_labels.get(t, t) for t in types]
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

    webhook_urls_display.short_description = _("Webhook URLs")

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

    usage_display.short_description = _("Usage")

    def status_display_detail(self, obj):
        return self.status_display(obj)

    status_display_detail.short_description = _("Status")

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

    config_vars_display.short_description = _("Variables")

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

    config_vars_display_detail.short_description = _("Configuration Variables")

    def changelist_view(self, request, extra_context=None):
        """Ajoute du contexte à la vue liste."""
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
