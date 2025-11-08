"""
Choix (enums) pour les modèles Django Missive.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class RecipientType(models.TextChoices):
    """Types de destinataires"""

    INDIVIDUAL = "INDIVIDUAL", _("Particulier")
    COMPANY = "COMPANY", _("Entreprise")
    ADMINISTRATION = "ADMINISTRATION", _("Administration")


class MissiveType(models.TextChoices):
    """Types de missives disponibles"""

    POSTAL = "POSTAL", _("Courrier postal")
    EMAIL = "EMAIL", _("Email")
    SMS = "SMS", _("SMS")
    WHATSAPP = "WHATSAPP", _("WhatsApp")
    NOTIFICATION = "NOTIFICATION", _("Notification in-app")


class MissiveStatus(models.TextChoices):
    """Statuts du cycle de vie d'une missive"""

    DRAFT = "DRAFT", _("Brouillon")
    PENDING = "PENDING", _("En attente")
    PROCESSING = "PROCESSING", _("En cours de traitement")
    SENT = "SENT", _("Envoyé")
    DELIVERED = "DELIVERED", _("Délivré")
    READ = "READ", _("Lu")
    FAILED = "FAILED", _("Échec")
    CANCELLED = "CANCELLED", _("Annulé")


class MissivePriority(models.TextChoices):
    """Niveaux de priorité"""

    LOW = "LOW", _("Basse")
    NORMAL = "NORMAL", _("Normale")
    HIGH = "HIGH", _("Haute")
    URGENT = "URGENT", _("Urgente")
