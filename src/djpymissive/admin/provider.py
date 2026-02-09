"""Admin for provider model."""

from django.contrib import admin

from djproviderkit.admin.provider import BaseProviderAdmin

from ..models.provider import MissiveProviderModel
from django_boosted.decorators import admin_boost_view


@admin.register(MissiveProviderModel)
class ProviderAdmin(BaseProviderAdmin):
    """Admin for missive providers."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin_boost_view("message", "Custom Message View")
    def custom_message_status_object_view(self, request, obj):
        return {"message": "This is a custom message view"}
