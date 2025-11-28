"""Administration des modèles Missive."""

from ..decorators import sandbox_warning
from ..helpers import (
    get_all_provider_choices,
    get_provider_name_from_path,
    get_providers_from_config,
)
from .address_backend import AddressBackendInfoAdmin, AddressLookupAdmin
from .attachment import MissiveAttachmentAdmin, MissiveAttachmentInline
from .event import MissiveEventAdmin, MissiveEventInline
from .missive import MissiveAdmin, MissiveAdminForm
from .provider import ProviderInfoAdmin
from .template import MissiveTemplateAdmin

MissiveAdmin.inlines = [MissiveAttachmentInline, MissiveEventInline]

# Register admin views for address autocomplete
from django.contrib import admin
from .views import get_admin_urls

_admin_urls = get_admin_urls()
if _admin_urls:
    _original_get_urls = admin.site.get_urls

    def _get_urls_with_address_autocomplete():
        return _admin_urls + _original_get_urls()

    admin.site.get_urls = _get_urls_with_address_autocomplete

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
    "AddressLookupAdmin",
    "get_provider_name_from_path",
    "get_providers_from_config",
    "get_all_provider_choices",
]
