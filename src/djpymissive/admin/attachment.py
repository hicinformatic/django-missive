"""Admin for MissiveAttachment model."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django_boosted import AdminBoostModel

from ..models.attachment import MissiveAttachment


class MissiveAttachmentInline(admin.TabularInline):
    """Inline for missive attachments."""

    model = MissiveAttachment
    extra = 0
    readonly_fields = [
        "file_object",
        "file_display",
    ]
    fields = [
        "file",
        "file_content_type",
        "file_object_id",
        "file_method_access",
        "files_object_arguments",
        "multiple_files",
        "order",
    ]

    @admin.display(description=_("File"))
    def file_display(self, obj):
        """Display file name or method access."""
        if obj and obj.pk:
            if obj.file:
                return obj.file.name
            elif obj.file_method_access:
                return f"Method: {obj.file_method_access}"
        return "-"


@admin.register(MissiveAttachment)
class MissiveAttachmentAdmin(AdminBoostModel):
    """Admin for missive attachment model."""

    list_display = [
        "id",
        "file_display",
        "missive",
        "order",
    ]
    list_filter = [
        "missive__missive_type",
    ]
    search_fields = [
        "missive__subject",
        "missive__recipient_name",
    ]
    readonly_fields = [
        "file_object",
        "file_display",
    ]
    raw_id_fields = ["missive", "file_content_type"]

    @admin.display(description=_("File"))
    def file_display(self, obj):
        """Display file name or method access."""
        if obj.file:
            return obj.file.name
        elif obj.file_method_access:
            return f"Method: {obj.file_method_access}"
        return "-"

    fieldsets = [
        (
            None,
            {
                "fields": (
                    "missive",
                    "file",
                    "file_metadata",
                    "order",
                )
            },
        ),
    ]

    def change_fieldsets(self):
        """Configure fieldsets for change view."""
        self.add_to_fieldset(
            _("File Object"),
            ["file_content_type", "file_object_id", "file_method_access", "files_object_arguments", "file_object", "multiple_files"],
        )
