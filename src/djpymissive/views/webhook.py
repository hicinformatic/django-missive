"""Webhook view for receiving provider events."""


from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView

from ..task.events import handle_events
from ..models.provider import MissiveProviderModel


@method_decorator(csrf_exempt, name="dispatch")
class WebhookView(DetailView):
    """Webhook view based on provider model."""

    model = MissiveProviderModel
    slug_field = "name"
    slug_url_kwarg = "provider"

    def post(self, request, *args, **kwargs):
        """Handle webhook POST request."""
        provider = self.get_object()
        missive_type = kwargs.get("missive_type")
        handler = f"handle_webhook_{missive_type.lower()}"
        normalized = provider._provider.call_service(handler, request.body)
        if normalized is not None and normalized.get("external_id"):
            missive = handle_events([normalized])
            if missive:
                missive.set_last_status()
        return HttpResponse(status=200)

    def get(self, request, *args, **kwargs):
        """Handle webhook GET request."""
        provider = self.get_object()
        normalized = provider._provider.handle_webhook(request.body)
        if normalized is not None and normalized.get("external_id"):
            missive = handle_events([normalized])
            if missive:
                missive.set_last_status()
        return HttpResponse(status=200)
