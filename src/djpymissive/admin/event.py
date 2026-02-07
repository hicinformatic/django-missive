"""Admin for MissiveEvent model."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django_boosted import AdminBoostModel

from ..models.event import MissiveEvent


class MissiveEventInline(admin.TabularInline):
    """Inline for missive events (read-only)."""

    model = MissiveEvent
    extra = 0
    readonly_fields = [
        "event_type",
        "status",
        "description",
        "occurred_at",
    ]
    fields = [
        "event_type",
        "status",
        "description",
        "occurred_at",
    ]
    show_change_link = True
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MissiveEvent)
class MissiveEventAdmin(AdminBoostModel):
    """Admin for missive event model."""

    list_display = [
        "id",
        "event_type",
        "missive",
        "status",
        "occurred_at",
    ]
    list_filter = [
        "event_type",
        "status",
        "occurred_at",
    ]
    search_fields = [
        "event_type",
        "description",
        "missive__subject",
        "missive__recipient_name",
    ]
    readonly_fields = [
        "missive",
        "event_type",
        "status",
        "description",
        "metadata",
        "trace",
        "occurred_at",
    ]
    raw_id_fields = ["missive"]

    fieldsets = [
        (
            None,
            {
                "fields": (
                    "missive",
                    "event_type",
                    "status",
                )
            },
        ),
    ]

    def change_fieldsets(self):
        """Configure fieldsets for change view."""
        self.add_to_fieldset(
            _("Details"),
            ["description", "metadata", "occurred_at"],
        )
        self.add_to_fieldset(
            _("Trace"),
            ["trace"],
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
