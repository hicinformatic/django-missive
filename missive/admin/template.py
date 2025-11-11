"""Admin for MissiveTemplate model."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ..decorators import sandbox_warning
from ..models import MissiveTemplate


@sandbox_warning
@admin.register(MissiveTemplate)
class MissiveTemplateAdmin(admin.ModelAdmin):
    """Admin for missive templates"""

    list_display = ["name", "missive_type", "is_active", "created_at"]
    list_filter = ["missive_type", "is_active", "created_at"]
    search_fields = ["name", "description", "subject_template", "body_template"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            _("Informations générales"),
            {"fields": ("name", "missive_type", "is_active", "created_by")},
        ),
        (
            _("Template"),
            {
                "fields": ("subject_template", "body_template"),
                "description": _("Utilisez {{variable}} pour les variables dynamiques"),
            },
        ),
        (
            _("Dates"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
