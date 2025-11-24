"""Main Missive model for multi-channel sending."""

from typing import Optional

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

try:
    from python_missive import format_phone_international
except ImportError:
    format_phone_international = None

from .choices import MissivePriority, MissiveStatus, MissiveType
from ..providers import normalize_provider_path


class Missive(models.Model):
    """Multi-channel missive model (email, SMS, postal, WhatsApp, etc.)."""

    # =============================================================================
    # Sender (Expéditeur) fields
    # =============================================================================
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
    sender_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Sender Phone"),
        help_text=_("Sender's phone number in international format (e.g., +33 6 12 34 56 78)"),
    )
    sender_address_line1 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Sender Address Line 1"),
        help_text=_("Street number and name"),
    )
    sender_address_line2 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Sender Address Line 2"),
        help_text=_("Building, apartment, floor (optional)"),
    )
    sender_address_line3 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Sender Address Line 3"),
        help_text=_("Additional address info (optional)"),
    )
    sender_postal_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Sender Postal Code"),
        help_text=_("Postal code"),
    )
    sender_city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Sender City"),
        help_text=_("City"),
    )
    sender_state = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Sender State/Region"),
        help_text=_("Region, department or state"),
    )
    sender_country = models.CharField(
        max_length=2,
        blank=True,
        default="FR",
        verbose_name=_("Sender Country (ISO code)"),
        help_text=_("ISO country code (FR, BE, CH, etc.)"),
    )

    # =============================================================================
    # Recipient (Destinataire) fields
    # =============================================================================
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
    recipient_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Recipient Phone"),
        help_text=_("Recipient's phone number in international format (e.g., +33 6 12 34 56 78)"),
    )
    recipient_address_line1 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Recipient Address Line 1"),
        help_text=_("Street number and name"),
    )
    recipient_address_line2 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Recipient Address Line 2"),
        help_text=_("Building, apartment, floor (optional)"),
    )
    recipient_address_line3 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Recipient Address Line 3"),
        help_text=_("Additional address info (optional)"),
    )
    recipient_postal_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Recipient Postal Code"),
        help_text=_("Postal code"),
    )
    recipient_city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Recipient City"),
        help_text=_("City"),
    )
    recipient_state = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Recipient State/Region"),
        help_text=_("Region, department or state"),
    )
    recipient_country = models.CharField(
        max_length=2,
        blank=True,
        default="FR",
        verbose_name=_("Recipient Country (ISO code)"),
        help_text=_("ISO country code (FR, BE, CH, etc.)"),
    )

    recipient_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="received_missives",
        verbose_name=_("Recipient (user)"),
        help_text=_("Optional: link to a user account"),
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Source Object Type"),
        help_text=_(
            "Type of model that generates this missive (Order, Participant, Invoice, etc.)"
        ),
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Source Object ID"),
        help_text=_("Source object ID"),
    )
    content_object = GenericForeignKey("content_type", "object_id")

    missive_type = models.CharField(
        max_length=20,
        choices=MissiveType.choices,
        verbose_name=_("Missive Type"),
        help_text=_("Email, SMS, WhatsApp, Postal Mail or Notification"),
    )
    priority = models.CharField(
        max_length=10,
        choices=MissivePriority.choices,
        default=MissivePriority.NORMAL,
        verbose_name=_("Priority"),
        help_text=_("Low, Normal, High or Urgent"),
    )

    subject = models.CharField(
        max_length=255,
        verbose_name=_("Subject"),
        help_text=_("Title or subject of the missive"),
    )
    body = models.TextField(
        verbose_name=_("HTML Content"),
        help_text=_("Message body (HTML for emails, text for SMS/WhatsApp)"),
    )
    body_text = models.TextField(
        blank=True,
        verbose_name=_("Plain Text Content"),
        help_text=_(
            "Plain text version of the message (fallback for emails, required for SMS)"
        ),
    )
    context = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Context Variables"),
        help_text=_(
            "JSON variables for template rendering (e.g., {'name': 'Smith', 'amount': 150})"
        ),
    )
    provider_options = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Provider Options"),
        help_text=_(
            "Provider-specific options (e.g., {'scheduled_time': 14, 'track_clicks': true, 'priority': 'high'})"
        ),
    )

    # Specific options
    is_registered = models.BooleanField(
        default=False,
        verbose_name=_("Registered"),
        help_text=_("Registered email or mail with acknowledgement of receipt"),
    )
    requires_signature = models.BooleanField(
        default=False,
        verbose_name=_("Signature Required"),
        help_text=_("For registered mail with signature"),
    )

    # Status and tracking
    status = models.CharField(
        max_length=20,
        choices=MissiveStatus.choices,
        default=MissiveStatus.DRAFT,
        verbose_name=_("Status"),
        help_text=_("Draft, Pending, Sent, Delivered, Read, Failed or Cancelled"),
    )

    # Dates
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Creation Date"),
        help_text=_("Automatic creation date of the missive"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Modification Date"),
        help_text=_("Automatic last modification date"),
    )
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Scheduled Send Date"),
        help_text=_("Leave blank for immediate sending"),
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Send Date"),
        help_text=_("Actual date and time the missive was sent"),
    )
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Delivery Date"),
        help_text=_("Date and time of confirmed receipt by recipient"),
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Read Date"),
        help_text=_("Date and time opened by recipient"),
    )

    # Tracking
    external_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("External Reference"),
        help_text=_("Provider tracking reference (LaPoste, SendGrid, etc.)"),
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Error Message"),
        help_text=_("Error message in case of sending failure"),
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Metadata"),
        help_text=_("Additional data in JSON format"),
    )

    # Attachments
    attachments_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Number of Attachments"),
        help_text=_("Total number of associated attachments"),
    )

    # Cost and billing
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Cost"),
        help_text=_("Sending cost in euros"),
    )

    class Meta:
        verbose_name = _("Missive")
        verbose_name_plural = _("Missives")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["sender_email", "-created_at"]),
            models.Index(fields=["recipient_email", "-created_at"]),
            models.Index(fields=["recipient_phone", "-created_at"]),
            models.Index(fields=["recipient_user", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["missive_type", "status"]),
            models.Index(fields=["external_id"]),
            models.Index(fields=["scheduled_at"]),
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        parts = [self.get_missive_type_display(), self.subject]
        if self.content_object:
            parts.append(f"→ {self.content_object}")
        parts.append(f"({self.get_status_display()})")
        return " - ".join(parts)

    def save(self, *args, **kwargs):
        """
        Save the missive.

        Automatically cleans phone numbers to international format.
        If MISSIVE_SANDBOX=True in settings, automatically forces
        sandbox=True in provider_options for ALL providers.
        """
        from django.conf import settings

        # Clean phone numbers to international format
        if format_phone_international:
            if self.recipient_phone:
                try:
                    # Use recipient country if available, otherwise default to FR
                    country_code = self.recipient_country or "FR"
                    self.recipient_phone = format_phone_international(
                        self.recipient_phone, country_code
                    )
                except Exception:
                    # If formatting fails, keep original phone
                    pass

            if self.sender_phone:
                try:
                    # Use sender country if available, otherwise default to FR
                    country_code = self.sender_country or "FR"
                    self.sender_phone = format_phone_international(
                        self.sender_phone, country_code
                    )
                except Exception:
                    # If formatting fails, keep original phone
                    pass

        # Force sandbox mode if enabled globally
        # B110: getattr on settings is safe, settings are controlled
        if getattr(settings, "MISSIVE_SANDBOX", False):  # nosec B110
            if not self.provider_options:
                self.provider_options = {}
            # Force sandbox=True (unless explicitly disabled)
            if "sandbox" not in self.provider_options:
                self.provider_options["sandbox"] = True

        super().save(*args, **kwargs)

    @property
    def recipient_display(self):
        """Returns the recipient identifier"""
        if self.recipient_name:
            return self.recipient_name
        elif self.recipient_email:
            return self.recipient_email
        elif self.recipient_phone:
            return self.recipient_phone
        elif self.recipient_user:
            return str(self.recipient_user)
        return _("Unknown recipient")

    def get_recipient_email(self):
        """Get the recipient's email"""
        if self.recipient_email:
            return self.recipient_email
        elif self.recipient_user and hasattr(self.recipient_user, "email"):
            return self.recipient_user.email
        return None

    def get_recipient_phone(self):
        """Get the recipient's phone number"""
        return self.recipient_phone

    def get_recipient_address(self):
        """Get the recipient's postal address"""
        lines = []
        if self.recipient_name:
            lines.append(self.recipient_name)
        if self.recipient_address_line1:
            lines.append(self.recipient_address_line1)
        if self.recipient_address_line2:
            lines.append(self.recipient_address_line2)
        if self.recipient_address_line3:
            lines.append(self.recipient_address_line3)
        city_line = []
        if self.recipient_postal_code:
            city_line.append(self.recipient_postal_code)
        if self.recipient_city:
            city_line.append(self.recipient_city)
        if city_line:
            lines.append(" ".join(city_line))
        if self.recipient_state:
            lines.append(self.recipient_state)
        if self.recipient_country and self.recipient_country != "FR":
            lines.append(self.recipient_country)
        return "\n".join(lines) if lines else None

    def get_sender_email(self):
        """Get the sender's email"""
        return self.sender_email

    def get_sender_phone(self):
        """Get the sender's phone number"""
        return self.sender_phone

    def get_sender_address(self):
        """Get the sender's postal address"""
        lines = []
        if self.sender_name:
            lines.append(self.sender_name)
        if self.sender_address_line1:
            lines.append(self.sender_address_line1)
        if self.sender_address_line2:
            lines.append(self.sender_address_line2)
        if self.sender_address_line3:
            lines.append(self.sender_address_line3)
        city_line = []
        if self.sender_postal_code:
            city_line.append(self.sender_postal_code)
        if self.sender_city:
            city_line.append(self.sender_city)
        if city_line:
            lines.append(" ".join(city_line))
        if self.sender_state:
            lines.append(self.sender_state)
        if self.sender_country and self.sender_country != "FR":
            lines.append(self.sender_country)
        return "\n".join(lines) if lines else None

    @property
    def is_sent(self):
        """Check if the missive has been sent"""
        return self.status in [
            MissiveStatus.SENT,
            MissiveStatus.DELIVERED,
            MissiveStatus.READ,
        ]

    @property
    def is_delivered(self):
        """Check if the missive has been delivered"""
        return self.status in [MissiveStatus.DELIVERED, MissiveStatus.READ]

    def can_send(self):
        """Check if the missive can be sent"""
        return self.status in [MissiveStatus.DRAFT, MissiveStatus.PENDING]

    @property
    def provider(self):
        """Get the provider from the first send event"""
        first_event = self.events.filter(event_type="sent").first()
        return first_event.provider if first_event else None

    def create_send_event(self, provider, status=None, description=""):
        """
        Create an initial send event for this missive.
        This method should be called when creating the missive.

        Args:
            provider: Provider name (sendgrid, twilio, laposte, etc.)
            status: Associated status (optional)
            description: Event description (optional)

        Returns:
            The created event
        """
        from .event import MissiveEvent

        return MissiveEvent.objects.create(
            missive=self,
            event_type="created",
            provider=provider or "django_email",
            status=status or self.status,
            description=description
            or f"Missive created with provider {provider or 'django_email'}",
        )

    def render_body(self):
        """
        Render the message body with context variables.

        Uses Django template engine to replace variables
        in the body with values from the context field.

        Example:
            body = "Hello {{ name }}, your order #{{ number }} is ready."
            context = {"name": "Jane", "number": "12345"}
            render_body() => "Hello Jane, your order #12345 is ready."

        Returns:
            The rendered body with context variables applied
        """
        from django.template import Context, Template

        if not self.context:
            return self.body

        try:
            template = Template(self.body)
            context = Context(self.context)
            return template.render(context)
        except Exception:
            # In case of template errors, return the original body
            return self.body

    def render_body_text(self):
        """
        Render the plain-text version of the body with context variables.
        """
        from django.template import Context, Template

        if not self.body_text:
            return ""

        if not self.context:
            return self.body_text

        try:
            template = Template(self.body_text)
            context = Context(self.context)
            return template.render(context)
        except Exception:
            # In case of template errors, return the original plain text
            return self.body_text

    def render_subject(self):
        """
        Render the subject with context variables.
        """
        from django.template import Context, Template

        if not self.context:
            return self.subject

        try:
            template = Template(self.subject)
            context = Context(self.context)
            return template.render(context)
        except Exception:
            # In case of template error, return the original subject
            return self.subject

    def get_proofs_of_delivery(self, service_type: Optional[str] = None):
        """
        Get all delivery/deposit proofs from the provider.

        This method instantiates the appropriate provider and retrieves all available proofs.

        Args:
            service_type: Service type (lre, postal_registered, email_ar, etc.)

        Returns:
            List of dict with information for each proof

        Example:
            missive = Missive.objects.get(id=123)
            proofs = missive.get_proofs_of_delivery()
            for proof in proofs:
                if proof['available']:
                    print(f"{proof['label']}: {proof['url']}")
        """
        from django.utils.module_loading import import_string

        # Get the provider from the first send event
        provider_name = self.provider
        if not provider_name:
            return []

        try:
            # Dynamically load the provider class
            from django.conf import settings

            providers_config = getattr(settings, "MISSIVE_PROVIDERS", {})

            # Search for the provider in config
            provider_path = None
            for missive_type, providers_list in providers_config.items():
                for prov in providers_list:
                    if provider_name.lower() in prov.lower():
                        provider_path = prov
                        break
                if provider_path:
                    break

            if provider_path:
                provider_path = normalize_provider_path(provider_path)
            else:
                # Fallback: try to construct the path (python-missive, except local django_email)
                if provider_name.lower() == "django_email":
                    provider_path = (
                        "python_missive.providers.django_email.DjangoEmailProvider"
                    )
                else:
                    provider_path = (
                        f"python_missive.providers.{provider_name.lower()}."
                        f"{provider_name.capitalize()}Provider"
                    )
                provider_path = normalize_provider_path(provider_path)

            # Import and instantiate the provider
            provider_class = import_string(provider_path)
            provider_instance = provider_class(missive=self)

            # Get all proofs
            return provider_instance.get_proofs_of_delivery(service_type)

        except Exception:
            return []

    def cancel(self) -> bool:
        """
        Cancel sending of this missive if it is pending or scheduled.

        This method:
        1. Checks that the missive is cancellable (status PENDING or SCHEDULED)
        2. If already sent to provider, attempts to cancel via its API
        3. Otherwise, simply changes status to CANCELLED

        Returns:
            True if cancellation succeeded, False otherwise

        Example:
            missive = Missive.objects.get(id=123)
            if missive.cancel():
                print("Missive cancelled successfully")
        """
        from django.conf import settings
        from django.utils.module_loading import import_string

        # Check that the missive is cancellable
        if self.status not in [MissiveStatus.PENDING, MissiveStatus.DRAFT]:
            return False

        # If already sent to a provider with external_id, attempt to cancel via API
        if self.provider and self.external_id:
            try:
                # Search for the provider in config
                providers_config = getattr(settings, "MISSIVE_PROVIDERS", {})
                provider_path = None

                for missive_type, providers_list in providers_config.items():
                    for prov in providers_list:
                        if self.provider.lower() in prov.lower():
                            provider_path = prov
                            break
                    if provider_path:
                        break

                if provider_path:
                    provider_path = normalize_provider_path(provider_path)
                else:
                    # Fallback: try to construct the path (python-missive, except local django_email)
                    if self.provider.lower() == "django_email":
                        provider_path = (
                            "python_missive.providers.django_email.DjangoEmailProvider"
                        )
                    else:
                        provider_path = (
                            f"python_missive.providers.{self.provider.lower()}."
                            f"{self.provider.capitalize()}Provider"
                        )
                    provider_path = normalize_provider_path(provider_path)

                # Import and instantiate the provider
                provider_class = import_string(provider_path)
                provider_instance = provider_class(missive=self)

                # Try to call the appropriate cancel method
                # Use provider's cancel() which automatically dispatches
                if provider_instance.cancel():
                    self.status = MissiveStatus.CANCELLED
                    self.save()
                    return True

            except Exception:
                # In case of error, continue to cancel locally
                pass

        # If not yet sent or provider cancellation failed, simple status change
        self.status = MissiveStatus.CANCELLED
        self.save()
        return True
