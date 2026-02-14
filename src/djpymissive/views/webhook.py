"""Webhook view for receiving provider events."""

import contextlib
from datetime import timezone as dt_timezone

from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView

from ..models.choices import event_to_missive_status, MissiveRecipientType
from ..models.provider import MissiveProviderModel
from ..models.event import MissiveEvent
from ..models.missive import Missive


@method_decorator(csrf_exempt, name="dispatch")
class WebhookView(DetailView):
    """Webhook view based on provider model."""

    model = MissiveProviderModel
    slug_field = "name"
    slug_url_kwarg = "provider"

    def _process_normalized_event(self, normalized):
        """Process normalized webhook event and update missive/recipient status."""
        with contextlib.suppress(Exception):
            missive = Missive.objects.get(external_id=normalized["external_id"])
            recipient = missive.to_missiverecipient.get(
                **{
                    missive.missive_support.lower(): normalized["recipient"],
                },
                missive=missive,
                recipient_type__in=[
                    MissiveRecipientType.RECIPIENT,
                    MissiveRecipientType.CC,
                    MissiveRecipientType.BCC,
                ],
            )
            occurred_at = normalized.get("occurred_at")
            if isinstance(occurred_at, str):
                occurred_at = parse_datetime(occurred_at.replace("Z", "+00:00"))
            if occurred_at is not None and timezone.is_naive(occurred_at):
                occurred_at = timezone.make_aware(occurred_at, dt_timezone.utc)
            if occurred_at is None:
                occurred_at = timezone.now()
            event, _ = MissiveEvent.objects.get_or_create(
                missive=missive,
                recipient=recipient,
                event=normalized["event"],
                description=normalized["description"],
                occurred_at=occurred_at,
                trace=normalized["trace"],
            )
            missive.status = event_to_missive_status(event.event)
            missive.save(update_fields=["status"])
            recipient.status = event_to_missive_status(event.event)
            recipient.save(update_fields=["status"])

    def post(self, request, *args, **kwargs):
        """Handle webhook POST request."""
        provider = self.get_object()
        missive_type = kwargs.get("missive_type")
        handler = f"handle_webhook_{missive_type.lower()}"
        normalized = provider._provider.call_service(handler, request.body)
        if normalized is not None and normalized.get("external_id"):
            self._process_normalized_event(normalized)
        return HttpResponse(status=200)

    def get(self, request, *args, **kwargs):
        """Handle webhook GET request."""
        provider = self.get_object()
        normalized = provider._provider.handle_webhook(request.body)
        if normalized is not None and normalized.get("external_id"):
            self._process_normalized_event(normalized)
        return HttpResponse(status=200)
