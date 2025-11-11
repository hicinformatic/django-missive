"""
Shortcut functions to send missives quickly.

Usage:
    from missive.shortcuts import send_missive

    send_missive('sms', phone='+33612345678', content='Test SMS')
    send_missive('email', email='user@example.com', subject='Test', content='Hello!')
    send_missive('branded', phone='+33612345678', content='Hello WhatsApp')
"""

import re
import uuid
from typing import Dict, Optional

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .exceptions import MissiveValidationError
from .models import Missive, MissiveType, Recipient
from .sender import MissiveSender

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================


def _validate_email(email: str) -> None:
    """Validate email format (RFC 5321 compliant)."""
    if not email:
        raise MissiveValidationError(_("Email address cannot be empty"))

    max_email_length = getattr(settings, "MISSIVE_MAX_EMAIL_LENGTH", 254)  # RFC 5321
    if len(email) > max_email_length:
        raise MissiveValidationError(_("Email address is too long"))

    # ReDoS-safe regex
    email_pattern = r"^[a-zA-Z0-9._%+-]{1,64}@[a-zA-Z0-9.-]{1,253}\.[a-zA-Z]{2,63}$"
    if not re.match(email_pattern, email):
        raise MissiveValidationError(_("Invalid email format"))


def _validate_phone(phone: str) -> None:
    """Validate phone number format (E.164 standard)."""
    if not phone:
        raise MissiveValidationError(_("Phone number cannot be empty"))

    max_phone_length = getattr(settings, "MISSIVE_MAX_PHONE_LENGTH", 16)
    if len(phone) > max_phone_length:
        raise MissiveValidationError(_("Phone number is too long"))

    # E.164 format, ReDoS-safe
    phone_pattern = r"^\+[1-9]\d{1,14}$"
    if not re.match(phone_pattern, phone):
        raise MissiveValidationError(
            _("Invalid phone format. Expected E.164 (e.g. +33612345678)")
        )


def _validate_content(content: str, missive_type: str = "") -> None:
    """Validate missive content."""
    if not content or not content.strip():
        msg = _("Content cannot be empty")
        if missive_type:
            msg = _("%(type)s content cannot be empty") % {"type": missive_type}
        raise MissiveValidationError(msg)

    max_length = getattr(settings, "MISSIVE_MAX_CONTENT_LENGTH", 1_000_000)
    if len(content) > max_length:
        raise MissiveValidationError(
            _("Content too long (max: %(max)s chars)") % {"max": max_length}
        )


