"""Admin for MissiveEvent model."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ..decorators import sandbox_warning
from ..models import MissiveEvent


class MissiveEventInline(admin.TabularInline):
    """Inline for event history"""

    model = MissiveEvent
    extra = 0
    readonly_fields = [
        "event_type",
        "provider",
        "status",
        "description",
        "metadata",
        "created_at",
    ]
    fields = ["event_type", "provider", "status", "description", "created_at"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        """Prevent adding events via admin"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting events via admin"""
        return False


@sandbox_warning
@admin.register(MissiveEvent)
class MissiveEventAdmin(admin.ModelAdmin):
    """Admin for events (read-only)"""

    list_display = ["event_type", "provider", "missive", "status", "created_at"]
    list_filter = ["event_type", "provider", "status", "created_at"]
    search_fields = ["missive__subject", "description", "provider"]
    readonly_fields = [
        "missive",
        "event_type",
        "provider",
        "status",
        "description",
        "metadata",
        "created_at",
    ]

    fieldsets = (
        (
            _("Event"),
            {"fields": ("missive", "event_type", "provider", "status")},
        ),
        (_("Details"), {"fields": ("description", "metadata", "created_at")}),
    )

    def has_add_permission(self, request):
        """Events cannot be created manually"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Events cannot be deleted"""
        return False

    def has_change_permission(self, request, obj=None):
        """Events cannot be modified"""
        return False
