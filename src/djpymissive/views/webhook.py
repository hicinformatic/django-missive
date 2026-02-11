"""Webhook view for receiving provider events."""

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView

from ..models.choices import event_to_missive_status
from ..models.provider import MissiveProviderModel
from ..models.event import MissiveEvent
from ..models.missive import Missive


@method_decorator(csrf_exempt, name="dispatch")
class WebhookView(DetailView):
    """Webhook view based on provider model."""

    model = MissiveProviderModel
    slug_field = "name"
    slug_url_kwarg = "provider"

    def post(self, request, *args, **kwargs):
        """Handle webhook POST request."""
        provider = self.get_object()
        normalized = provider._provider.handle_webhook(request.body)
        missive = Missive.objects.get(external_id=normalized["external_id"])
        event = MissiveEvent.objects.create(
            missive=missive,
            event=normalized["event"],
            description=normalized["event"],
            occurred_at=normalized["occurred_at"],
            trace=normalized["trace"],
        )
        missive.status = event_to_missive_status(event.event)
        missive.save(update_fields=["status"])
        return HttpResponse(status=200)

    def get(self, request, *args, **kwargs):
        """Handle webhook GET request."""
        provider = self.get_object()
        provider._provider.handle_webhook(request.body)
        return HttpResponse(status=200)