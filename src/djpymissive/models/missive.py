"""Modèle Missive principal pour l'envoi multi-canal."""

import uuid

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from djgeoaddress.fields import GeoaddressField
from django.template import Context, Template
from djproviderkit import ProviderField
from django.utils.safestring import mark_safe
from django.urls import reverse

from .choices import (
    AcknowledgementLevel,
    MissiveSupport,
    MissiveEventType,
    MissivePriority,
    MissiveStatus,
    event_to_missive_status,
    MissiveType,
    get_missive_support_from_type,
    MissiveRecipientType,
    MissiveDocumentType,
)
from ..managers import MissiveManager

SEPARATOR = "\n--------------------------------\n"
ATTACHMENT_ICON = "&#128196;"
ATTACHMENT_STYLE = "text-decoration: none; font-size: 14px;"
ATTACHMENT_TPL_HTML = """<div>
    <a href='{url}' target='_blank' rel='noopener' style='{style}'>
        {icon}&nbsp;{name}
    </a>
</div>"""

PREVIEW_ICON = "&#127760;"
PREVIEW_STYLE = "text-decoration: none; font-size: 14px;"
PREVIEW_TPL_HTML = """<a href='{url}' target='_blank' rel='noopener' style='{style}'>
    {icon}&nbsp;{text}
</a>"""

