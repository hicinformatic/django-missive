"""Admin views for Django Missive."""

from django.contrib import admin
from django.urls import path

from djgeoaddress.views import address_autocomplete_view


def get_admin_urls():
    """Get admin URL patterns for address autocomplete."""
    return [
        path(
            "address/autocomplete/",
            admin.site.admin_view(address_autocomplete_view),
            name="missive_address_autocomplete",
        ),
    ]

