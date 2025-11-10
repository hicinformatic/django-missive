"""
Administration pour le modèle MissiveEvent.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ..models import MissiveEvent


class MissiveEventInline(admin.TabularInline):
    """Inline pour l'historique des événements"""

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
        """Empêche l'ajout d'événements via l'admin"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Empêche la suppression d'événements via l'admin"""
        return False


@admin.register(MissiveEvent)
class MissiveEventAdmin(admin.ModelAdmin):
    """Admin pour les événements (lecture seule)"""

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
            _("Événement"),
            {"fields": ("missive", "event_type", "provider", "status")},
        ),
        (_("Détails"), {"fields": ("description", "metadata", "created_at")}),
    )

    def has_add_permission(self, request):
        """Les événements ne peuvent pas être créés manuellement"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Les événements ne peuvent pas être supprimés"""
        return False

    def has_change_permission(self, request, obj=None):
        """Les événements ne peuvent pas être modifiés"""
        return False
