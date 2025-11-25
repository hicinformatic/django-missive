"""Shortcut functions to send missives quickly."""

import re
import uuid
from typing import Dict, Optional, Union

from django.conf import settings
from django.utils.functional import Promise
from django.utils.translation import gettext_lazy

try:
    from python_missive import format_phone_international
except ImportError:
    format_phone_international = None

from .exceptions import MissiveValidationError
from .models import Missive, MissiveType
from .sender import MissiveSender


def _validate_email(email: str) -> None:
    """Validate email format (RFC 5321 compliant)."""
    if not email:
        raise MissiveValidationError(gettext_lazy("Email address cannot be empty"))

    max_email_length = getattr(settings, "MISSIVE_MAX_EMAIL_LENGTH", 254)
    if len(email) > max_email_length:
        raise MissiveValidationError(gettext_lazy("Email address is too long"))

    email_pattern = r"^[a-zA-Z0-9._%+-]{1,64}@[a-zA-Z0-9.-]{1,253}\.[a-zA-Z]{2,63}$"
    if not re.match(email_pattern, email):
        raise MissiveValidationError(gettext_lazy("Invalid email format"))


def _clean_phone(phone: str, country_code: Optional[str] = None) -> str:
    """Clean and format phone number to international E.164 format.

    Uses format_phone_international from python-missive if available,
    otherwise returns the phone as-is.
    """
    if not phone:
        return phone

    if format_phone_international:
        try:
            result = format_phone_international(phone, country_code)
            return str(result) if result is not None else phone
        except Exception:
            # If formatting fails, return original phone
            return phone

    return phone


def _validate_phone(phone: str, country_code: Optional[str] = None) -> str:
    """Clean, format and validate phone number (E.164 standard).

    Returns the cleaned phone number in international format.
    """
    if not phone:
        raise MissiveValidationError(gettext_lazy("Phone number cannot be empty"))

    # Clean and format the phone number
    cleaned_phone = _clean_phone(phone, country_code)

    max_phone_length = getattr(settings, "MISSIVE_MAX_PHONE_LENGTH", 16)
    if len(cleaned_phone) > max_phone_length:
        raise MissiveValidationError(gettext_lazy("Phone number is too long"))

    phone_pattern = r"^\+[1-9]\d{1,14}$"
    if not re.match(phone_pattern, cleaned_phone):
        raise MissiveValidationError(
            gettext_lazy("Invalid phone format. Expected E.164 (e.g. +33612345678)")
        )

    return cleaned_phone


