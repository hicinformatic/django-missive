"""Custom exceptions for django-missive."""


class MissiveError(Exception):
    """Base exception for all django-missive errors."""


class MissiveValidationError(MissiveError):
    """Input data validation error."""


class MissiveProviderError(MissiveError):
    """Provider-related error (config, sending, etc.)."""


class MissiveConfigError(MissiveError):
    """Django-missive configuration error."""


class MissiveWebhookError(MissiveError):
    """Webhook processing error."""


class MissiveNotFoundError(MissiveError):
    """Missive not found."""


class MissiveProviderNotAvailableError(MissiveProviderError):
    """No provider available for this missive type."""
