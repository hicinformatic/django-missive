"""Decorators for Django Missive."""

import importlib
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.utils.translation import gettext_lazy as _


def sandbox_warning(admin_class):
    """Adds sandbox warning messages in admin views when MISSIVE_SANDBOX is enabled."""

    original_changelist_view = admin_class.changelist_view
    original_add_view = admin_class.add_view
    original_change_view = admin_class.change_view

    @wraps(original_changelist_view)
    def changelist_view_with_warning(self, request, extra_context=None):
        """Overrides changelist_view with sandbox message."""
        extra_context = extra_context or {}

        if getattr(settings, "MISSIVE_SANDBOX", False):
            messages.warning(
                request,
                _(
                    "SANDBOX MODE ENABLED: All sends use test mode. "
                    "Messages will not be actually sent. "
                    "Disable MISSIVE_SANDBOX in settings.py to send in production."
                ),
            )

        return original_changelist_view(self, request, extra_context=extra_context)

    @wraps(original_add_view)
    def add_view_with_warning(self, request, form_url="", extra_context=None):
        """Overrides add_view with sandbox message."""
        extra_context = extra_context or {}

        if getattr(settings, "MISSIVE_SANDBOX", False):
            messages.warning(
                request,
                _("Sandbox mode active: This entry will be processed in test mode."),
            )

        return original_add_view(self, request, form_url, extra_context)

    @wraps(original_change_view)
    def change_view_with_warning(
        self, request, object_id, form_url="", extra_context=None
    ):
        """Overrides change_view with sandbox message."""
        extra_context = extra_context or {}

        if getattr(settings, "MISSIVE_SANDBOX", False):
            messages.warning(
                request,
                _("Sandbox mode active: This entry will be processed in test mode."),
            )

        return original_change_view(self, request, object_id, form_url, extra_context)

    admin_class.changelist_view = changelist_view_with_warning
    admin_class.add_view = add_view_with_warning
    admin_class.change_view = change_view_with_warning

    return admin_class


def library_presence_warning(admin_class, *, module_name: str = "python_missive"):
    """
    Adds an admin warning if the external library is not installed.
    Default checks for 'python_missive' importability.
    """
    original_changelist_view = admin_class.changelist_view
    original_add_view = admin_class.add_view
    original_change_view = admin_class.change_view

    def _warn_if_missing(request):
        try:
            importlib.import_module(module_name)
            return
        except Exception:
            messages.warning(
                request,
                _(
                    "External library '%(module)s' is not installed. "
                    "Some provider features may be unavailable. "
                    "Install it or configure providers accordingly."
                )
                % {"module": module_name},
            )

    @wraps(original_changelist_view)
    def changelist_view_with_lib_check(self, request, extra_context=None):
        _warn_if_missing(request)
        return original_changelist_view(self, request, extra_context=extra_context)

    @wraps(original_add_view)
    def add_view_with_lib_check(self, request, form_url="", extra_context=None):
        _warn_if_missing(request)
        return original_add_view(self, request, form_url, extra_context)

    @wraps(original_change_view)
    def change_view_with_lib_check(
        self, request, object_id, form_url="", extra_context=None
    ):
        _warn_if_missing(request)
        return original_change_view(self, request, object_id, form_url, extra_context)

    admin_class.changelist_view = changelist_view_with_lib_check
    admin_class.add_view = add_view_with_lib_check
    admin_class.change_view = change_view_with_lib_check

    return admin_class
