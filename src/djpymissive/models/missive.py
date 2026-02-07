"""Main Missive model for multi-channel sending."""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

try:
    from phonenumber_field.modelfields import PhoneNumberField
except ImportError:
    PhoneNumberField = models.CharField

from djproviderkit import ProviderField

from .choices import AcknowledgementLevel, MissivePriority, MissiveStatus, MissiveType


class Missive(models.Model):
    """Multi-channel missive model (email, SMS, postal, WhatsApp, etc.)."""
    # Provider and external tracking
    provider = ProviderField(
        package_name='pymissive',
        blank=True,
        verbose_name=_("Provider"),
        help_text=_("Provider used to send this missive"),
    )
    missive_type = models.CharField(
        max_length=50,
        choices=MissiveType.choices,
        verbose_name=_("Missive Type"),
        help_text=_("Type of missive (email, SMS, postal, etc.)"),
    )
    acknowledgement = models.CharField(
        max_length=50,
        choices=AcknowledgementLevel.choices,
        blank=True,
        null=True,
        verbose_name=_("Acknowledgement Level"),
        help_text=_("Desired acknowledgement level for delivery proof"),
    )


    # Status
    status = models.CharField(
        max_length=50,
        choices=MissiveStatus.choices,
        default=MissiveStatus.DRAFT,
        verbose_name=_("Status"),
        help_text=_("Current status of the missive"),
    )
    priority = models.CharField(
        max_length=20,
        choices=MissivePriority.choices,
        default=MissivePriority.NORMAL,
        verbose_name=_("Priority"),
        help_text=_("Priority level"),
    )
    # Sender fields
    sender_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Sender Name"),
        help_text=_("Sender's full name or company name"),
    )
    sender_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name=_("Sender Email"),
        help_text=_("Sender's email address"),
    )
    sender_phone = PhoneNumberField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Sender Phone"),
        help_text=_("Sender's phone number"),
    )

    # Recipient fields
    recipient_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Recipient Name"),
        help_text=_("Recipient's full name or company name"),
    )
    recipient_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name=_("Recipient Email"),
        help_text=_("Recipient's email address"),
    )
    recipient_phone = PhoneNumberField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Recipient Phone"),
        help_text=_("Recipient's phone number"),
    )

    # Content fields
    subject = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Subject"),
        help_text=_("Subject line (for email, SMS, etc.)"),
    )
    body = models.TextField(
        blank=True,
        verbose_name=_("Body"),
        help_text=_("Message body/content"),
    )

    # Tracking
    external_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("External ID"),
        help_text=_("External identifier from the provider"),
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Metadata"),
        help_text=_("Additional metadata as JSON"),
    )


    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Sent At"),
        help_text=_("When the missive was sent"),
    )
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Delivered At"),
        help_text=_("When the missive was delivered"),
    )

    class Meta:
        verbose_name = _("Missive")
        verbose_name_plural = _("Missives")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["missive_type", "status"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["provider", "external_id"]),
        ]

    def __str__(self):
        return f"{self.missive_type} - {self.recipient_name or self.recipient_email or 'Unknown'} ({self.status})"
