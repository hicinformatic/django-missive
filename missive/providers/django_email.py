"""
Provider Django Email (SMTP natif de Django).
"""

from typing import Dict, Tuple

from ..models import MissiveStatus
from .base import BaseProvider


class DjangoEmailProvider(BaseProvider):
    """Provider utilisant le système d'email de Django (SMTP)"""

    name = "Django Email"
    display_name = "Django Email (par défaut)"
    supported_types = ["EMAIL"]
    services = ["email"]  # Email via SMTP configuré dans Django
    config_keys = ["EMAIL_HOST", "EMAIL_PORT", "EMAIL_HOST_USER", "EMAIL_HOST_PASSWORD"]
    required_package = None  # Toujours disponible avec Django

    def send_email(self) -> bool:
        """Envoie via Django mail (SMTP)"""
        # Validation
        is_valid, error = self.validate()
        if not is_valid:
            self._update_status(MissiveStatus.FAILED, error_message=error)
            return False

        if not self.missive.recipient_email:
            self._update_status(MissiveStatus.FAILED, error_message="Email manquant")
            return False

        try:
            from django.conf import settings
            from django.core.mail import send_mail

            # Marquer comme en traitement
            self._update_status(MissiveStatus.PROCESSING, provider=self.name)

            # Envoyer l'email
            send_mail(
                subject=self.missive.subject,
                message=self.missive.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.missive.recipient_email],
                fail_silently=False,
            )

            # Succès
            self._update_status(MissiveStatus.SENT)
            self._create_event("sent", f"Email envoyé via {self.name}")

            return True

        except Exception as e:
            self._update_status(MissiveStatus.FAILED, error_message=str(e))
            self._create_event("failed", str(e))
            return False

    def validate_webhook_signature(
        self, payload: Dict, headers: Dict
    ) -> Tuple[bool, str]:
        """Pas de webhooks pour Django Email natif"""
        return False, "Django Email ne supporte pas les webhooks"

    def get_service_status(self) -> Dict:
        """
        Récupère le statut du serveur SMTP Django.
        
        Django Email utilise le serveur SMTP configuré dans settings.py.
        Pas de crédits, mais on peut tester la connexion SMTP.
        
        Returns:
            Dict avec status, disponibilité SMTP, etc.
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
