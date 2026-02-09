"""Missive model choices."""

from django.db import models
from django.utils.translation import gettext_lazy as _
from pymissive.config import MISSIVE_TYPES, MISSIVE_ACKNOWLEDGEMENT_LEVELS

class MissiveStatus(models.TextChoices):
    """Missive status."""

    DRAFT = "DRAFT", _("Draft")
    PREPARE = "PREPARE", _("Prepare")
    PENDING = "PENDING", _("Pending")
    PROCESSING = "PROCESSING", _("Processing")
    SENT = "SENT", _("Sent")
    DELIVERED = "DELIVERED", _("Delivered")
    READ = "READ", _("Read")
    FAILED = "FAILED", _("Failed")
    CANCELLED = "CANCELLED", _("Cancelled")


# Mapping des styles pour chaque statut
_MISSIVE_STATUS_STYLE_MAP = {
    "DRAFT": "secondary",
    "PREPARE": "info",
    "PENDING": "info",
    "PROCESSING": "info",
    "SENT": "success",
    "DELIVERED": "success",
    "READ": "success",
    "FAILED": "danger",
    "CANCELLED": "warning",
}


def get_status_style(status: str) -> str:
    """Retourne le style associé à un statut."""
    return _MISSIVE_STATUS_STYLE_MAP.get(status, "info")


class MissivePriority(models.TextChoices):
    """Priority levels."""

    LOW = "LOW", _("Low")
    NORMAL = "NORMAL", _("Normal")
    HIGH = "HIGH", _("High")
    URGENT = "URGENT", _("Urgent")


# Mapping des styles pour chaque priorité
_MISSIVE_PRIORITY_STYLE_MAP = {
    "LOW": "info",
    "NORMAL": "secondary",
    "HIGH": "warning",
    "URGENT": "danger",
}


def get_priority_style(priority: str) -> str:
    """Retourne le style associé à une priorité."""
    return _MISSIVE_PRIORITY_STYLE_MAP.get(priority, "info")


choices_missive_modes = {
    type_key.upper(): (type_key.upper(), _(type_description))
    for type_key, type_description in MISSIVE_TYPES.items()
}

MissiveType = models.TextChoices(
    "MissiveMode",
    choices_missive_modes
)

choices_acknowledgement_levels = {
    level["name"].upper(): (level["name"], _(level["display_name"]))
    for level in MISSIVE_ACKNOWLEDGEMENT_LEVELS
}

AcknowledgementLevel = models.TextChoices(
    "AcknowledgementLevel",
    choices_acknowledgement_levels
)
