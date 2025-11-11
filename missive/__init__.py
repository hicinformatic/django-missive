"""
Django Missive - A Django library for missive management
"""

__version__ = "0.1.0"


def __getattr__(name):
    """Lazy imports pour éviter les imports circulaires"""
    if name == "Missive":
        from .models import Missive

        return Missive
    elif name == "MissiveType":
        from .models import MissiveType

        return MissiveType
    elif name == "MissiveStatus":
        from .models import MissiveStatus

        return MissiveStatus
    elif name == "MissivePriority":
        from .models import MissivePriority

        return MissivePriority
    elif name == "MissiveAttachment":
        from .models import MissiveAttachment

        return MissiveAttachment
    elif name == "MissiveEvent":
        from .models import MissiveEvent

        return MissiveEvent
    elif name == "MissiveTemplate":
        from .models import MissiveTemplate

        return MissiveTemplate
    elif name == "Recipient":
        from .models import Recipient

        return Recipient
    elif name == "RecipientType":
        from .models import RecipientType

        return RecipientType
    elif name == "MissiveSender":
        from .sender import MissiveSender

        return MissiveSender
    elif name == "MissiveBuilder":
        from .helpers import MissiveBuilder

        return MissiveBuilder
    elif name == "get_missives_stats_for_object":
        from .helpers import get_missives_stats_for_object

        return get_missives_stats_for_object
    # Shortcuts
    elif name == "send_missive":
        from .shortcuts import send_missive

        return send_missive
    elif name == "send_sms":
        from .shortcuts import send_sms

        return send_sms
    elif name == "send_email":
        from .shortcuts import send_email

        return send_email
    elif name == "send_whatsapp":
        from .shortcuts import send_whatsapp

        return send_whatsapp
    elif name == "send_slack":
        from .shortcuts import send_slack

        return send_slack
    elif name == "send_telegram":
        from .shortcuts import send_telegram

        return send_telegram
    # Exceptions
    elif name == "MissiveError":
        from .exceptions import MissiveError

        return MissiveError
    elif name == "MissiveValidationError":
        from .exceptions import MissiveValidationError

        return MissiveValidationError
    elif name == "MissiveProviderError":
        from .exceptions import MissiveProviderError

        return MissiveProviderError
    elif name == "MissiveConfigError":
        from .exceptions import MissiveConfigError

        return MissiveConfigError
    elif name == "MissiveWebhookError":
        from .exceptions import MissiveWebhookError

        return MissiveWebhookError
    elif name == "MissiveNotFoundError":
        from .exceptions import MissiveNotFoundError

        return MissiveNotFoundError
    elif name == "MissiveProviderNotAvailableError":
        from .exceptions import MissiveProviderNotAvailableError

        return MissiveProviderNotAvailableError
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    "__version__",
    # Models
    "Missive",
    "MissiveType",
    "MissiveStatus",
    "MissivePriority",
    "MissiveAttachment",
    "MissiveEvent",
    "MissiveTemplate",
    "Recipient",
    "RecipientType",
    # Sender
    "MissiveSender",
    "MissiveBuilder",
    "get_missives_stats_for_object",
    # Shortcuts
    "send_missive",
    "send_sms",
    "send_email",
    "send_whatsapp",
    "send_slack",
    "send_telegram",
    # Exceptions
    "MissiveError",
    "MissiveValidationError",
    "MissiveProviderError",
    "MissiveConfigError",
    "MissiveWebhookError",
    "MissiveNotFoundError",
    "MissiveProviderNotAvailableError",
]
