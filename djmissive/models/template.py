"""MissiveTemplate model."""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from .choices import MissiveType


class MissiveTemplate(models.Model):
    """Reusable missive template."""

    name = models.CharField(
        max_length=255,
        verbose_name=_("Template Name"),
        help_text=_("Template name for easy retrieval"),
    )
    missive_type = models.CharField(
        max_length=20,
        choices=MissiveType.choices,
        verbose_name=_("Missive Type"),
        help_text=_("Type of missive for which this template will be used"),
    )
    subject_template = models.CharField(
        max_length=255,
        verbose_name=_("Subject Template"),
        help_text=_("Can contain variables: {{variable}}"),
    )
    body_template = models.TextField(
        verbose_name=_("Body Template"),
        help_text=_("Can contain variables: {{variable}}"),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Disable to hide this template without deleting it"),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_templates",
        verbose_name=_("Created By"),
        help_text=_("User who created this template"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Creation Date"),
        help_text=_("Automatic creation date of the template"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Modification Date"),
        help_text=_("Automatic last modification date"),
    )

    class Meta:
        verbose_name = _("Missive Template")
        verbose_name_plural = _("Missive Templates")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_missive_type_display()})"
