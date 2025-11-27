"""Administration du modèle MissiveAttachment."""

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from ..decorators import library_presence_warning, sandbox_warning
from ..models import MissiveAttachment


class MissiveAttachmentInline(admin.StackedInline):
    """Inline des pièces jointes."""

    model = MissiveAttachment
    extra = 1
    readonly_fields = [
        "created_at",
        "file_url_display",
        "attached_to_display",
        "file_size",
        "mime_type",
    ]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "file",
                    "external_url",
                    "file_url_display",
                    "content_type",
                    "object_id",
                    "attached_to_display",
                    "order",
                )
            },
        ),
        (
            _("Metadata"),
            {
                "fields": (
                    "file_size",
                    "mime_type",
                    "created_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description=_("Link"))
    def file_url_display(self, obj):
        """Displays file link."""
        if obj and obj.file_url:
            icon = "🔗" if obj.is_external else "📎"
            return format_html(
                '<a href="{}" target="_blank">{} View file</a>',
                obj.file_url,
                icon,
            )
        return "-"

    @admin.display(description=_("Attached to"))
    def attached_to_display(self, obj):
        """Displays attached object."""
        if not obj or not obj.pk:
            return "-"

        attached = obj.attached_to
        if not attached:
            return "-"

        try:
            if obj.content_object:
                ct = obj.content_type
                url = reverse(
                    f"admin:{ct.app_label}_{ct.model}_change", args=[obj.object_id]
                )
                label = str(obj.content_object)
                if len(label) > 40:
                    label = label[:37] + "..."
                return format_html('<a href="{}">{}</a>', url, label)
        except Exception:
            return str(attached)

        return str(attached)

        return str(attached)


@sandbox_warning
@library_presence_warning
@admin.register(MissiveAttachment)
class MissiveAttachmentAdmin(admin.ModelAdmin):
    """Administration des pièces jointes."""

    raw_id_fields = ["missive"]

    list_display = [
        "id",
        "attached_to_display",
        "storage_type_badge",
        "file_size_display",
        "mime_type",
        "order",
        "created_at",
    ]
    list_filter = ["mime_type", "content_type", "created_at"]
    search_fields = [
        "missive__subject",
        "content_type__model",
        "content_type__app_label",
    ]
    readonly_fields = [
        "created_at",
        "file_url_display",
        "attached_to_display",
        "file_size",
        "mime_type",
    ]
    list_editable = ["order"]
    list_display_links = ["id"]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "missive",
                    "file",
                    "external_url",
                    "file_url_display",
                    "content_type",
                    "object_id",
                    "attached_to_display",
                    "order",
                ),
                "description": _(
                    "Provide either a local file or external URL, optionally linked to another object"
                ),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("file_size", "mime_type", "created_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description=_("Storage"))
    def storage_type_badge(self, obj):
        """Badge du type de stockage."""
        if obj.is_external:
            return format_html(
                '<span style="background-color: #0dcaf0; color: white; padding: 2px 8px; '
                'border-radius: 3px; font-size: 10px; white-space: nowrap;">🔗 External</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #198754; color: white; padding: 2px 8px; '
                'border-radius: 3px; font-size: 10px; white-space: nowrap;">📎 Local</span>'
            )

    @admin.display(description=_("Attached to"))
    def attached_to_display(self, obj):
        """Displays attached object."""
        attached = obj.attached_to
        if not attached:
            return "-"

        try:
            if obj.missive:
                url = reverse("admin:missive_missive_change", args=[obj.missive.id])
                return format_html(
                    '<a href="{}">📧 Missive #{}</a>', url, obj.missive.id
                )
            elif obj.content_object:
                ct = obj.content_type
                url = reverse(
                    f"admin:{ct.app_label}_{ct.model}_change", args=[obj.object_id]
                )
                label = str(obj.content_object)
                if len(label) > 40:
                    label = label[:37] + "..."
                return format_html('<a href="{}">{}</a>', url, label)
        except Exception:
            return str(attached)

        return str(attached)

    @admin.display(description=_("Size"))
    def file_size_display(self, obj):
        """Displays formatted size."""
        if obj.file_size:
            if obj.file_size < 1024:
                return f"{obj.file_size} B"
            elif obj.file_size < 1024 * 1024:
                return f"{obj.file_size / 1024:.1f} KB"
            else:
                return f"{obj.file_size / (1024 * 1024):.1f} MB"
        return "-"

    @admin.display(description=_("Link"))
    def file_url_display(self, obj):
        """Displays file link."""
        if obj.file_url:
            icon = "🔗" if obj.is_external else "📎"
            return format_html(
                '<a href="{}" target="_blank">{} Download/View</a>',
                obj.file_url,
                icon,
            )
        return "-"
