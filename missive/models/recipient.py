"""
Modèle Recipient pour gérer les destinataires.
"""

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from .choices import RecipientType


class Recipient(models.Model):
    """
    Modèle pour gérer les destinataires avec toutes leurs coordonnées.
    Peut être lié à n'importe quel objet via GenericForeignKey (Customer, Contact, etc.).
    """

    # Lien générique optionnel (Customer, Contact, etc.)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Type d'objet"),
        help_text=_("Type d'objet lié (Customer, Contact, etc.)"),
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("ID de l'objet"),
        help_text=_("ID de l'objet lié"),
    )
    content_object = GenericForeignKey("content_type", "object_id")

    # Type de destinataire
    recipient_type = models.CharField(
        max_length=20,
        choices=RecipientType.choices,
        default=RecipientType.INDIVIDUAL,
        verbose_name=_("Type de destinataire"),
        help_text=_("Particulier, Entreprise ou Administration"),
    )

    # Identité
    civility = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_("Civilité"),
        help_text=_("M., Mme, Dr, etc."),
    )
    name = models.CharField(
        max_length=255,
        default="",
        verbose_name=_("Nom"),
        help_text=_(
            "Nom complet (personne) ou dénomination (entreprise/administration)"
        ),
    )

    # Coordonnées
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name=_("Email"),
        help_text=_("Adresse email du destinataire"),
    )
    mobile = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Téléphone mobile"),
        help_text=_(
            "Numéro de téléphone mobile au format international (ex: +33 6 12 34 56 78)"
        ),
    )

    # Adresse postale complète
    address_line1 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Adresse ligne 1"),
        help_text=_("Numéro et nom de rue"),
    )
    address_line2 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Adresse ligne 2"),
        help_text=_("Bâtiment, appartement, étage (optionnel)"),
    )
    address_line3 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Adresse ligne 3"),
        help_text=_("Complément d'adresse (optionnel)"),
    )
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Code postal"),
        help_text=_("Code postal"),
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Ville"),
        help_text=_("Ville"),
    )
    state = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("État/Région"),
        help_text=_("Région, département ou état"),
    )
    country = models.CharField(
        max_length=2,
        blank=True,
        default="FR",
        verbose_name=_("Pays (code ISO)"),
        help_text=_("Code pays ISO (FR, BE, CH, etc.)"),
    )

    # Métadonnées
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes"),
        help_text=_("Notes internes sur ce destinataire"),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Actif"),
        help_text=_("Désactiver pour masquer ce destinataire sans le supprimer"),
    )

    # Configuration expéditeur
    can_be_sender = models.BooleanField(
        default=False,
        verbose_name=_("Utilisable comme expéditeur"),
        help_text=_(
            "Cocher si ce destinataire peut être utilisé comme expéditeur de missives"
        ),
    )
    is_default_sender = models.BooleanField(
        default=False,
        verbose_name=_("Expéditeur par défaut"),
        help_text=_("Un seul expéditeur par défaut possible dans le système"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Créé le"),
        help_text=_("Date de création automatique"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Modifié le"),
        help_text=_("Date de dernière modification automatique"),
    )

    class Meta:
        verbose_name = _("Destinataire")
        verbose_name_plural = _("Destinataires")
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["email"]),
            models.Index(fields=["mobile"]),
            models.Index(fields=["content_type", "object_id"]),
        ]
        constraints = [
            # Un email ne peut être utilisé qu'une seule fois (si fourni)
            models.UniqueConstraint(
                fields=["email"],
                condition=models.Q(email__isnull=False) & ~models.Q(email=""),
                name="unique_email",
                violation_error_message=_("Un destinataire avec cet email existe déjà"),
            ),
            # Un mobile ne peut être utilisé qu'une seule fois (si fourni)
            models.UniqueConstraint(
                fields=["mobile"],
                condition=models.Q(mobile__isnull=False) & ~models.Q(mobile=""),
                name="unique_mobile",
                violation_error_message=_("Un destinataire avec ce mobile existe déjà"),
            ),
            # Une adresse postale complète ne peut être dupliquée
            models.UniqueConstraint(
                fields=["name", "address_line1", "postal_code", "city"],
                condition=models.Q(address_line1__isnull=False)
                & ~models.Q(address_line1=""),
                name="unique_postal_address",
                violation_error_message=_(
                    "Un destinataire avec cette adresse existe déjà"
                ),
            ),
        ]

    def __str__(self):
        """Représentation textuelle du destinataire avec contact principal"""
        name_part = self.full_name or f"Recipient #{self.id}"
        contact = self.primary_contact
        if contact:
            return f"{name_part} - {contact}"
        return name_part

    @property
    def full_name(self):
        """Retourne le nom complet avec civilité"""
        if self.civility and self.name:
            return f"{self.civility} {self.name}"
        return self.name or ""

    @property
    def display_name(self):
        """Nom d'affichage"""
        return self.full_name or self.email or self.mobile or f"Recipient #{self.id}"

    @property
    def postal_address(self):
        """Adresse postale formatée pour impression"""
        lines = []

        # Nom
        if self.full_name:
            lines.append(self.full_name)

        # Adresse
        if self.address_line1:
            lines.append(self.address_line1)
        if self.address_line2:
            lines.append(self.address_line2)
        if self.address_line3:
            lines.append(self.address_line3)

        # Ville
        city_line = []
        if self.postal_code:
            city_line.append(self.postal_code)
        if self.city:
            city_line.append(self.city)
        if city_line:
            lines.append(" ".join(city_line))

        # Région/Pays
        if self.state:
            lines.append(self.state)
        if self.country and self.country != "FR":
            lines.append(self.country)

        return "\n".join(lines)

    @property
    def primary_contact(self):
        """Retourne le contact principal : email, téléphone mobile ou adresse (1ère ligne)"""
        if self.email:
            return self.email
        elif self.mobile:
            return self.mobile
        elif self.address_line1:
            # Retourne l'adresse courte : ligne1, code postal ville
            parts = [self.address_line1]
            if self.postal_code and self.city:
                parts.append(f"{self.postal_code} {self.city}")
            elif self.city:
                parts.append(self.city)
            return ", ".join(parts)
        return None

    def save(self, *args, **kwargs):
        """
        Assure qu'un seul expéditeur par défaut existe.
        Si is_default_sender est True, tous les autres sont mis à False.
        """
        if self.is_default_sender:
            # Si on marque celui-ci comme expéditeur par défaut,
            # on retire le flag des autres
            Recipient.objects.filter(is_default_sender=True).exclude(pk=self.pk).update(
                is_default_sender=False
            )
            # Activer automatiquement can_be_sender si c'est l'expéditeur par défaut
            self.can_be_sender = True

        super().save(*args, **kwargs)
