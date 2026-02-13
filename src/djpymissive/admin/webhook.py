"""Admin for webhook model."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ..models.webhook import MissiveWebhook
from django_boosted import AdminBoostModel
from urllib.parse import unquote
from djpymissive.forms.webhook import WebhookForm
from django_boosted.decorators import admin_boost_view
from django.utils.safestring import mark_safe


class ProviderListFilter(admin.SimpleListFilter):
    """Custom filter for provider field."""
    
    title = _("Provider")
    parameter_name = "provider"
    
    def lookups(self, request, model_admin):
        """Return list of providers as filter options."""
        try:
            # Get the provider field from the model
            provider_field = MissiveWebhook._meta.get_field("provider")
            # Use the field's method to get choices
            choices = provider_field.get_provider_choices()
            # Remove the empty choice
            return [choice for choice in choices if choice[0]]
        except Exception:
            return []
    
    def queryset(self, request, queryset):
        """Filter queryset by provider."""
        return queryset


@admin.register(MissiveWebhook)
class MissiveWebhookAdmin(AdminBoostModel):
    """Admin for missive webhooks."""

    list_display = [
        "id",
        "provider",
        "type",
        "url",
        "created_at",
        "updated_at",
    ]
    list_filter = [ProviderListFilter, "type"]
    search_fields = ["url", "description",]
    readonly_fields = ["id", "webhook_id", "provider", "created_at", "updated_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def change_fieldsets(self):
        self.add_to_fieldset(None, ["type", "url",])
        self.add_to_fieldset(_("Backend"), ["provider", "webhook_id",])
        self.add_to_fieldset(_("Timestamps"), ["created_at", "updated_at"])

    def get_object(self, request, object_id, from_field=None):
        provider, webhook_id = unquote(object_id).split("-", 1)
        qs = self.model.objects.get_queryset(provider)
        print("webhook_id", webhook_id)
        return next((item for item in qs if str(item.id) == str(webhook_id)), None)

    def get_queryset(self, request):
        if provider := request.GET.get("provider"):
            return self.model.objects.get_queryset(provider)
        return self.model.objects.none()

    def save_model(self, request, obj, form, change):
        from django.contrib import messages
        service = f"update_webhook_{obj.type}".lower()
        provider = obj.get_provider()
        if hasattr(provider._provider, service):
            try:
                getattr(provider._provider, service)(webhook_id=obj.webhook_id, webhook_url=obj.url)
                messages.success(request, _("Webhook updated successfully."))
            except Exception as e:
                messages.error(request, _("Webhook update failed: %s") % e)
        return True

    @admin_boost_view("adminform", "Add Webhook", requires_object=False)
    def add_webhook_view(self, request, form=None):
        from django.contrib import messages
        if form is not None:
            # Form was validated, save the webhook
            webhook = form.save()
            messages.success(request, f"Webhook added successfully!")
            return {"redirect_url": ".."}
        
        return {
            "form": WebhookForm(),
            "has_add_permission": True,
            "has_change_permission": True,
        }