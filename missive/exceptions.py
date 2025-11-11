"""
Exceptions personnalisées pour django-missive.
"""


class MissiveError(Exception):
    """Exception de base pour toutes les erreurs django-missive."""

    pass


class MissiveValidationError(MissiveError):
    """Erreur de validation des données d'entrée."""

    pass


class MissiveProviderError(MissiveError):
    """Erreur liée à un provider (configuration, envoi, etc.)."""

    pass


class MissiveConfigError(MissiveError):
    """Erreur de configuration django-missive."""

    pass


class MissiveWebhookError(MissiveError):
    """Erreur lors du traitement d'un webhook."""

    pass


class MissiveNotFoundError(MissiveError):
    """Missive introuvable."""

    pass


class MissiveProviderNotAvailableError(MissiveProviderError):
    """Aucun provider disponible pour le type de missive."""

    pass