def send_missive(
    missive_type: str,
    content: str,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    address: Optional[Dict] = None,
    sender_email: Optional[str] = None,
    sender_phone: Optional[str] = None,
    sender_name: Optional[str] = None,
    subject: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    denomination: Optional[str] = None,
    provider: Optional[str] = None,
    **kwargs,
) -> Missive:
    """
    Send a missive with minimal information. Auto-generates missing fields.

    Args:
        missive_type: Type ('sms', 'email', 'branded', 'postal', etc.)
        content: Message content
        phone: Recipient phone (for SMS/WhatsApp/Voice)
        email: Recipient email (for Email)
        address: Postal address (dict: street, city, postal_code, country)
        sender_email: Sender email (default: settings.DEFAULT_FROM_EMAIL)
        sender_phone: Sender phone
        sender_name: Sender name
        subject: Subject (auto-generated for emails)
        first_name: Recipient first name
        last_name: Recipient last name
        denomination: Organization name
        provider: Specific provider (else auto-selected)
        **kwargs: Additional options

    Returns:
        Created and sent Missive

    Example:
        >>> send_missive('sms', phone='+33612345678', content='Test')
        <Missive: SMS to +33612345678>
    """
    # Normalize type
    missive_type = missive_type.upper()
    if not hasattr(MissiveType, missive_type):
        type_mapping = {
            "SMS": "SMS",
            "EMAIL": "EMAIL",
            "MAIL": "EMAIL",
            "POSTAL": "POSTAL",
            "LETTER": "POSTAL",
            "COURRIER": "POSTAL",
            "LRE": "LRE",
            "NOTIFICATION": "NOTIFICATION",
            "NOTIF": "NOTIFICATION",
            "PUSH": "PUSH_NOTIFICATION",
            "PUSH_NOTIFICATION": "PUSH_NOTIFICATION",
            "VOICE": "VOICE_CALL",
            "VOICE_CALL": "VOICE_CALL",
            "CALL": "VOICE_CALL",
            "VOCAL": "VOICE_CALL",
            "BRANDED": "BRANDED",
            "WHATSAPP": "BRANDED",
            "SLACK": "BRANDED",
            "TEAMS": "BRANDED",
            "TELEGRAM": "BRANDED",
            "MESSENGER": "BRANDED",
            "SIGNAL": "BRANDED",
            "DISCORD": "BRANDED",
        }
        missive_type = type_mapping.get(missive_type, "EMAIL")

    # Validate content
    _validate_content(content, missive_type)

    # Validate required fields by type
    if missive_type in ("SMS", "VOICE_CALL"):
        if not phone:
            raise MissiveValidationError(
                _("'phone' field required for %(type)s") % {"type": missive_type}
            )
        _validate_phone(phone)

    elif missive_type == "EMAIL":
        if not email:
            raise MissiveValidationError(_("'email' field required for EMAIL"))
        _validate_email(email)

        if subject is not None and not subject.strip():
            raise MissiveValidationError(_("Email subject cannot be empty"))

    elif missive_type == "BRANDED":
        # For branded (WhatsApp, Slack, etc.), phone/email optional
        if phone:
            _validate_phone(phone)
        if email:
            _validate_email(email)

    elif missive_type == "POSTAL":
        if not address or not isinstance(address, dict):
            raise MissiveValidationError(
                _("'address' dict required for POSTAL missives")
            )
        required_fields = ["street", "city", "postal_code", "country"]
        missing = [f for f in required_fields if not address.get(f)]
        if missing:
            raise MissiveValidationError(
                _("Missing address fields: %(fields)s") % {"fields": ", ".join(missing)}
            )

    # Validate sender fields if provided
    if sender_email:
        _validate_email(sender_email)
    if sender_phone:
        _validate_phone(sender_phone)

    # 1. CREATE OR GET SENDER
    sender = None

    if sender_email or sender_phone:
        sender = Recipient.objects.filter(
            email=sender_email, mobile=sender_phone
        ).first()

    if not sender:
        default_email = sender_email or getattr(
            settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"
        )
        default_phone = sender_phone or getattr(settings, "MISSIVE_DEFAULT_PHONE", None)
        default_name = sender_name or getattr(
            settings, "MISSIVE_DEFAULT_SENDER_NAME", "System"
        )

        sender, _ = Recipient.objects.get_or_create(
            email=default_email,
            defaults={
                "name": default_name,
                "mobile": default_phone,
                "is_active": True,
                "can_be_sender": True,
            },
        )

    # 2. CREATE RECIPIENT
    recipient_name = ""
    if first_name and last_name:
        recipient_name = f"{first_name} {last_name}"
    elif first_name:
        recipient_name = first_name
    elif last_name:
        recipient_name = last_name
    elif denomination:
        recipient_name = denomination
    else:
        unique_id = str(uuid.uuid4())
        recipient_name = f"User_{unique_id}"

    recipient_data = {
        "is_active": True,
        "name": recipient_name,
    }

    if phone:
        recipient_data["mobile"] = phone
    if email:
        recipient_data["email"] = email
    if address:
        recipient_data["address_line1"] = address.get("street", "")
        recipient_data["city"] = address.get("city", "")
        recipient_data["postal_code"] = address.get("postal_code", "")
        recipient_data["country"] = address.get("country", "FR")

    lookup_fields = {}
    if email:
        lookup_fields["email"] = email
    elif phone:
        lookup_fields["mobile"] = phone
    else:
        lookup_fields["name"] = recipient_name

    recipient, _ = Recipient.objects.get_or_create(
        **lookup_fields, defaults=recipient_data
    )

    # 3. CREATE MISSIVE
    if missive_type == "EMAIL" and not subject:
        sender_display = (
            getattr(sender, "display_name", None) or sender.name or "System"
        )
        subject = _("Message from %(sender)s") % {"sender": sender_display}

    max_subject_length = getattr(settings, "MISSIVE_MAX_SUBJECT_LENGTH", 998)
    if subject and len(subject) > max_subject_length:
        raise MissiveValidationError(
            _("Subject too long (max: %(max)s chars)") % {"max": max_subject_length}
        )

    missive_data = {
        "missive_type": missive_type,
        "sender": sender,
        "recipient": recipient,
        "body": content,
        "subject": subject or "",
    }

    # Add optional kwargs
    if "priority" in kwargs:
        missive_data["priority"] = kwargs.pop("priority")
    if "is_registered" in kwargs:
        missive_data["is_registered"] = kwargs.pop("is_registered")
    if "requires_signature" in kwargs:
        missive_data["requires_signature"] = kwargs.pop("requires_signature")
    if "provider_options" in kwargs:
        missive_data["provider_options"] = kwargs.pop("provider_options")

    missive = Missive.objects.create(**missive_data)

    # Force provider if specified
    if provider:
        missive._provider_name = provider

    # 4. SEND MISSIVE
    sender_instance = MissiveSender()
    sender_instance.send(missive)

    return missive


def send_sms(phone: str, content: str, **kwargs) -> Missive:
    """Shortcut to send an SMS."""
    return send_missive("sms", phone=phone, content=content, **kwargs)


def send_email(email: str, subject: str, content: str, **kwargs) -> Missive:
    """Shortcut to send an email."""
    return send_missive(
        "email", email=email, subject=subject, content=content, **kwargs
    )


def send_whatsapp(phone: str, content: str, **kwargs) -> Missive:
    """Shortcut to send a WhatsApp message (via Twilio by default)."""
    if "provider" not in kwargs:
        kwargs["provider"] = "twilio"
    return send_missive("branded", phone=phone, content=content, **kwargs)


def send_slack(channel_id: str, content: str, **kwargs) -> Missive:
    """Shortcut to send a Slack message."""
    if "provider" not in kwargs:
        kwargs["provider"] = "slack"
    if "provider_options" not in kwargs:
        kwargs["provider_options"] = {}
    kwargs["provider_options"]["channel_id"] = channel_id

    if "first_name" not in kwargs:
        kwargs["first_name"] = f"Slack_{channel_id}"

    return send_missive("branded", content=content, **kwargs)


def send_telegram(chat_id: str, content: str, **kwargs) -> Missive:
    """Shortcut to send a Telegram message."""
    if "provider" not in kwargs:
        kwargs["provider"] = "telegram"
    if "provider_options" not in kwargs:
        kwargs["provider_options"] = {}
    kwargs["provider_options"]["chat_id"] = chat_id

    if "first_name" not in kwargs:
        kwargs["first_name"] = f"Telegram_{chat_id}"

    return send_missive("branded", content=content, **kwargs)
