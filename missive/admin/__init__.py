"""Administration des modèles Missive."""

from ..decorators import sandbox_warning
from ..helpers import (
    get_all_provider_choices,
    get_provider_name_from_path,
    get_providers_from_config,
)
from .address_backend import AddressBackendInfoAdmin
from .attachment import MissiveAttachmentAdmin, MissiveAttachmentInline
from .event import MissiveEventAdmin, MissiveEventInline

from .missive import MissiveAdmin, MissiveAdminForm
from .provider import ProviderInfoAdmin
from .template import MissiveTemplateAdmin

MissiveAdmin.inlines = [MissiveAttachmentInline, MissiveEventInline]

__all__ = [
    "sandbox_warning",
    "MissiveAdmin",
    "MissiveAdminForm",
    "MissiveAttachmentAdmin",
    "MissiveAttachmentInline",
    "MissiveEventAdmin",
    "MissiveEventInline",
    "MissiveTemplateAdmin",
    "ProviderInfoAdmin",
    "AddressBackendInfoAdmin",
    "get_provider_name_from_path",
    "get_providers_from_config",
    "get_all_provider_choices",
]
