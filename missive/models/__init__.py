"""
Django Missive Models.
Tous les modèles sont importés ici pour faciliter l'usage.
"""

from .attachment import MissiveAttachment

# Import des choix (enums)
from .choices import MissivePriority, MissiveStatus, MissiveType, RecipientType
from .event import MissiveEvent
from .missive import Missive
from .provider import ProviderInfo  # Modèle virtuel pour l'admin

# Import des modèles
from .recipient import Recipient
from .template import MissiveTemplate

__all__ = [
    # Choix
    "RecipientType",
    "MissiveType",
    "MissiveStatus",
    "MissivePriority",
    # Modèles
    "Recipient",
    "Missive",
    "MissiveAttachment",
    "MissiveEvent",
    "MissiveTemplate",
    "ProviderInfo",  # Modèle virtuel
]
