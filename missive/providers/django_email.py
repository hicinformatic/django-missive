"""Django Email provider (native SMTP)."""

from typing import Dict, Tuple

from ..models import MissiveStatus
from .base import BaseProvider


class DjangoEmailProvider(BaseProvider):
    """Django's native email system provider."""

    name = "Django Email"
    display_name = "Django Email (default)"
    supported_types = ["EMAIL"]
    services = ["email"]
    config_keys = ["EMAIL_HOST", "EMAIL_PORT", "EMAIL_HOST_USER", "EMAIL_HOST_PASSWORD"]
    required_packages = []
    description_text = "Native Django SMTP email (always available)"

    def send_email(self, **kwargs) -> bool:
        """Sends email via Django's SMTP."""
        is_valid, error = self.validate()
        if not is_valid:
            self._update_status(MissiveStatus.FAILED, error_message=error)
            return False

        if not self.missive.recipient_email:
            self._update_status(MissiveStatus.FAILED, error_message="Email missing")
            return False

        try:
            from django.conf import settings
            from django.core.mail import send_mail

            self._update_status(MissiveStatus.PROCESSING, provider=self.name)

            send_mail(
                subject=self.missive.subject,
                message=self.missive.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.missive.recipient_email],
                fail_silently=False,
            )

            self._update_status(MissiveStatus.SENT)
            self._create_event("sent", f"Email sent via {self.name}")

            return True

        except Exception as e:
            self._update_status(MissiveStatus.FAILED, error_message=str(e))
            self._create_event("failed", str(e))
            return False

    def validate_webhook_signature(
        self, payload: Dict, headers: Dict
    ) -> Tuple[bool, str]:
        """No webhooks for native Django Email"""
        return False, "Django Email does not support webhooks"

    def get_service_status(self) -> Dict:
        """
        Gets Django SMTP server status.

        Django Email uses the SMTP server configured in settings.py.
        No credits, but SMTP connection can be tested.

        Returns:
            Dict with status, SMTP availability, etc.
        """
        # TODO: Tester la connexion SMTP
        # from django.core.mail import get_connection
        #
        # try:
        #     # Tester la connexion au serveur SMTP
        #     connection = get_connection()
        #     connection.open()
        #     is_available = connection.connection is not None
        #     connection.close()
        #
        #     status = "operational" if is_available else "down"
        #     warnings = [] if is_available else ["Impossible de se connecter au serveur SMTP"]
        #
        #     return {
        #         "status": status,
        #         "is_available": is_available,
        #         "services": self.services,
        #         "credits": {
        #             "type": "unlimited",
        #             "remaining": None,
        #             "currency": "",
        #             "limit": None,
        #             "percentage": None,
        #         },
        #         "rate_limits": {
        #             "per_second": None,  # Dépend du serveur SMTP
        #         },
        #         "sla": {
        #             "uptime_percentage": None,  # Dépend du serveur
        #         },
        #         "last_check": timezone.now(),
        #         "warnings": warnings,
        #         "details": {
        #             "smtp_host": settings.EMAIL_HOST,
        #             "smtp_port": settings.EMAIL_PORT,
        #             "smtp_use_tls": settings.EMAIL_USE_TLS,
        #         }
        #     }
        # except Exception as e:
        #     return {
        #         "status": "down",
        #         "is_available": False,
        #         "warnings": [str(e)]
        #     }

        from django.utils import timezone

        return {
            "status": "unknown",
            "is_available": None,
            "services": self.services,
            "credits": {
                "type": "unlimited",
                "remaining": None,
                "currency": "",
                "limit": None,
                "percentage": None,
            },
            "rate_limits": {
                "per_second": None,
            },
            "sla": {
                "uptime_percentage": None,
            },
            "last_check": timezone.now(),
            "warnings": ["Test SMTP non implémenté - décommenter le code"],
            "details": {
                "provider_type": "Django SMTP",
                "note": "Utilisé les paramètres EMAIL_* de settings.py",
            },
        }
