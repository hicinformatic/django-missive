"""
Django Missive Models.
Tous les modèles sont importés ici pour faciliter l'usage.
"""

from .attachment import MissiveAttachment

# Import des choix (enums)
from .choices import MissivePriority, MissiveStatus, MissiveType, RecipientType
from .event import MissiveEvent
from .missive import Missive

# Import des modèles
from .recipient import Recipient
from .template import MissiveTemplate
from .provider import ProviderInfo  # Modèle virtuel pour l'admin

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
