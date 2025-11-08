"""
Modèle MissiveAttachment pour gérer les pièces jointes.
"""

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class MissiveAttachment(models.Model):
    """
    Pièces jointes pouvant être attachées :
    - À une missive (via missive)
    - À n'importe quel autre modèle (via content_object)
    """

    # Import tardif pour éviter les imports circulaires
    # La relation sera résolue au runtime par Django
    # Relation avec une missive (optionnel si content_object est fourni)
    missive = models.ForeignKey(
        "missive.Missive",
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name=_("Missive"),
        null=True,
        blank=True,
        help_text=_("Missive à laquelle ce fichier est attaché"),
    )

    # Relation générique (optionnel si missive est fourni)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Type d'objet"),
        help_text=_(
            "Type du modèle auquel ce fichier est attaché (Order, Invoice, etc.)"
        ),
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("ID de l'objet"),
        help_text=_("ID de l'objet auquel ce fichier est attaché"),
    )
    content_object = GenericForeignKey("content_type", "object_id")

    # Fichier local (optionnel si external_url est fourni)
    file = models.FileField(
        upload_to="missive/attachments/%Y/%m/%d/",
        blank=True,
        null=True,
        verbose_name=_("Fichier local"),
        help_text=_("Laisser vide si le fichier est hébergé en externe"),
    )

    # Fichier externe (optionnel si file est fourni)
    external_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_("URL externe"),
        help_text=_("URL du fichier hébergé en externe (S3, Google Drive, etc.)"),
    )

    # Métadonnées
    filename = models.CharField(max_length=255, verbose_name=_("Nom du fichier"))
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Description ou notes sur cette pièce jointe"),
    )
    file_size = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=_("Taille (bytes)")
    )
    mime_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Type MIME"),
        help_text=_("Type MIME du fichier (application/pdf, image/png, etc.)"),
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Ordre"),
        help_text=_("Ordre d'affichage (automatique si non fourni)"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date d'ajout"))

    class Meta:
        verbose_name = _("Pièce jointe")
        verbose_name_plural = _("Pièces jointes")
        ordering = ["order", "created_at"]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["missive", "order"]),
            models.Index(fields=["missive", "created_at"]),
        ]

    def __str__(self):
        parts = [self.filename]
        if self.missive:
            parts.append(f"(Missive #{self.missive.id})")
        elif self.content_object:
            parts.append(f"({self.content_object})")
        return " ".join(parts)

    @property
    def file_url(self):
        """Retourne l'URL du fichier (local ou externe)"""
        if self.file:
            return self.file.url
        elif self.external_url:
            return self.external_url
        return None

    @property
    def is_external(self):
        """Vérifie si le fichier est externe"""
        return bool(self.external_url and not self.file)

    @property
    def attached_to(self):
        """Retourne l'objet auquel le fichier est attaché"""
        if self.missive:
            return self.missive
        elif self.content_object:
            return self.content_object
        return None

    def save(self, *args, **kwargs):
        """Attribue automatiquement un ordre si non fourni"""
        if not self.order and self.order != 0:
            # Récupère le dernier ordre pour cet objet
            if self.missive:
                last_attachment = (
                    MissiveAttachment.objects.filter(missive=self.missive)
                    .order_by("-order")
                    .first()
                )
            elif self.content_type and self.object_id:
                last_attachment = (
                    MissiveAttachment.objects.filter(
                        content_type=self.content_type, object_id=self.object_id
                    )
                    .order_by("-order")
                    .first()
                )
            else:
                last_attachment = None

            if last_attachment:
                self.order = last_attachment.order + 1
            else:
                self.order = 0

        super().save(*args, **kwargs)

    def clean(self):
        """Validation"""
        # Au moins file ou external_url doit être fourni
        if not self.file and not self.external_url:
            raise ValidationError(
                _("Vous devez fournir soit un fichier local, soit une URL externe.")
            )

        # Au moins missive ou content_object doit être fourni
        if not self.missive and not self.content_type:
            raise ValidationError(
                _(
                    "Vous devez attacher ce fichier soit à une missive, soit à un autre objet."
                )
            )
