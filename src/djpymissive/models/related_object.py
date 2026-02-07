"""MissiveRelatedObject model for linking missives to other models."""

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _


class MissiveRelatedObject(models.Model):
    """Model to link a missive to any other Django model."""

    missive = models.ForeignKey(
        "djpymissive.Missive",
        on_delete=models.CASCADE,
        related_name="to_missiverelatedobject",
        verbose_name=_("Missive"),
        help_text=_("Missive to which this object is related"),
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_("Content Type"),
        help_text=_("Type of the related object"),
    )
    object_id = models.PositiveIntegerField(
        verbose_name=_("Object ID"),
        help_text=_("ID of the related object"),
    )
    content_object = GenericForeignKey("content_type", "object_id")

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
    )

    class Meta:
        verbose_name = _("Missive Related Object")
        verbose_name_plural = _("Missive Related Objects")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["missive", "-created_at"]),
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        return f"{self.missive} -> {self.content_object}"
