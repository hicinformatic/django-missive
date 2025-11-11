"""
Missive models administration.

This module groups all admin files for different models.
"""

from ..decorators import sandbox_warning
from ..helpers import (
    get_all_provider_choices,
    get_provider_name_from_path,
    get_providers_from_config,
)
from .attachment import MissiveAttachmentAdmin, MissiveAttachmentInline
from .event import MissiveEventAdmin, MissiveEventInline

# Import all admins to register them
from .missive import MissiveAdmin, MissiveAdminForm
from .provider import ProviderInfoAdmin
from .recipient import RecipientAdmin
from .template import MissiveTemplateAdmin

# Configure inlines for MissiveAdmin (after all imports)
MissiveAdmin.inlines = [MissiveAttachmentInline, MissiveEventInline]

__all__ = [
    # Decorators
    "sandbox_warning",
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
