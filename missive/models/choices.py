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

    # Courrier
    POSTAL = "POSTAL", _("Courrier postal")
    LRE = "LRE", _("Lettre recommandée électronique")

    # Email
    EMAIL = "EMAIL", _("Email")

    # SMS et évolutions
    SMS = "SMS", _("SMS")
    RCS = "RCS", _("RCS (SMS enrichi)")

    # Vocal
    VOICE_CALL = "VOICE_CALL", _("Appel vocal automatisé")

    # Notifications
    NOTIFICATION = "NOTIFICATION", _("Notification in-app")
    PUSH_NOTIFICATION = "PUSH_NOTIFICATION", _("Notification push mobile")

    # Messageries d'applications (type générique ultra-simplifié)
    # Le nom du provider (self.name) détermine automatiquement quelle méthode appeler.
    # Supporte TOUTES les messageries : WhatsApp, Slack, Teams, Discord, Telegram, Signal, etc.
    # Exemple: un provider avec name="slack" appellera automatiquement send_slack()
    BRANDED = "BRANDED", _("Messagerie d'application")


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
