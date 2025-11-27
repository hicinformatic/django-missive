"""MissiveAttachment model."""

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class MissiveAttachment(models.Model):
    """File attachment for missives or any other model."""

    missive = models.ForeignKey(
        "missive.Missive",
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name=_("Missive"),
        null=True,
        blank=True,
        help_text=_("Missive to which this file is attached"),
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Object Type"),
        help_text=_(
            "Type of model to which this file is attached (Order, Invoice, etc.)"
        ),
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Object ID"),
        help_text=_("ID of the object to which this file is attached"),
    )
    content_object = GenericForeignKey("content_type", "object_id")

    file = models.FileField(
        upload_to="missive/attachments/%Y/%m/%d/",
        blank=True,
        null=True,
        verbose_name=_("Local File"),
        help_text=_("Leave blank if the file is hosted externally"),
    )

    external_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_("External URL"),
        help_text=_("URL of externally hosted file (S3, Google Drive, etc.)"),
    )

    filename = models.CharField(
        max_length=255,
        verbose_name=_("Filename"),
        help_text=_("Filename with extension"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Description or notes about this attachment"),
    )
    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Size (bytes)"),
        help_text=_("File size in bytes"),
    )
    mime_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("MIME Type"),
        help_text=_("MIME type of the file (application/pdf, image/png, etc.)"),
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Order"),
        help_text=_("Display order (automatic if not provided)"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date Added"),
        help_text=_("Automatic addition date of the attachment"),
    )

    class Meta:
        verbose_name = _("Attachment")
        verbose_name_plural = _("Attachments")
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
        """Returns file URL."""
        if self.file:
            return self.file.url
        elif self.external_url:
            return self.external_url
        return None

    @property
    def is_external(self):
        """Checks if file is external."""
        return bool(self.external_url and not self.file)

    @property
    def attached_to(self):
        """Returns attached object."""
        if self.missive:
            return self.missive
        elif self.content_object:
            return self.content_object
        return None

    def save(self, *args, **kwargs):
        """Auto-assigns order if not provided."""
        if not self.order and self.order != 0:
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
        """Validates attachment."""
        if not self.file and not self.external_url:
            raise ValidationError(
                _("You must provide either a local file or an external URL.")
            )

        if not self.missive and not self.content_type:
            raise ValidationError(
                _("You must attach this file to either a missive or another object.")
            )
