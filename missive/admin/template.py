"""Administration du modèle MissiveTemplate."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ..decorators import library_presence_warning, sandbox_warning
from ..models import MissiveTemplate


@sandbox_warning
@library_presence_warning
@admin.register(MissiveTemplate)
class MissiveTemplateAdmin(admin.ModelAdmin):
    """Administration des modèles de missive."""

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
                "description": _("Use {{variable}} for dynamic variables"),
            },
        ),
        (
            _("Dates"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
