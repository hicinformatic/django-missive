"""Manager for missive providers."""

from djproviderkit.managers import BaseProviderManager


class ProviderManager(BaseProviderManager):
    """Manager for missive providers."""
    package_name = 'pymissive'