class Missive(models.Model):
    """Modèle de missive multi-canal (email, SMS, postal, WhatsApp, etc.)."""

    campaign = models.ForeignKey(
        "djpymissive.MissiveCampaign",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="to_missive",
        verbose_name=_("Campaign"),
        help_text=_("Optional campaign this missive belongs to"),
    )
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )
    provider = ProviderField(
        package_name='pymissive',
        blank=True,
        verbose_name=_("Provider"),
        help_text=_("Provider used to send this missive"),
    )
    missive_support = models.CharField(
        max_length=50,
        choices=MissiveSupport.choices,
        verbose_name=_("Missive Support"),
        help_text=_("Support for the missive (email, SMS, postal, etc.)"),
        editable=False,
    )
    missive_type = models.CharField(
        max_length=50,
        choices=MissiveType.choices,
        verbose_name=_("Missive Type"),
        help_text=_("Type of missive (email, SMS, postal, etc.)"),
    )
    acknowledgement = models.CharField(
        max_length=50,
        choices=AcknowledgementLevel.choices,
        blank=True,
        null=True,
        verbose_name=_("Acknowledgement Level"),
        help_text=_("Desired acknowledgement level for delivery proof"),
    )
    status = models.CharField(
        max_length=20,
        choices=MissiveStatus.choices,
        default=MissiveStatus.DRAFT,
        verbose_name=_("Status"),
        help_text=_("Current status of the missive"),
    )
    priority = models.CharField(
        max_length=20,
        choices=MissivePriority.choices,
        default=MissivePriority.NORMAL,
        verbose_name=_("Priority"),
        help_text=_("Priority level"),
    )
    subject = models.CharField(
        max_length=500,
        verbose_name=_("Subject"),
        help_text=_("Subject line (for email, SMS, etc.)"),
    )
    body = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Body"),
        help_text=_("Message body/content"),
    )
    body_text = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Body Text"),
        help_text=_("Plain text version of the message"),
    )
    external_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        editable=False,
        verbose_name=_("External ID"),
        help_text=_("External identifier from the provider"),
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Metadata"),
        help_text=_("Additional metadata as JSON"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Sent At"),
        help_text=_("When the missive was sent"),
    )
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Delivered At"),
        help_text=_("When the missive was delivered"),
    )
    is_billed = models.BooleanField(
        default=False,
        verbose_name=_("Billed"),
        help_text=_("Indicates if the missive has been billed"),
    )
    billing_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Billing Amount"),
        help_text=_("Amount billed for the missive"),
    )
    estimate_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Estimate Amount"),
        help_text=_("Estimated amount for the missive"),
    )

    objects = MissiveManager()

    class Meta:
        verbose_name = _("Missive")
        verbose_name_plural = _("Missives")
        ordering = ["-created_at"]

    def __str__(self):
        recipient = self.first_recipient or 'Unknown'
        return f"{self.missive_type} - {recipient} ({self.status})"

    def save(self, *args, **kwargs):
        """Save the missive."""
        if self.can_be_modified:
            self.missive_support = get_missive_support_from_type(self.missive_type)
        super().save(*args, **kwargs)

    @property
    def can_be_modified(self):
        return not self.external_id

    @property
    def last_event_display(self):
        return dict(MissiveEventType.choices).get(self.last_event, self.last_event)

    def get_serialized_data(self):
        """Serialize missive data to a dictionary for provider calls."""
        from .recipient import MissiveRecipient
        missive_data = {
            field.name: getattr(self, field.name) 
            for field in self._meta.get_fields() 
            if not field.is_relation and not field.many_to_many
            and not field.name.startswith("_") and field.name not in ["body", "body_text"]
        }
        missive_data["body"] = self.body_compiled()
        missive_data["body_text"] = self.body_text_compiled()
        missive_data["recipients"] = [recipient.get_serialized_data() for recipient in self.recipients]
        if isinstance(self.sender, MissiveRecipient) and self.sender:
            missive_data["sender"] = self.sender.get_serialized_data()
        if isinstance(self.reply_to, MissiveRecipient) and self.reply_to:
            missive_data["reply_to"] = self.reply_to.get_serialized_data()
        if self.cc:
            missive_data["cc"] = [recipient.get_serialized_data() for recipient in self.cc]
        if self.bcc:
            missive_data["bcc"] = [recipient.get_serialized_data() for recipient in self.bcc]
        missive_data["attachments"] = self.get_serialized_attachments(linked=False)
        return missive_data

    def call_provider_service(self, service: str, status: str | None = None, **kwargs):
        """Call a provider service."""
        serialized = self.get_serialized_data()
        service_name = f"{service}_{self.missive_type}".lower()
        is_error = False
        try:
            description = f"Service {service_name} called"
            response = self.provider._provider.call_service(service_name, silent=False, **serialized)
        except Exception as e:
            raise e
            status = MissiveEventType.FAILED
            description = str(e)
            response = {"error": str(e)}
            is_error = True
        event = self.to_missiveevent.create(
            missive=self,
            event=status,
            trace=response,
            description=description,
            metadata={"service": service_name},
        )
        self.status = (
            MissiveStatus.ERROR if is_error else event_to_missive_status(event.event)
        )
        self.save(update_fields=["status"])
        return response

    #########################################################
    # Template rendering / Context
    #########################################################

    def missive_context(self):
        """Get the context of the missive."""
        return {
            "show_preview_browser": self.show_preview_browser,
            "show_preview_browser_text": self.show_preview_browser_text,
            "show_attahcments_linked": self.show_attachments_linked,
            "show_attachments_linked_text": self.show_attachments_linked_text,
        }

    @property
    def show_preview_browser(self):
        """Show the preview browser."""
        url = reverse("djpymissive:missive_preview", args=[self.pk])
        url = self.domain + url
        data = {
            "url": url,
            "icon": PREVIEW_ICON,
            "text": _('Preview in browser'),
            "style": PREVIEW_STYLE,
        }
        return mark_safe(PREVIEW_TPL_HTML.format(**data))

    @property
    def show_preview_browser_text(self):
        """Show the preview browser text."""
        url = reverse("djpymissive:missive_preview", args=[self.pk])
        url = self.domain + url
        return f"- {_('Preview in browser')}:{SEPARATOR}{url}\n"

    def body_compiled(self):
        """Compile the body of the missive."""
        context = self.missive_context()
        return Template(self.body).render(Context(context))

    def body_text_compiled(self):
        """Compile the body text of the missive."""
        context = self.missive_context()
        return Template(self.body_text).render(Context(context))

    #########################################################
    # Attachments
    #########################################################

    @property
    def domain(self):
        from django.conf import settings
        if settings.DEBUG:
            return "http://localhost:8000"
        return settings.DOMAIN 

    @property
    def show_attachments_linked(self):
        """Show the attachments linked."""
        html = "<div>"
        for attachment in self.get_serialized_attachments(linked=True):
            data = {
                "url": self.domain + attachment['url'],
                "icon": ATTACHMENT_ICON,
                "name": attachment['name'],
                "style": ATTACHMENT_STYLE,
            }
            html += ATTACHMENT_TPL_HTML.format(**data)
        html += "</div>"
        return mark_safe(html)

    @property
    def show_attachments_linked_text(self):
        """Show the attachments linked text."""
        qs = self.get_serialized_attachments(linked=True)
        if not qs:
            return ""
        title = _("Attachments:")
        text = f"{title}{SEPARATOR}"
        for attachment in qs:
            text += f"- {attachment['name']}\n{ self.domain }{attachment['url']}{SEPARATOR}"
        return text

    @property
    def attachments(self):
        return self.to_missivedocument.filter(
            models.Q(document_type=MissiveDocumentType.ATTACHMENT) |
            models.Q(document_type=MissiveDocumentType.VIRTUAL_ATTACHMENT),
        )

    @property
    def attachments_physical(self):
        return self.attachments.filter(linked=False)

    def get_serialized_attachments(self, linked=False):
        """Get the attachments of the missive."""
        qs = self.attachments.filter(linked=linked)
        return [attachment.get_serialized_document(linked) for attachment in qs]

    #########################################################
    # Services
    #########################################################

    def prepare_missive(self):
        """Prepare the missive for sending."""
        self.status = MissiveStatus.PROCESSING
        self.save()
        self.call_provider_service("prepare", status=MissiveEventType.PREPARE)

    def send_missive(self):
        """Send the missive."""
        self.status = MissiveStatus.PROCESSING
        self.save()
        response = self.call_provider_service("send", status=MissiveEventType.SENT)
        self.external_id = self.provider._provider.get_external_id_email(response)
        self.status = (
            MissiveStatus.SUCCESS if self.external_id else MissiveStatus.FAILED
        )
        self.save()

    def cancel_missive(self):
        """Cancel the missive."""
        self.call_provider_service("cancel", status=MissiveEventType.CANCELLED)

    def status_missive(self):
        """Get the status of the missive."""
        self.call_provider_service("status")

    #########################################################
    # Billing
    #########################################################

    def billing_amount_missive(self):
        """Get the billing amount of the missive."""
        self.call_provider_service("billing_amount")

    def estimate_amount_missive(self):
        """Get the estimate amount of the missive."""
        self.call_provider_service("estimate_amount")

    #########################################################
    # Recipients
    #########################################################

    @property
    def sender(self):
        try:
            return self.to_missiverecipient.get(recipient_type=MissiveRecipientType.SENDER)
        except ObjectDoesNotExist:
            return _("Unknown sender")

    @property
    def reply_to(self):
        try:
            return self.to_missiverecipient.get(recipient_type=MissiveRecipientType.REPLY_TO)
        except ObjectDoesNotExist:
            return _("Unknown reply to")

    @property
    def recipients(self):
        return self.to_missiverecipient.filter(recipient_type=MissiveRecipientType.RECIPIENT)

    @property
    def first_recipient(self):
        try:
            return self.recipients.first()
        except ObjectDoesNotExist:
            return _("Unknown recipient")

    @property
    def cc(self):
        return self.to_missiverecipient.filter(recipient_type=MissiveRecipientType.CC)

    @property
    def bcc(self):
        return self.to_missiverecipient.filter(recipient_type=MissiveRecipientType.BCC)

    #########################################################
    # Clean methods
    #########################################################

    def clean(self):
        """Clean the missive."""
        clean_by_support = f"clean_support_{self.missive_support}".lower()
        if hasattr(self, clean_by_support):
            getattr(self, clean_by_support)()

    def clean_support_email(self):
        """Clean the missive for email support."""
        if not self.body and not self.body_text:
            raise ValidationError(_("Body or body text is required"))

    def clean_support_phone(self):
        """Clean the missive for SMS support."""
        if not self.body_text:
            raise ValidationError(_("Body text is required"))

    def clean_support_postal(self):
        """Clean the missive for phone support."""
        if not self.body and len(self.to_missivedocument.all()) == 0:
            raise ValidationError(_("Body or attachments are required"))
