"""Modèle Missive principal pour l'envoi multi-canal."""

import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from djgeoaddress.fields import GeoaddressField

from djproviderkit import ProviderField

from .choices import AcknowledgementLevel, MissivePriority, MissiveStatus, MissiveType
from ..managers import MissiveManager

class Missive(models.Model):
    """Modèle de missive multi-canal (email, SMS, postal, WhatsApp, etc.)."""
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
        max_length=50,
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
    sender_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Sender Name"),
        help_text=_("Sender's full name or company name"),
    )
    sender_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name=_("Sender Email"),
        help_text=_("Sender's email address"),
    )
    sender_phone = PhoneNumberField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Sender Phone"),
        help_text=_("Sender's phone number"),
    )
    sender_address = GeoaddressField(
        blank=True,
        null=True,
        verbose_name=_("Sender Address"),
        help_text=_("Sender's address"),
    )

    recipient_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Recipient Name"),
        help_text=_("Recipient's full name or company name"),
    )
    recipient_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name=_("Recipient Email"),
        help_text=_("Recipient's email address"),
    )
    recipient_phone = PhoneNumberField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Recipient Phone"),
        help_text=_("Recipient's phone number"),
    )
    recipient_address = GeoaddressField(
        blank=True,
        null=True,
        verbose_name=_("Recipient Address"),
        help_text=_("Recipient's address"),
    )

    subject = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Subject"),
        help_text=_("Subject line (for email, SMS, etc.)"),
    )
    body = models.TextField(
        blank=True,
        verbose_name=_("Body"),
        help_text=_("Message body/content"),
    )
    body_text = models.TextField(
        blank=True,
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
        recipient = self.recipient_name or self.recipient_email or 'Unknown'
        return f"{self.missive_type} - {recipient} ({self.status})"

    def clean(self):
        super().clean()
        
        if self.pk:
            try:
                original = Missive.objects.get(pk=self.pk)
                has_events = self.to_missiveevent.exists()
                
                if has_events:
                    errors = {}
                    excluded_fields = {'id', 'created_at', 'updated_at'}
                    for field in self._meta.get_fields():
                        if field.is_relation and not field.one_to_one:
                            continue
                        field_name = field.name
                        if field_name in excluded_fields:
                            continue
                        if hasattr(self, field_name) and hasattr(original, field_name):
                            try:
                                current_value = getattr(self, field_name)
                                original_value = getattr(original, field_name)
                                if current_value != original_value:
                                    errors[field_name] = _('This field cannot be modified once events have been created.')
                            except (AttributeError, ValueError):
                                continue
                    
                    if errors:
                        raise ValidationError(errors)
            except Missive.DoesNotExist:
                pass
        
        if not self.sender_name:
            raise ValidationError({
                'sender_name': _('Sender name is required.'),
            })
        
        recipient_email = self.recipient_email
        recipient_phone = self.recipient_phone
        recipient_address = self.recipient_address
        
        has_recipient_address = (
            recipient_address is not None
            and isinstance(recipient_address, dict)
            and bool(recipient_address)
        )
        
        if not recipient_email and not recipient_phone and not has_recipient_address:
            raise ValidationError({
                'recipient_email': _('At least one recipient information (email, phone, or address) must be provided.'),
                'recipient_phone': _('At least one recipient information (email, phone, or address) must be provided.'),
                'recipient_address': _('At least one recipient information (email, phone, or address) must be provided.'),
            })
        
        self.clean_email()
        self.clean_address()
        self.clean_phone()

    def clean_email(self):
        recipient_email = self.recipient_email
        sender_email = self.sender_email
        
        if recipient_email and not sender_email:
            raise ValidationError({
                'sender_email': _('Sender email is required when recipient email is provided.'),
            })

    def clean_address(self):
        recipient_address = self.recipient_address
        sender_address = self.sender_address
        
        has_recipient_address = (
            recipient_address is not None
            and isinstance(recipient_address, dict)
            and bool(recipient_address)
        )
        
        if has_recipient_address:
            has_sender_address = (
                sender_address is not None
                and isinstance(sender_address, dict)
                and bool(sender_address)
            )
            if not has_sender_address:
                raise ValidationError({
                    'sender_address': _('Sender address is required when recipient address is provided.'),
                })

    def clean_phone(self):
        pass

    def get_target(self, prefix: str):
        fields = ["email", "phone", "address"]
        return next((getattr(self, f"{prefix}_{field}") for field in fields if getattr(self, f"{prefix}_{field}", None)), None)

    @property
    def sender(self):
        return self.get_target("sender")

    @property
    def recipient(self):
        return self.get_target("recipient")

    def get_serialized_data(self):
        """Serialize missive data to a dictionary for provider calls."""
        return {
            field.name: getattr(self, field.name) 
            for field in self._meta.get_fields() 
            if not field.is_relation and not field.many_to_many
            and not field.name.startswith("_")
        }


    def call_provider_service(self, service: str, status: str | None = None, **kwargs):
        """Call a provider service."""
        serialized = self.get_serialized_data()
        service_name = f"{service}_{self.missive_type}".lower()
        try:
            description = f"Service {service_name} called"
            response = self.provider._provider.call_service(service_name, **serialized)
        except Exception as e:
            status = MissiveStatus.FAILED
            description = str(e)
            response = {"error": str(e)}
        event = self.to_missiveevent.create(
            missive=self,
            event_type=service_name,
            status=status,
            trace=response,
            description=description,
        )
        if event.status:
            self.status = event.status
        return response

    def prepare_missive(self):
        """Prepare the missive for sending."""
        self.call_provider_service("prepare", status=MissiveStatus.PREPARE)

    def send_missive(self):
        """Send the missive."""
        response = self.call_provider_service("send", status=MissiveStatus.SENT)
        print("response", response)
        self.external_id = self.provider._provider.get_external_id_email(response)
        print("external_id", self.external_id)
        self.status = MissiveStatus.SENT if self.external_id else MissiveStatus.FAILED
        self.save()

    def cancel_missive(self):
        """Cancel the missive."""
        self.call_provider_service("cancel", status=MissiveStatus.CANCELLED)

    def status_missive(self):
        """Get the status of the missive."""
        self.call_provider_service("status")

    def billing_amount_missive(self):
        """Get the billing amount of the missive."""
        self.call_provider_service("billing_amount")

    def estimate_amount_missive(self):
        """Get the estimate amount of the missive."""
        self.call_provider_service("estimate_amount")

    def attachments_missive(self):
        """Get the attachments of the missive."""
        self.call_provider_service("attachments")

    def save(self, *args, **kwargs):
        """Save the missive, preventing any modification if events exist."""
        if self.pk:
            try:
                original = Missive.objects.get(pk=self.pk)
                has_events = self.to_missiveevent.exists()
                
                if has_events:
                    excluded_fields = {'status', 'external_id', 'id', 'created_at', 'updated_at'}
                    for field in self._meta.get_fields():
                        if field.is_relation and not field.one_to_one:
                            continue
                        field_name = field.name
                        if field_name in excluded_fields:
                            continue
                        if hasattr(original, field_name):
                            try:
                                setattr(self, field_name, getattr(original, field_name))
                            except (AttributeError, ValueError):
                                continue
            except Missive.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
