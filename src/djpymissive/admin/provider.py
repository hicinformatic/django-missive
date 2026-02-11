"""Admin for provider model."""

from django.contrib import admin

from djproviderkit.admin.provider import BaseProviderAdmin

from ..models.provider import MissiveProviderModel
from django_boosted.decorators import admin_boost_view
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


@admin.register(MissiveProviderModel)
class ProviderAdmin(BaseProviderAdmin):
    """Admin for missive providers."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
