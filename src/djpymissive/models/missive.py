"""Modèle Missive principal pour l'envoi multi-canal."""

import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from djgeoaddress.fields import GeoaddressField

from djproviderkit import ProviderField

from .choices import AcknowledgementLevel, MissivePriority, MissiveStatus, MissiveType
from ..managers import MissiveManager

class Missive(models.Model):
    """Modèle de missive multi-canal (email, SMS, postal, WhatsApp, etc.)."""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )
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
    sender_address = GeoaddressField(
        blank=True,
        null=True,
        verbose_name=_("Sender Address"),
        help_text=_("Sender's address"),
    )

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
    recipient_address = GeoaddressField(
        blank=True,
        null=True,
        verbose_name=_("Recipient Address"),
        help_text=_("Recipient's address"),
    )

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

    external_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        editable=False,
        verbose_name=_("External ID"),
        help_text=_("External identifier from the provider"),
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Metadata"),
        help_text=_("Additional metadata as JSON"),
    )

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

    objects = MissiveManager()

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
        recipient = self.recipient_name or self.recipient_email or 'Unknown'
        return f"{self.missive_type} - {recipient} ({self.status})"

    def clean(self):
        super().clean()
        
        if not self.sender_name:
            raise ValidationError({
                'sender_name': _('Sender name is required.'),
            })
        
        recipient_email = self.recipient_email
        recipient_phone = self.recipient_phone
        recipient_address = self.recipient_address
        
        has_recipient_address = (
            recipient_address is not None
            and isinstance(recipient_address, dict)
            and bool(recipient_address)
        )
        
        if not recipient_email and not recipient_phone and not has_recipient_address:
            raise ValidationError({
                'recipient_email': _('At least one recipient information (email, phone, or address) must be provided.'),
                'recipient_phone': _('At least one recipient information (email, phone, or address) must be provided.'),
                'recipient_address': _('At least one recipient information (email, phone, or address) must be provided.'),
            })
        
        self.clean_email()
        self.clean_address()
        self.clean_phone()

    def clean_email(self):
        recipient_email = self.recipient_email
        sender_email = self.sender_email
        
        if recipient_email and not sender_email:
            raise ValidationError({
                'sender_email': _('Sender email is required when recipient email is provided.'),
            })

    def clean_address(self):
        recipient_address = self.recipient_address
        sender_address = self.sender_address
        
        has_recipient_address = (
            recipient_address is not None
            and isinstance(recipient_address, dict)
            and bool(recipient_address)
        )
        
        if has_recipient_address:
            has_sender_address = (
                sender_address is not None
                and isinstance(sender_address, dict)
                and bool(sender_address)
            )
            if not has_sender_address:
                raise ValidationError({
                    'sender_address': _('Sender address is required when recipient address is provided.'),
                })

    def clean_phone(self):
        pass

    def get_target(self, prefix: str):
        fields = ["email", "phone", "address"]
        return next((getattr(self, f"{prefix}_{field}") for field in fields if getattr(self, f"{prefix}_{field}", None)), None)

    @property
    def sender(self):
        return self.get_target("sender")

    @property
    def recipient(self):
        return self.get_target("recipient")