def _validate_content(content: str, missive_type: str = "") -> None:
    """Validate missive content."""
    if not content or not content.strip():
        msg: Union[Promise, str] = gettext_lazy("Content cannot be empty")
        if missive_type:
            msg = gettext_lazy("%(type)s content cannot be empty") % {"type": missive_type}
        raise MissiveValidationError(msg)

    max_length = getattr(settings, "MISSIVE_MAX_CONTENT_LENGTH", 1_000_000)
    if len(content) > max_length:
        raise MissiveValidationError(
            gettext_lazy("Content too long (max: %(max)s chars)") % {"max": max_length}
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
    """Sends missive with minimal info. Auto-generates missing fields."""
    missive_type = missive_type.upper()
    if not hasattr(MissiveType, missive_type):
        raise MissiveValidationError(
            gettext_lazy("Unsupported missive type: %(type)s") % {"type": missive_type}
        )

    _validate_content(content, missive_type)

    # Get country code from address if available (for phone formatting)
    country_code = None
    if address and isinstance(address, dict):
        country_code = address.get("country")

    if missive_type in ("SMS", "VOICE_CALL"):
        if not phone:
            raise MissiveValidationError(
                gettext_lazy("'phone' field required for %(type)s") % {"type": missive_type}
            )
        phone = _validate_phone(phone, country_code)

    elif missive_type == "EMAIL":
        if not email:
            raise MissiveValidationError(gettext_lazy("'email' field required for EMAIL"))
        _validate_email(email)

        if subject is not None and not subject.strip():
            raise MissiveValidationError(gettext_lazy("Email subject cannot be empty"))

    elif missive_type == "BRANDED":
        if phone:
            phone = _validate_phone(phone, country_code)
        if email:
            _validate_email(email)

    elif missive_type in ("POSTAL", "POSTAL_REGISTERED"):
        if not address or not isinstance(address, dict):
            raise MissiveValidationError(
                gettext_lazy("'address' dict required for %(type)s missives")
                % {"type": missive_type}
            )
        required_fields = ["street", "city", "postal_code", "country"]
        missing = [f for f in required_fields if not address.get(f)]
        if missing:
            raise MissiveValidationError(
                gettext_lazy("Missing address fields: %(fields)s") % {"fields": ", ".join(missing)}
            )
        if missive_type == "POSTAL_REGISTERED":
            kwargs.setdefault("is_registered", True)

    if sender_email:
        _validate_email(sender_email)
    if sender_phone:
        sender_phone = _validate_phone(sender_phone)

    # Extract sender data
    default_email = sender_email or getattr(
        settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"
    )
    default_phone = sender_phone or getattr(settings, "MISSIVE_DEFAULT_PHONE", None)
    default_name = sender_name or getattr(
        settings, "MISSIVE_DEFAULT_SENDER_NAME", "System"
    )

    # Extract recipient name
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

    if missive_type == "EMAIL" and not subject:
        sender_display = sender_name or default_name or "System"
        subject = gettext_lazy("Message from %(sender)s") % {"sender": sender_display}

    max_subject_length = getattr(settings, "MISSIVE_MAX_SUBJECT_LENGTH", 998)
    if subject and len(subject) > max_subject_length:
        raise MissiveValidationError(
            gettext_lazy("Subject too long (max: %(max)s chars)") % {"max": max_subject_length}
        )

    missive_data = {
        "missive_type": missive_type,
        "sender_name": default_name,
        "sender_email": default_email,
        "sender_phone": default_phone,
        "recipient_name": recipient_name,
        "recipient_email": email,
        "recipient_phone": phone,
        "body": content,
        "subject": subject or "",
    }

    # Add recipient address fields if provided
    if address:
        missive_data["recipient_address_line1"] = address.get("street", "")
        missive_data["recipient_city"] = address.get("city", "")
        missive_data["recipient_postal_code"] = address.get("postal_code", "")
        missive_data["recipient_country"] = address.get("country", "FR")

    if "priority" in kwargs:
        missive_data["priority"] = kwargs.pop("priority")
    if "is_registered" in kwargs:
        missive_data["is_registered"] = kwargs.pop("is_registered")
    if "requires_signature" in kwargs:
        missive_data["requires_signature"] = kwargs.pop("requires_signature")
    if "provider_options" in kwargs:
        missive_data["provider_options"] = kwargs.pop("provider_options")

    missive: Missive = Missive.objects.create(**missive_data)

    if provider:
        missive._provider_name = provider  # type: ignore[attr-defined]

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
    """Sends WhatsApp message (via Twilio by default)."""
    if "provider" not in kwargs:
        kwargs["provider"] = "twilio"
    return send_missive("branded", phone=phone, content=content, **kwargs)


def send_slack(channel_id: str, content: str, **kwargs) -> Missive:
    """Sends Slack message."""
    if "provider" not in kwargs:
        kwargs["provider"] = "slack"
    if "provider_options" not in kwargs:
        kwargs["provider_options"] = {}
    kwargs["provider_options"]["channel_id"] = channel_id

    if "first_name" not in kwargs:
        kwargs["first_name"] = f"Slack_{channel_id}"

    return send_missive("branded", content=content, **kwargs)


def send_telegram(chat_id: str, content: str, **kwargs) -> Missive:
    """Sends Telegram message."""
    if "provider" not in kwargs:
        kwargs["provider"] = "telegram"
    if "provider_options" not in kwargs:
        kwargs["provider_options"] = {}
    kwargs["provider_options"]["chat_id"] = chat_id

    if "first_name" not in kwargs:
        kwargs["first_name"] = f"Telegram_{chat_id}"

    return send_missive("branded", content=content, **kwargs)
