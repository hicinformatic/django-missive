"""Django Missive - Django library for missive management."""

from importlib import import_module

__version__ = "0.1.0"

_LAZY_IMPORTS = {
    "Missive": ".models:Missive",
    "MissiveType": ".models:MissiveType",
    "MissiveStatus": ".models:MissiveStatus",
    "MissivePriority": ".models:MissivePriority",
    "MissiveAttachment": ".models:MissiveAttachment",
    "MissiveEvent": ".models:MissiveEvent",
    "MissiveTemplate": ".models:MissiveTemplate",
    "RecipientType": ".models:RecipientType",
    "MissiveSender": ".sender:MissiveSender",
    "MissiveBuilder": ".helpers:MissiveBuilder",
    "get_missives_stats_for_object": ".helpers:get_missives_stats_for_object",
    "send_missive": ".shortcuts:send_missive",
    "send_sms": ".shortcuts:send_sms",
    "send_email": ".shortcuts:send_email",
    "send_whatsapp": ".shortcuts:send_whatsapp",
    "send_slack": ".shortcuts:send_slack",
    "send_telegram": ".shortcuts:send_telegram",
    "MissiveError": ".exceptions:MissiveError",
    "MissiveValidationError": ".exceptions:MissiveValidationError",
    "MissiveProviderError": ".exceptions:MissiveProviderError",
    "MissiveConfigError": ".exceptions:MissiveConfigError",
    "MissiveWebhookError": ".exceptions:MissiveWebhookError",
    "MissiveNotFoundError": ".exceptions:MissiveNotFoundError",
    "MissiveProviderNotAvailableError": ".exceptions:MissiveProviderNotAvailableError",
}


def __getattr__(name):
    """Lazy imports to avoid circular dependencies."""
    target = _LAZY_IMPORTS.get(name)
    if not target:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    module_path, attr_name = target.split(":")
    module = import_module(module_path, __name__)
    return getattr(module, attr_name)


__all__ = ["__version__", *_LAZY_IMPORTS.keys()]
