"""Recipient model."""

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from .choices import RecipientType


class Recipient(models.Model):
    """Recipient with contact details, linkable to any model via GenericForeignKey."""

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Object Type"),
        help_text=_("Linked object type (Customer, Contact, etc.)"),
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Object ID"),
        help_text=_("Linked object ID"),
    )
    content_object = GenericForeignKey("content_type", "object_id")

    recipient_type = models.CharField(
        max_length=20,
        choices=RecipientType.choices,
        default=RecipientType.INDIVIDUAL,
        verbose_name=_("Recipient Type"),
        help_text=_("Individual, Company or Administration"),
    )

    civility = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_("Civility"),
        help_text=_("Mr., Mrs., Dr, etc."),
    )
    name = models.CharField(
        max_length=255,
        default="",
        verbose_name=_("Name"),
        help_text=_(
            "Full name (person) or denomination (company/administration)"
        ),
    )

    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name=_("Email"),
        help_text=_("Recipient's email address"),
    )
    mobile = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Mobile Phone"),
        help_text=_(
            "Mobile phone number in international format (e.g., +33 6 12 34 56 78)"
        ),
    )

    address_line1 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Address Line 1"),
        help_text=_("Street number and name"),
    )
    address_line2 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Address Line 2"),
        help_text=_("Building, apartment, floor (optional)"),
    )
    address_line3 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Address Line 3"),
        help_text=_("Additional address info (optional)"),
    )
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Postal Code"),
        help_text=_("Postal code"),
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("City"),
        help_text=_("City"),
    )
    state = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("State/Region"),
        help_text=_("Region, department or state"),
    )
    country = models.CharField(
        max_length=2,
        blank=True,
        default="FR",
        verbose_name=_("Country (ISO code)"),
        help_text=_("ISO country code (FR, BE, CH, etc.)"),
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes"),
        help_text=_("Internal notes about this recipient"),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Disable to hide this recipient without deleting them"),
    )

    can_be_sender = models.BooleanField(
        default=False,
        verbose_name=_("Usable as Sender"),
        help_text=_(
            "Check if this recipient can be used as a missive sender"
        ),
    )
    is_default_sender = models.BooleanField(
        default=False,
        verbose_name=_("Default Sender"),
        help_text=_("Only one default sender possible in the system"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created On"),
        help_text=_("Automatic creation date"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Modified On"),
        help_text=_("Automatic last modification date"),
    )

    class Meta:
        verbose_name = _("Recipient")
        verbose_name_plural = _("Recipients")
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["email"]),
            models.Index(fields=["mobile"]),
            models.Index(fields=["content_type", "object_id"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["email"],
                condition=models.Q(email__isnull=False) & ~models.Q(email=""),
                name="unique_email",
                violation_error_message=_("A recipient with this email already exists"),
            ),
            models.UniqueConstraint(
                fields=["mobile"],
                condition=models.Q(mobile__isnull=False) & ~models.Q(mobile=""),
                name="unique_mobile",
                violation_error_message=_("A recipient with this mobile already exists"),
            ),
            models.UniqueConstraint(
                fields=["name", "address_line1", "postal_code", "city"],
                condition=models.Q(address_line1__isnull=False)
                & ~models.Q(address_line1=""),
                name="unique_postal_address",
                violation_error_message=_(
                    "A recipient with this address already exists"
                ),
            ),
        ]

    def __str__(self):
        """Returns recipient name with primary contact."""
        name_part = self.full_name or f"Recipient #{self.id}"
        contact = self.primary_contact
        if contact:
            return f"{name_part} - {contact}"
        return name_part

    @property
    def full_name(self):
        """Returns the full name with civility"""
        if self.civility and self.name:
            return f"{self.civility} {self.name}"
        return self.name or ""

    @property
    def display_name(self):
        """Display name"""
        return self.full_name or self.email or self.mobile or f"Recipient #{self.id}"

    @property
    def postal_address(self):
        """Formatted postal address for printing"""
        lines = []

        # Name
        if self.full_name:
            lines.append(self.full_name)

        # Address
        if self.address_line1:
            lines.append(self.address_line1)
        if self.address_line2:
            lines.append(self.address_line2)
        if self.address_line3:
            lines.append(self.address_line3)

        # City
        city_line = []
        if self.postal_code:
            city_line.append(self.postal_code)
        if self.city:
            city_line.append(self.city)
        if city_line:
            lines.append(" ".join(city_line))

        # Region/Country
        if self.state:
            lines.append(self.state)
        if self.country and self.country != "FR":
            lines.append(self.country)

        return "\n".join(lines)

    @property
    def primary_contact(self):
        """Returns the primary contact: email, mobile phone or address (1st line)"""
        if self.email:
            return self.email
        elif self.mobile:
            return self.mobile
        elif self.address_line1:
            # Returns short address: line1, postal code city
            parts = [self.address_line1]
            if self.postal_code and self.city:
                parts.append(f"{self.postal_code} {self.city}")
            elif self.city:
                parts.append(self.city)
            return ", ".join(parts)
        return None

    def save(self, *args, **kwargs):
        """
        Ensures only one default sender exists.
        If is_default_sender is True, all others are set to False.
        """
        if self.is_default_sender:
            # If marking this one as default sender,
            # remove the flag from others
            Recipient.objects.filter(is_default_sender=True).exclude(pk=self.pk).update(
                is_default_sender=False
            )
            # Automatically enable can_be_sender if it's the default sender
            self.can_be_sender = True

        super().save(*args, **kwargs)
