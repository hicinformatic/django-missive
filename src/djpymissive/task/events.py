from datetime import timezone as dt_timezone

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from ..models.event import MissiveEvent
from ..models.missive import Missive
from ..models.recipient import MissiveRecipient
from ..models.choices import MissiveRecipientType


def _get_occurred_at(occurred_at):
    """Get occurred at from normalized event."""
    if isinstance(occurred_at, str):
        occurred_at = parse_datetime(occurred_at.replace("Z", "+00:00"))
    if occurred_at is not None and timezone.is_naive(occurred_at):
        return timezone.make_aware(occurred_at, dt_timezone.utc)
    if occurred_at is None:
        return timezone.now()
    return occurred_at

def _process_normalized_event_recipient(missive, recipient, _event_type):
    """Process normalized webhook event recipient."""
    recipient = MissiveRecipient.objects.get(
        **{missive.missive_support.lower(): recipient},
        missive=missive,
        recipient_type__in=[
            MissiveRecipientType.RECIPIENT,
            MissiveRecipientType.CC,
            MissiveRecipientType.BCC,
        ],
    )
    return recipient

def _process_normalized_event(normalized):
    """Process normalized webhook event and update missive/recipient status."""
    missive = Missive.objects.get(external_id=normalized["external_id"])
    recipient = None
    if normalized.get("recipient"):
        recipient = _process_normalized_event_recipient(
            missive, normalized.get("recipient"), normalized["event"]
        )
    occurred_at = _get_occurred_at(normalized.get("occurred_at"))
    MissiveEvent.objects.get_or_create(
        missive=missive,
        recipient=recipient,
        event=normalized["event"],
        description=normalized["description"],
        occurred_at=occurred_at,
        trace=normalized["trace"],
    )
    return missive, recipient


def handle_events(events: list[dict]):
    missive = None
    recipients = []
    for event in events:
        missive, recipient = _process_normalized_event(event)
        if recipient not in recipients:
            recipients.append(recipient)
    if missive:
        missive.set_last_status()
    for recipient in recipients:
        recipient.set_last_status()
