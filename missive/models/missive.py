"""
Modèle principal Missive pour l'envoi de missives multi-canaux.
"""

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from .choices import MissivePriority, MissiveStatus, MissiveType
from .recipient import Recipient


class Missive(models.Model):
    """
    Modèle principal pour gérer l'envoi de missives multi-canaux.
    Supporte : courrier postal, email, SMS, WhatsApp, notifications in-app.
    """

    # Identification
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_missives",
        verbose_name=_("Expéditeur"),
    )

    # Destinataire (nouveau modèle Recipient)
    recipient = models.ForeignKey(
        Recipient,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="missives",
        verbose_name=_("Destinataire"),
        help_text=_("Destinataire avec toutes ses coordonnées"),
    )

    # Compatibilité : lien direct avec User (optionnel si recipient est fourni)
    recipient_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="received_missives",
        verbose_name=_("Destinataire (utilisateur)"),
        help_text=_("Optionnel si 'recipient' est fourni"),
    )

    # Objet source (relation générique)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Type d'objet source"),
        help_text=_(
            "Type du modèle qui génère cette missive (Order, Participant, Invoice, etc.)"
        ),
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("ID de l'objet source"),
        help_text=_("ID de l'objet source"),
    )
    content_object = GenericForeignKey("content_type", "object_id")

    # Type et configuration
    missive_type = models.CharField(
        max_length=20, choices=MissiveType.choices, verbose_name=_("Type de missive")
    )
    priority = models.CharField(
        max_length=10,
        choices=MissivePriority.choices,
        default=MissivePriority.NORMAL,
        verbose_name=_("Priorité"),
    )

    # Contenu
    subject = models.CharField(
        max_length=255,
        verbose_name=_("Sujet"),
        help_text=_("Titre ou objet de la missive"),
    )
    body = models.TextField(
        verbose_name=_("Contenu HTML"),
        help_text=_("Corps du message (HTML pour emails, texte pour SMS/WhatsApp)"),
    )
    body_text = models.TextField(
        blank=True,
        verbose_name=_("Contenu texte brut"),
        help_text=_(
            "Version texte brut du message (fallback pour emails, obligatoire pour SMS)"
        ),
    )

    # Destinataire (selon le type)
    recipient_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name=_("Email destinataire"),
        help_text=_("Pour les emails"),
    )
    recipient_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Téléphone destinataire"),
        help_text=_("Pour SMS/WhatsApp (format international +33...)"),
    )
    recipient_address = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Adresse postale"),
        help_text=_("Pour le courrier postal"),
    )

    # Options spécifiques
    is_registered = models.BooleanField(
        default=False,
        verbose_name=_("Recommandé"),
        help_text=_("Email ou courrier recommandé avec accusé de réception"),
    )
    requires_signature = models.BooleanField(
        default=False,
        verbose_name=_("Signature requise"),
        help_text=_("Pour courrier recommandé avec signature"),
    )

    # Statut et tracking
    status = models.CharField(
        max_length=20,
        choices=MissiveStatus.choices,
        default=MissiveStatus.DRAFT,
        verbose_name=_("Statut"),
    )

    # Dates
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de modification")
    )
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date d'envoi programmée"),
        help_text=_("Laisser vide pour envoi immédiat"),
    )
    sent_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Date d'envoi")
    )
    delivered_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Date de réception")
    )
    read_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Date de lecture")
    )

    # Provider et tracking
    provider = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_("Provider"),
        help_text=_(
            "Provider à utiliser (sendgrid, twilio, laposte, etc.). Laissez vide pour utiliser la config par défaut."
        ),
    )
    external_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("ID externe"),
        help_text=_("ID de tracking du provider (LaPoste, SendGrid, etc.)"),
    )
    error_message = models.TextField(
        blank=True, null=True, verbose_name=_("Message d'erreur")
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Métadonnées"),
        help_text=_("Données additionnelles au format JSON"),
    )

    # Pièces jointes
    attachments_count = models.PositiveIntegerField(
        default=0, verbose_name=_("Nombre de pièces jointes")
    )

    # Coût et facturation
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Coût"),
        help_text=_("Coût d'envoi en euros"),
    )

    class Meta:
        verbose_name = _("Missive")
        verbose_name_plural = _("Missives")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["sender", "-created_at"]),
            models.Index(fields=["recipient_user", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["missive_type", "status"]),
            models.Index(fields=["external_id"]),
            models.Index(fields=["scheduled_at"]),
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        parts = [self.get_missive_type_display(), self.subject]
        if self.content_object:
            parts.append(f"→ {self.content_object}")
        parts.append(f"({self.get_status_display()})")
        return " - ".join(parts)

    @property
    def recipient_display(self):
        """Retourne l'identifiant du destinataire"""
        if self.recipient:
            return self.recipient.display_name
        elif self.recipient_user:
            return str(self.recipient_user)
        elif self.missive_type == MissiveType.EMAIL:
            return self.recipient_email or ""
        elif self.missive_type in [MissiveType.SMS, MissiveType.WHATSAPP]:
            return self.recipient_phone or ""
        elif self.missive_type == MissiveType.POSTAL:
            return (
                self.recipient_address.split("\n")[0] if self.recipient_address else ""
            )
        return _("Destinataire inconnu")

    def get_recipient_email(self):
        """Récupère l'email du destinataire (Recipient prioritaire)"""
        if self.recipient and self.recipient.email:
            return self.recipient.email
        elif self.recipient_email:
            return self.recipient_email
        elif self.recipient_user and hasattr(self.recipient_user, "email"):
            return self.recipient_user.email
        return None

    def get_recipient_phone(self):
        """Récupère le téléphone du destinataire (Recipient prioritaire)"""
        if self.recipient:
            return self.recipient.mobile or self.recipient.phone
        elif self.recipient_phone:
            return self.recipient_phone
        return None

    def get_recipient_address(self):
        """Récupère l'adresse postale du destinataire (Recipient prioritaire)"""
        if self.recipient and self.recipient.postal_address:
            return self.recipient.postal_address
        elif self.recipient_address:
            return self.recipient_address
        return None

    @property
    def is_sent(self):
        """Vérifie si la missive a été envoyée"""
        return self.status in [
            MissiveStatus.SENT,
            MissiveStatus.DELIVERED,
            MissiveStatus.READ,
        ]

    @property
    def is_delivered(self):
        """Vérifie si la missive a été délivrée"""
        return self.status in [MissiveStatus.DELIVERED, MissiveStatus.READ]

    def can_send(self):
        """Vérifie si la missive peut être envoyée"""
        return self.status in [MissiveStatus.DRAFT, MissiveStatus.PENDING]
