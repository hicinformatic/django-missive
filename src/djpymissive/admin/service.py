from djproviderkit.admin.service import ProviderServiceAdmin
from djpymissive.models.service import MissiveServiceModel
from django.contrib import admin

@admin.register(MissiveServiceModel)
class MissiveServiceAdmin(ProviderServiceAdmin):
    """Admin for missive services."""
    pass