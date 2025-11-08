"""
Modèle Recipient pour gérer les destinataires.
"""

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from .choices import RecipientType


class Recipient(models.Model):
    """
    Modèle pour gérer les destinataires avec toutes leurs coordonnées.
    Peut être lié à un User ou à n'importe quel objet via GenericForeignKey.
    """

    # Lien optionnel avec un utilisateur Django
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recipient_profiles",
        verbose_name=_("Utilisateur"),
    )

    # Lien générique optionnel (Customer, Contact, etc.)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Type d'objet"),
    )
    object_id = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=_("ID de l'objet")
    )
    content_object = GenericForeignKey("content_type", "object_id")

    # Type de destinataire
    recipient_type = models.CharField(
        max_length=20,
        choices=RecipientType.choices,
        default=RecipientType.INDIVIDUAL,
        verbose_name=_("Type de destinataire"),
    )

    # Identité
    civility = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_("Civilité"),
        help_text=_("M., Mme, Dr, etc."),
    )
    first_name = models.CharField(max_length=100, blank=True, verbose_name=_("Prénom"))
    last_name = models.CharField(max_length=100, blank=True, verbose_name=_("Nom"))
    company_name = models.CharField(
        max_length=255, blank=True, verbose_name=_("Nom de l'entreprise")
    )

    # Coordonnées
    email = models.EmailField(blank=True, null=True, verbose_name=_("Email"))
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Téléphone"),
        help_text=_("Format international : +33600000000"),
    )
    mobile = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Mobile"),
        help_text=_("Format international"),
    )

    # Adresse postale complète
    address_line1 = models.CharField(
        max_length=255, blank=True, verbose_name=_("Adresse ligne 1")
    )
    address_line2 = models.CharField(
        max_length=255, blank=True, verbose_name=_("Adresse ligne 2")
    )
    address_line3 = models.CharField(
        max_length=255, blank=True, verbose_name=_("Adresse ligne 3")
    )
    postal_code = models.CharField(
        max_length=20, blank=True, verbose_name=_("Code postal")
    )
    city = models.CharField(max_length=100, blank=True, verbose_name=_("Ville"))
    state = models.CharField(max_length=100, blank=True, verbose_name=_("État/Région"))
    country = models.CharField(
        max_length=2, blank=True, default="FR", verbose_name=_("Pays (code ISO)")
    )

    # Métadonnées
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    is_active = models.BooleanField(default=True, verbose_name=_("Actif"))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Créé le"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Modifié le"))

    class Meta:
        verbose_name = _("Destinataire")
        verbose_name_plural = _("Destinataires")
        ordering = ["last_name", "first_name", "company_name"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["phone"]),
            models.Index(fields=["mobile"]),
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["last_name", "first_name"]),
            models.Index(fields=["company_name"]),
        ]

    def __str__(self):
        if self.company_name:
            return self.company_name
        elif self.first_name or self.last_name:
            parts = [self.civility, self.first_name, self.last_name]
            return " ".join(p for p in parts if p)
        elif self.email:
            return self.email
        elif self.phone or self.mobile:
            return self.phone or self.mobile
        return f"Recipient #{self.id}"

    @property
    def full_name(self):
        """Retourne le nom complet"""
        parts = [self.civility, self.first_name, self.last_name]
        return " ".join(p for p in parts if p).strip()

    @property
    def display_name(self):
        """Nom d'affichage"""
        if self.company_name:
            name = self.company_name
            if self.full_name:
                name += f" ({self.full_name})"
            return name
        return (
            self.full_name
            or self.email
            or self.phone
            or self.mobile
            or f"Recipient #{self.id}"
        )

    @property
    def postal_address(self):
        """Adresse postale formatée pour impression"""
        lines = []

        # Nom
        if self.company_name:
            lines.append(self.company_name)
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
