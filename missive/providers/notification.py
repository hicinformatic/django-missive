"""In-app notification provider."""

from typing import Dict, Tuple

from django.utils import timezone

from ..models import MissiveStatus
from .base import BaseProvider


class InAppNotificationProvider(BaseProvider):
    """In-app notification provider."""

    name = "notification"
    display_name = "Notification In-App"
    supported_types = ["NOTIFICATION"]
    services = ["notification", "push_notification", "badge"]
    required_packages = []
    description_text = (
        "In-app notifications without external dependency"
    )

    def send_notification(self, **kwargs) -> bool:
        """Create an in-app notification"""
        # Validation
        is_valid, error = self.validate()
        if not is_valid:
            self._update_status(MissiveStatus.FAILED, error_message=error)
            return False

        if not self.missive.recipient_user:
            self._update_status(
                MissiveStatus.FAILED, error_message="User missing"
            )
            return False

        try:
            # TODO: Créer la notification
            # Peut utiliser:
            # - Django signals
            # - WebSocket (channels)
            # - Firebase Cloud Messaging
            # - OneSignal
            #
            # Exemple avec signal:
            # from django.dispatch import Signal
            # notification_created = Signal()
            # notification_created.send(
            #     sender=self.__class__,
            #     missive=self.missive,
            #     recipient=self.missive.recipient_user,
            #     subject=self.missive.subject,
            #     body=self.missive.body
            # )

            # La notification est instantanée
            self._update_status(
                MissiveStatus.SENT,
                provider=self.name,
                sent_at=timezone.now(),
                delivered_at=timezone.now(),
            )

            self._create_event("sent", "Notification created")
            self._create_event("delivered", "Notification delivered")

            return True

        except Exception as e:
            self._update_status(MissiveStatus.FAILED, error_message=str(e))
            self._create_event("failed", str(e))
            return False

    def validate_webhook_signature(
        self, payload: Dict, headers: Dict
    ) -> Tuple[bool, str]:
        """No webhooks for in-app notifications"""
        return False, "In-app notifications do not use webhooks"

    def get_service_status(self) -> Dict:
        """
        Gets in-app notification system status.

        In-app notifications are managed locally, no limits.

        Returns:
            Dict with status, availability, etc.
        """
        from django.utils import timezone

        # Local system, always available
        return {
            "status": "operational",
            "is_available": True,
            "services": self.services,
            "credits": {
                "type": "unlimited",
                "remaining": None,
                "currency": "",
                "limit": None,
                "percentage": None,
            },
            "rate_limits": {
                "per_second": None,  # No limit
            },
            "sla": {
                "uptime_percentage": 100.0,  # Local
            },
            "last_check": timezone.now(),
            "warnings": [],
            "details": {
                "provider_type": "In-App (Local)",
                "note": "Notifications stockées en base de données Django",
            },
        }
