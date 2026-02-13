"""Admin configuration for djpymissive."""

from .document import MissiveDocumentAdmin
from .campaign import MissiveCampaignAdmin
from .event import MissiveEventAdmin
from .recipient import MissiveRecipientAdmin
from .missive import MissiveAdmin
from .provider import ProviderAdmin
from .related_object import MissiveRelatedObjectAdmin
from .webhook import MissiveWebhookAdmin

__all__ = [
    "ProviderAdmin",
    "MissiveCampaignAdmin",
    "MissiveAdmin",
    "MissiveDocumentAdmin",
    "MissiveEventAdmin",
    "MissiveRelatedObjectAdmin",
    "MissiveRecipientAdmin",
    "MissiveWebhookAdmin",
]
