"""
Utility functions for the Missive app
"""


def get_missive_config():
    """
    Get the configuration for the Missive app from Django settings.
    Returns a dictionary with default values if not configured.
    """
    from django.conf import settings

    default_config = {
        # Add your default configuration options here
    }

    return getattr(settings, "MISSIVE_CONFIG", default_config)
