"""
Modèle MissiveEvent pour le tracking des événements.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .choices import MissiveStatus


class MissiveEvent(models.Model):
    """Événements et historique de tracking d'une missive"""

    missive = models.ForeignKey(
        "missive.Missive",
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name=_("Missive"),
        help_text=_("Missive associée à cet événement"),
    )
    event_type = models.CharField(
        max_length=50,
        verbose_name=_("Type d'événement"),
        help_text=_("Ex: created, sent, delivered, opened, clicked, bounced, etc."),
    )
    provider = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_("Provider"),
        help_text=_("Provider qui a généré cet événement (sendgrid, twilio, laposte, etc.)"),
    )
    status = models.CharField(
        max_length=20,
        choices=MissiveStatus.choices,
        null=True,
        blank=True,
        verbose_name=_("Statut associé"),
        help_text=_("Statut de la missive suite à cet événement"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Description détaillée de l'événement"),
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Métadonnées"),
        help_text=_("Données additionnelles (IP, user agent, etc.)"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de l'événement"),
        help_text=_("Date et heure de l'événement"),
    )

    class Meta:
        verbose_name = _("Événement")
        verbose_name_plural = _("Événements")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["missive", "-created_at"]),
            models.Index(fields=["event_type"]),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.missive.subject} ({self.created_at})"
