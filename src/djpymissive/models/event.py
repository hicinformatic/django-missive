"""MissiveEvent model for tracking missive events."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .choices import MissiveStatus


class MissiveEvent(models.Model):
    """Event tracking for missives (status changes, webhooks, etc.)."""

    missive = models.ForeignKey(
        "djpymissive.Missive",
        on_delete=models.CASCADE,
        related_name="to_missiveevent",
        verbose_name=_("Missive"),
        help_text=_("Missive associated with this event"),
    )

    event_type = models.CharField(
        max_length=100,
        verbose_name=_("Event Type"),
        help_text=_("Type of event (sent, delivered, read, failed, etc.)"),
    )

    status = models.CharField(
        max_length=50,
        choices=MissiveStatus.choices,
        null=True,
        blank=True,
        verbose_name=_("Status"),
        help_text=_("Status associated with this event"),
    )

    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Description or details about this event"),
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Metadata"),
        help_text=_("Additional metadata as JSON"),
    )

    trace = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Trace"),
        help_text=_("Raw trace data (webhook payload, API response, etc.)"),
    )

    occurred_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Occurred At"),
        help_text=_("When this event occurred"),
    )

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")
        ordering = ["-occurred_at"]

    def __str__(self):
        return f"{self.missive} - {self.event_type} ({self.occurred_at})"
