"""
Modèle principal Missive pour l'envoi de missives multi-canaux.
"""

from typing import Optional

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
        Recipient,
        on_delete=models.PROTECT,
        related_name="sent_missives",
        verbose_name=_("Expéditeur"),
        help_text=_("Expéditeur de cette missive (utilise le modèle Recipient)"),
    )

    # Destinataire
    recipient = models.ForeignKey(
        Recipient,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="received_missives",
        verbose_name=_("Destinataire"),
        help_text=_("Destinataire de cette missive (utilise le modèle Recipient)"),
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
        max_length=20,
        choices=MissiveType.choices,
        verbose_name=_("Type de missive"),
        help_text=_("Email, SMS, WhatsApp, Courrier postal ou Notification"),
    )
    priority = models.CharField(
        max_length=10,
        choices=MissivePriority.choices,
        default=MissivePriority.NORMAL,
        verbose_name=_("Priorité"),
        help_text=_("Basse, Normale, Haute ou Urgente"),
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
    context = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Variables de contexte"),
        help_text=_(
            "Variables JSON pour le rendu du template (ex: {'nom': 'Dupont', 'montant': 150})"
        ),
    )
    provider_options = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Options du provider"),
        help_text=_(
            "Options spécifiques au provider (ex: {'scheduled_time': 14, 'track_clicks': true, 'priority': 'high'})"
        ),
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
        help_text=_("Brouillon, En attente, Envoyé, Délivré, Lu, Échec ou Annulé"),
    )

    # Dates
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création"),
        help_text=_("Date de création automatique de la missive"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de modification"),
        help_text=_("Date de dernière modification automatique"),
    )
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date d'envoi programmée"),
        help_text=_("Laisser vide pour envoi immédiat"),
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date d'envoi"),
        help_text=_("Date et heure d'envoi effective de la missive"),
    )
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de réception"),
        help_text=_("Date et heure de réception confirmée par le destinataire"),
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de lecture"),
        help_text=_("Date et heure d'ouverture par le destinataire"),
    )

    # Tracking
    external_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Référence externe"),
        help_text=_("Référence de tracking du provider (LaPoste, SendGrid, etc.)"),
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Message d'erreur"),
        help_text=_("Message d'erreur en cas d'échec d'envoi"),
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Métadonnées"),
        help_text=_("Données additionnelles au format JSON"),
    )

    # Pièces jointes
    attachments_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Nombre de pièces jointes"),
        help_text=_("Nombre total de pièces jointes associées"),
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
        return _("Destinataire inconnu")

    def get_recipient_email(self):
        """Récupère l'email du destinataire"""
        if self.recipient and self.recipient.email:
            return self.recipient.email
        elif self.recipient_user and hasattr(self.recipient_user, "email"):
            return self.recipient_user.email
        return None

    def get_recipient_phone(self):
        """Récupère le téléphone du destinataire"""
        if self.recipient:
            return self.recipient.mobile or self.recipient.phone
        return None

    def get_recipient_address(self):
        """Récupère l'adresse postale du destinataire"""
        if self.recipient and self.recipient.postal_address:
            return self.recipient.postal_address
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

    @property
    def provider(self):
        """Récupère le provider depuis le premier événement d'envoi"""
        first_event = self.events.filter(event_type="sent").first()
        return first_event.provider if first_event else None

    def create_send_event(self, provider, status=None, description=""):
        """
        Crée un événement d'envoi initial pour cette missive.
        Cette méthode doit être appelée lors de la création de la missive.

        Args:
            provider: Nom du provider (sendgrid, twilio, laposte, etc.)
            status: Statut associé (optionnel)
            description: Description de l'événement (optionnel)

        Returns:
            L'événement créé
        """
        from .event import MissiveEvent

        return MissiveEvent.objects.create(
            missive=self,
            event_type="created",
            provider=provider or "django_email",
            status=status or self.status,
            description=description
            or f"Missive créée avec le provider {provider or 'django_email'}",
        )

    def render_body(self):
        """
        Rend le corps du message avec les variables de contexte.

        Utilise le moteur de template Django pour remplacer les variables
        dans le body avec les valeurs du champ context.

        Example:
            body = "Bonjour {{ nom }}, votre commande #{{ numero }} est prête."
            context = {"nom": "Jean", "numero": "12345"}
            render_body() => "Bonjour Jean, votre commande #12345 est prête."

        Returns:
            Le corps rendu avec les variables remplacées
        """
        from django.template import Context, Template

        if not self.context:
            return self.body

        try:
            template = Template(self.body)
            context = Context(self.context)
            return template.render(context)
        except Exception:
            # En cas d'erreur de template, retourner le body original
            return self.body

    def render_body_text(self):
        """
        Rend la version texte du corps avec les variables de contexte.

        Returns:
            Le corps texte rendu avec les variables remplacées
        """
        from django.template import Context, Template

        if not self.body_text:
            return ""

        if not self.context:
            return self.body_text

        try:
            template = Template(self.body_text)
            context = Context(self.context)
            return template.render(context)
        except Exception:
            # En cas d'erreur de template, retourner le body_text original
            return self.body_text

    def render_subject(self):
        """
        Rend le sujet avec les variables de contexte.

        Returns:
            Le sujet rendu avec les variables remplacées
        """
        from django.template import Context, Template

        if not self.context:
            return self.subject

        try:
            template = Template(self.subject)
            context = Context(self.context)
            return template.render(context)
        except Exception:
            # En cas d'erreur de template, retourner le sujet original
            return self.subject

    def get_proofs_of_delivery(self, service_type: Optional[str] = None):
        """
        Récupère toutes les preuves de dépôt/livraison depuis le provider.

        Cette méthode instancie le provider approprié et récupère toutes les preuves disponibles.

        Args:
            service_type: Type de service (lre, postal_registered, email_ar, etc.)

        Returns:
            Liste de dict avec les informations de chaque preuve

        Example:
            missive = Missive.objects.get(id=123)
            proofs = missive.get_proofs_of_delivery()
            for proof in proofs:
                if proof['available']:
                    print(f"{proof['label']}: {proof['url']}")
        """
        from django.utils.module_loading import import_string

        # Récupérer le provider depuis le premier événement d'envoi
        provider_name = self.provider
        if not provider_name:
            return []

        try:
            # Charger dynamiquement la classe du provider
            from django.conf import settings

            providers_config = getattr(settings, "MISSIVE_PROVIDERS", {})

            # Chercher le provider dans la config
            provider_path = None
            for missive_type, providers_list in providers_config.items():
                for prov in providers_list:
                    if provider_name.lower() in prov.lower():
                        provider_path = prov
                        break
                if provider_path:
                    break

            if not provider_path:
                # Fallback : essayer de construire le chemin
                provider_path = f"missive.providers.{provider_name.lower()}.{provider_name.capitalize()}Provider"

            # Importer et instancier le provider
            provider_class = import_string(provider_path)
            provider_instance = provider_class(missive=self)

            # Récupérer toutes les preuves
            return provider_instance.get_proofs_of_delivery(service_type)

        except Exception:
            return []

    def cancel(self) -> bool:
        """
        Annule l'envoi de cette missive si elle est en attente ou programmée.

        Cette méthode :
        1. Vérifie que la missive est annulable (status PENDING ou SCHEDULED)
        2. Si déjà envoyée au provider, tente d'annuler via son API
        3. Sinon, change simplement le status à CANCELLED

        Returns:
            True si l'annulation a réussi, False sinon

        Example:
            missive = Missive.objects.get(id=123)
            if missive.cancel():
                print("Missive annulée avec succès")
        """
        from django.conf import settings
        from django.utils.module_loading import import_string

        # Vérifier que la missive est annulable
        if self.status not in [MissiveStatus.PENDING, MissiveStatus.DRAFT]:
            return False

        # Si déjà envoyée à un provider avec external_id, tenter d'annuler via API
        if self.provider and self.external_id:
            try:
                # Chercher le provider dans la config
                providers_config = getattr(settings, "MISSIVE_PROVIDERS", {})
                provider_path = None

                for missive_type, providers_list in providers_config.items():
                    for prov in providers_list:
                        if self.provider.lower() in prov.lower():
                            provider_path = prov
                            break
                    if provider_path:
                        break

                if not provider_path:
                    # Fallback : essayer de construire le chemin
                    provider_path = f"missive.providers.{self.provider.lower()}.{self.provider.capitalize()}Provider"

                # Importer et instancier le provider
                provider_class = import_string(provider_path)
                provider_instance = provider_class(missive=self)

                # Essayer d'appeler la méthode cancel appropriée
                # Utiliser cancel() du provider qui dispatche automatiquement
                if provider_instance.cancel():
                    self.status = MissiveStatus.CANCELLED
                    self.save()
                    return True

            except Exception:
                # En cas d'erreur, on continue pour annuler localement
                pass

        # Si pas encore envoyé ou annulation provider échouée, simple changement de statut
        self.status = MissiveStatus.CANCELLED
        self.save()
        return True
