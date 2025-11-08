"""
Modèle MissiveTemplate pour les templates réutilisables.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from .choices import MissiveType


class MissiveTemplate(models.Model):
    """Templates réutilisables pour les missives"""

    name = models.CharField(max_length=255, verbose_name=_("Nom du template"))
    missive_type = models.CharField(
        max_length=20, choices=MissiveType.choices, verbose_name=_("Type de missive")
    )
    subject_template = models.CharField(
        max_length=255,
        verbose_name=_("Template du sujet"),
        help_text=_("Peut contenir des variables : {{variable}}"),
    )
    body_template = models.TextField(
        verbose_name=_("Template du corps"),
        help_text=_("Peut contenir des variables : {{variable}}"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Actif"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_templates",
        verbose_name=_("Créé par"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de modification")
    )

    class Meta:
        verbose_name = _("Template de missive")
        verbose_name_plural = _("Templates de missives")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_missive_type_display()})"
