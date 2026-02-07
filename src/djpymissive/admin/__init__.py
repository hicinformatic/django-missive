"""Admin configuration for djpymissive."""

from .attachment import MissiveAttachmentAdmin
from .event import MissiveEventAdmin
from .missive import MissiveAdmin
from .provider import ProviderAdmin
from .related_object import MissiveRelatedObjectAdmin

__all__ = [
    "ProviderAdmin",
    "MissiveAdmin",
    "MissiveAttachmentAdmin",
    "MissiveEventAdmin",
    "MissiveRelatedObjectAdmin",
]
