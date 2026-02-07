"""Admin for Missive model."""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_boosted import AdminBoostModel

from phonenumber_field.modelfields import PhoneNumberField
from phonenumber_field.formfields import SplitPhoneNumberField

from ..models.missive import Missive
from ..models.choices import get_priority_style, get_status_style
from .attachment import MissiveAttachmentInline
from .event import MissiveEventInline
from .related_object import MissiveRelatedObjectInline


@admin.register(Missive)
class MissiveAdmin(AdminBoostModel):
    """Admin for missive model."""

    list_display = [
        "recipient_display",
        "sender_display",
        "subject",
        "status_display",
        "event_display",
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
        "recipient_address",
        "sender_name",
        "sender_email",
        "sender_phone",
        "sender_address",
        "external_id",
    ]
    readonly_fields = [
        "created_at",
        "updated_at",
        "sent_at",
        "delivered_at",
        "external_id",
    ]
    inlines = [
        MissiveAttachmentInline,
        MissiveEventInline,
        MissiveRelatedObjectInline,
    ]

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if isinstance(db_field, PhoneNumberField):
            kwargs.setdefault('required', False)
            return SplitPhoneNumberField(**kwargs)
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def recipient_display(self, obj):
        return self.format_with_help_text(obj.recipient_name, obj.recipient)
    recipient_display.short_description = _("Recipient")

    def sender_display(self, obj):
        return self.format_with_help_text(obj.sender_name, obj.sender)
    sender_display.short_description = _("Sender")
    
    def status_display(self, obj):
        priority_style = get_priority_style(obj.priority)
        status_style = get_status_style(obj.status)
        status_html = format_html(
            '{} {}',
            self.format_label(obj.get_priority_display(), size="small", label_type=priority_style),
            self.format_label(obj.get_status_display(), size="small", label_type=status_style)
        )
        return self.format_with_help_text(status_html, obj.get_missive_type_display())
    status_display.short_description = _("Status")

    def event_display(self, obj):
        event_related_html = format_html(
            '{} {}',
            self.format_label(f"{obj.count_event} event(s)", size="small"),
            self.format_label(f"{obj.count_related_object} related(s)", size="small", label_type="secondary")
        )
        return self.format_with_help_text(event_related_html, obj.last_event_date)
    event_display.short_description = _("Event(s)/Related(s)")

    def change_fieldsets(self):
        """Configure fieldsets for change view."""
        self.add_to_fieldset(
            None,
            ["provider", "missive_type", "acknowledgement", "status", "priority"],
        )
        self.add_to_fieldset(
            _("Sender"),
            ["sender_name", "sender_email", "sender_phone", "sender_address"],
        )
        self.add_to_fieldset(
            _("Recipient"),
            ["recipient_name", "recipient_email", "recipient_phone", "recipient_address"],
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
