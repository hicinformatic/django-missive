"""
Provider pour les notifications in-app.
"""

from typing import Dict, Tuple

from django.utils import timezone

from ..models import MissiveStatus
from .base import BaseProvider


class InAppNotificationProvider(BaseProvider):
    """Provider pour les notifications in-app"""

    name = "notification"
    display_name = "Notification In-App"
    supported_types = ["NOTIFICATION"]
    services = ["notification", "push_notification", "badge"]
    required_packages = []
    description_text = (
        "Notifications dans l'application (in-app) sans dépendance externe"
    )

    def send_notification(self, **kwargs) -> bool:
        """Crée une notification in-app"""
        # Validation
        is_valid, error = self.validate()
        if not is_valid:
            self._update_status(MissiveStatus.FAILED, error_message=error)
            return False

        if not self.missive.recipient_user:
            self._update_status(
                MissiveStatus.FAILED, error_message="Utilisateur manquant"
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

            self._create_event("sent", "Notification créée")
            self._create_event("delivered", "Notification délivrée")

            return True

        except Exception as e:
            self._update_status(MissiveStatus.FAILED, error_message=str(e))
            self._create_event("failed", str(e))
            return False

    def validate_webhook_signature(
        self, payload: Dict, headers: Dict
    ) -> Tuple[bool, str]:
        """Pas de webhooks pour les notifications in-app"""
        return False, "Les notifications in-app n'utilisent pas de webhooks"

    def get_service_status(self) -> Dict:
        """
        Récupère le statut du système de notification in-app.

        Les notifications in-app sont gérées en local, pas de limitation.

        Returns:
            Dict avec status, disponibilité, etc.
        """
        from django.utils import timezone

        # Système local, toujours disponible
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
                "per_second": None,  # Pas de limite
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
