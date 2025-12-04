"""Administration du modèle MissiveEvent."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ..decorators import library_presence_warning, sandbox_warning
from ..models import MissiveEvent


class MissiveEventInline(admin.TabularInline):
    """Inline de l'historique des événements."""

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
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@sandbox_warning
@library_presence_warning
@admin.register(MissiveEvent)
class MissiveEventAdmin(admin.ModelAdmin):
    """Administration des événements (lecture seule)."""

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
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
