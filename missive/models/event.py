"""MissiveEvent model for tracking."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .choices import MissiveStatus


class MissiveEvent(models.Model):
    """Missive event tracking."""

    missive = models.ForeignKey(
        "missive.Missive",
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name=_("Missive"),
        help_text=_("Missive associated with this event"),
    )
    event_type = models.CharField(
        max_length=50,
        verbose_name=_("Event Type"),
        help_text=_("E.g.: created, sent, delivered, opened, clicked, bounced, etc."),
    )
    provider = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_("Provider"),
        help_text=_(
            "Provider that generated this event (sendgrid, twilio, laposte, etc.)"
        ),
    )
    status = models.CharField(
        max_length=20,
        choices=MissiveStatus.choices,
        null=True,
        blank=True,
        verbose_name=_("Associated Status"),
        help_text=_("Missive status following this event"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Detailed event description"),
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Metadata"),
        help_text=_("Additional data (IP, user agent, etc.)"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Event Date"),
        help_text=_("Event date and time"),
    )

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["missive", "-created_at"]),
            models.Index(fields=["event_type"]),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.missive.subject} ({self.created_at})"
