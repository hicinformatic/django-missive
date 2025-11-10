"""
Administration des modèles Missive.

Ce module regroupe tous les fichiers d'administration des différents modèles.
"""

from ..helpers import (
    get_all_provider_choices,
    get_provider_name_from_path,
    get_providers_from_config,
)
from .attachment import MissiveAttachmentAdmin, MissiveAttachmentInline
from .event import MissiveEventAdmin, MissiveEventInline

# Importer tous les admins pour qu'ils soient enregistrés
from .missive import MissiveAdmin, MissiveAdminForm
from .provider import ProviderInfoAdmin
from .recipient import RecipientAdmin
from .template import MissiveTemplateAdmin

# Configurer les inlines pour MissiveAdmin (après toutes les imports)
MissiveAdmin.inlines = [MissiveAttachmentInline, MissiveEventInline]

__all__ = [
    # Missive
    "MissiveAdmin",
    "MissiveAdminForm",
    # Attachment
    "MissiveAttachmentAdmin",
    "MissiveAttachmentInline",
    # Event
    "MissiveEventAdmin",
    "MissiveEventInline",
    # Recipient
    "RecipientAdmin",
    # Template
    "MissiveTemplateAdmin",
    # Provider Info
    "ProviderInfoAdmin",
    # Helpers
    "get_provider_name_from_path",
    "get_providers_from_config",
    "get_all_provider_choices",
]
