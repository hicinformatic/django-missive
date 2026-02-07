"""Admin for Missive model."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django_boosted import AdminBoostModel

from phonenumber_field.modelfields import PhoneNumberField
from phonenumber_field.formfields import SplitPhoneNumberField

from ..models.missive import Missive
from .attachment import MissiveAttachmentInline
from .event import MissiveEventInline
from .related_object import MissiveRelatedObjectInline


@admin.register(Missive)
class MissiveAdmin(AdminBoostModel):
    """Admin for missive model."""

    list_display = [
        "id",
        "missive_type",
        "recipient_name",
        "recipient_email",
        "status",
        "priority",
        "provider",
        "created_at",
    ]
    list_filter = [
        "missive_type",
        "status",
        "priority",
        "provider",
        "created_at",
    ]
    search_fields = [
        "subject",
        "recipient_name",
        "recipient_email",
        "recipient_phone",
        "sender_name",
        "sender_email",
        "external_id",
    ]
    readonly_fields = [
        "created_at",
        "updated_at",
        "sent_at",
        "delivered_at",
    ]
    inlines = [
        MissiveAttachmentInline,
        MissiveEventInline,
        MissiveRelatedObjectInline,
    ]

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if isinstance(db_field, PhoneNumberField):
            return SplitPhoneNumberField()
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def change_fieldsets(self):
        """Configure fieldsets for change view."""
        self.add_to_fieldset(
            None,
            ["provider", "missive_type", "acknowledgement", "status", "priority"],
        )
        self.add_to_fieldset(
            _("Sender"),
            ["sender_name", "sender_email", "sender_phone"],
        )
        self.add_to_fieldset(
            _("Recipient"),
            ["recipient_name", "recipient_email", "recipient_phone"],
        )
        self.add_to_fieldset(
            _("Content"),
            ["subject", "body"],
        )
        self.add_to_fieldset(
            _("Tracking"),
            ["external_id", "metadata"],
        )
        self.add_to_fieldset(
            _("Timestamps"),
            ["created_at", "updated_at", "sent_at", "delivered_at"],
        )
