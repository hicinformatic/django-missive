from django.db import models
from django.utils.translation import gettext_lazy as _

from phonenumber_field.modelfields import PhoneNumberField
from djgeoaddress.fields import GeoaddressField

from .choices import MissiveRecipientType, MissiveStatus
from ..managers.recipient import MissiveRecipientManager


class MissiveRecipient(models.Model):
    """Recipient model"""

    missive = models.ForeignKey(
        "djpymissive.Missive",
        on_delete=models.CASCADE,
        related_name="to_missiverecipient",
        verbose_name=_("Missive"),
        help_text=_("Missive"),
    )
    recipient_type = models.CharField(
        max_length=20,
        choices=MissiveRecipientType.choices,
        default=MissiveRecipientType.RECIPIENT,
        verbose_name=_("Recipient Type"),
        help_text=_("Type of recipient"),
    )
    status = models.CharField(
        max_length=20,
        choices=MissiveStatus.choices,
        default=MissiveStatus.DRAFT,
        verbose_name=_("Status"),
        help_text=_("Current status of the missive"),
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Name"),
        help_text=_("Full name or company name"),
    )
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name=_("Recipient Email"),
        help_text=_("Recipient's email address"),
    )
    phone = PhoneNumberField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Phone"),
        help_text=_("Phone number"),
    )
    address = GeoaddressField(
        blank=True,
        null=True,
        verbose_name=_("Address"),
        help_text=_("Address"),
    )
    notification_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Notification ID"),
        help_text=_("Notification ID"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
    )
    objects = MissiveRecipientManager()

    class Meta:
        verbose_name = _("Recipient")
        verbose_name_plural = _("Recipients")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.target})"

    @property
    def target(self):
        return self.email or self.phone or self.address

    def get_serialized_data(self):
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "notification_id": self.notification_id,
        }

    @property
    def can_be_modified(self):
        return self.missive.can_be_modified
