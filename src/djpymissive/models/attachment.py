"""MissiveAttachment model."""

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class MissiveAttachment(models.Model):
    """File attachment for missives or any other model."""

    missive = models.ForeignKey(
        "djpymissive.Missive",
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name=_("Missive"),
        null=True,
        blank=True,
        help_text=_("Missive to which this file is attached"),
    )

    file_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Object Type"),
        help_text=_("Type of model to which this file is attached"),
    )
    file_object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Object ID"),
        help_text=_("ID of the object to which this file is attached"),
    )
    file_method_access = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("File Method Access"),
        help_text=_("Method to access the file"),
    )
    file = models.FileField(
        upload_to="missive/attachments/%Y/%m/%d/",
        blank=True,
        null=True,
        verbose_name=_("Local File"),
        help_text=_("Leave blank if the file is hosted externally"),
    )
    file_metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("File Metadata"),
        help_text=_("Metadata of the file"),
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Order"),
        help_text=_("Display order"),
    )

    file_object = GenericForeignKey("file_content_type", "file_object_id")

    class Meta:
        verbose_name = _("Attachment")
        verbose_name_plural = _("Attachments")
        ordering = ["order",]


    def can_access_file(self):
        """Checks if the file can be accessed."""
        return all([self.file_content_type, self.file_object_id, self.file_method_access])

    def get_file_method(self):
        """Gets the file method."""
        if hasattr(self.file_object, self.file_method_access):
            method = getattr(self.file_object, self.file_method_access)
            if callable(method):
                return method
        return None

    def get_file(self):
        """Gets the file."""
        if self.file:
            return self.file
        return self.get_file_method()

    def clean(self):
        """Validates attachment."""
        if not self.file and not self.can_access_file():
            raise ValidationError(
                _("You must provide either a local file or a method to access the file.")
            )
