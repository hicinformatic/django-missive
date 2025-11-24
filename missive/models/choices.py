"""Missive model choices."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class RecipientType(models.TextChoices):
    """Recipient types."""

    INDIVIDUAL = "INDIVIDUAL", _("Individual")
    COMPANY = "COMPANY", _("Company")
    ADMINISTRATION = "ADMINISTRATION", _("Administration")


class MissiveType(models.TextChoices):
    """Missive types."""

    POSTAL = "POSTAL", _("Postal mail")
    POSTAL_REGISTERED = "POSTAL_REGISTERED", _("Registered postal mail")
    LRE = "LRE", _("Electronic registered letter")
    EMAIL = "EMAIL", _("Email")
    SMS = "SMS", _("SMS")
    RCS = "RCS", _("RCS (Rich SMS)")
    VOICE_CALL = "VOICE_CALL", _("Automated voice call")
    NOTIFICATION = "NOTIFICATION", _("In-app notification")
    PUSH_NOTIFICATION = "PUSH_NOTIFICATION", _("Mobile push notification")
    BRANDED = "BRANDED", _("App messaging")


class MissiveStatus(models.TextChoices):
    """Missive status."""

    DRAFT = "DRAFT", _("Draft")
    PENDING = "PENDING", _("Pending")
    PROCESSING = "PROCESSING", _("Processing")
    SENT = "SENT", _("Sent")
    DELIVERED = "DELIVERED", _("Delivered")
    READ = "READ", _("Read")
    FAILED = "FAILED", _("Failed")
    CANCELLED = "CANCELLED", _("Cancelled")


class MissivePriority(models.TextChoices):
    """Priority levels."""

    LOW = "LOW", _("Low")
    NORMAL = "NORMAL", _("Normal")
    HIGH = "HIGH", _("High")
    URGENT = "URGENT", _("Urgent")
