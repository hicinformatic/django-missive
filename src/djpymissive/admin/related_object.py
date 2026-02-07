"""Admin for MissiveRelatedObject model."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django_boosted import AdminBoostModel

from ..models.related_object import MissiveRelatedObject


class MissiveRelatedObjectInline(admin.TabularInline):
    """Inline for missive related objects."""

    model = MissiveRelatedObject
    extra = 0
    fields = [
        "content_type",
        "object_id",
    ]
    readonly_fields = []
    raw_id_fields = ["content_type"]


@admin.register(MissiveRelatedObject)
class MissiveRelatedObjectAdmin(AdminBoostModel):
    """Admin for missive related object model."""

    list_display = [
        "id",
        "missive",
        "content_type",
        "object_id",
        "content_object",
        "created_at",
    ]
    list_filter = [
        "content_type",
        "created_at",
    ]
    search_fields = [
        "missive__subject",
        "missive__recipient_name",
        "missive__recipient_email",
    ]
    readonly_fields = [
        "created_at",
    ]
    raw_id_fields = ["missive", "content_type"]

    def change_fieldsets(self):
        """Configure fieldsets for change view."""
        self.add_to_fieldset(
            None,
            ["missive", "content_type", "object_id", "content_object"],
        )
        self.add_to_fieldset(
            _("Timestamps"),
            ["created_at"],
        )
