"""
Provider Mailgun pour emails.
"""

import hashlib
import hmac
from typing import Dict, Optional, Tuple

from ..models import MissiveStatus
from .base import BaseProvider


class MailgunProvider(BaseProvider):
    """Provider pour Mailgun (Email uniquement)"""

    name = "Mailgun"
    display_name = "Mailgun"
    supported_types = ["EMAIL"]
    services = ["email", "email_validation", "email_routing"]
    config_keys = ["MAILGUN_API_KEY", "MAILGUN_DOMAIN"]
    required_packages = ["mailgun"]
    site_url = "https://www.mailgun.com/"
    status_url = "https://status.mailgun.com/"
    documentation_url = "https://documentation.mailgun.com/"
    description_text = "Service email transactionnel avec validation et routage avancés"

    def send_email(self, **kwargs) -> bool:
        """Envoie via Mailgun API"""
        # Validation
        is_valid, error = self.validate()
        if not is_valid:
            self._update_status(MissiveStatus.FAILED, error_message=error)
            return False

        if not self.missive.recipient_email:
            self._update_status(MissiveStatus.FAILED, error_message="Email manquant")
            return False

        try:
            # TODO: Intégrer avec Mailgun
            # import requests
            #
            # api_key = self.config.get('MAILGUN_API_KEY')
            # domain = self.config.get('MAILGUN_DOMAIN')
            #
            # response = requests.post(
            #     f"https://api.mailgun.net/v3/{domain}/messages",
            #     auth=("api", api_key),
            #     data={
            #         "from": self.config.get('DEFAULT_FROM_EMAIL'),
            #         "to": self.missive.recipient_email,
            #         "subject": self.missive.subject,
            #         "text": self.missive.body,
            #         "v:missive_id": str(self.missive.id)
            #     }
            # )
            #
            # external_id = response.json().get('id')

            # Simulation
            external_id = f"mg_{self.missive.id}"

            self._update_status(
                MissiveStatus.SENT, provider=self.name, external_id=external_id
            )
            self._create_event("sent", "Email envoyé via Mailgun")

            return True

        except Exception as e:
            self._update_status(MissiveStatus.FAILED, error_message=str(e))
            self._create_event("failed", str(e))
            return False

    def validate_webhook_signature(
        self, payload: Dict, headers: Dict
    ) -> Tuple[bool, str]:
        """Valide la signature Mailgun"""
        api_key = self.config.get("MAILGUN_API_KEY")
        if not api_key:
            return True, ""

        signature_data = payload.get("signature", {})
        timestamp = signature_data.get("timestamp", "")
        token = signature_data.get("token", "")
        signature = signature_data.get("signature", "")

        expected_signature = hmac.new(
            api_key.encode(), f"{timestamp}{token}".encode(), hashlib.sha256
        ).hexdigest()

        if hmac.compare_digest(signature, expected_signature):
            return True, ""
        return False, "Signature ne correspond pas"

    def extract_missive_id(self, payload: Dict) -> Optional[str]:
        """Extrait l'ID depuis Mailgun webhook"""
        event_data = payload.get("event-data", {})
        user_variables = event_data.get("user-variables", {})
        return user_variables.get("missive_id")

    def extract_event_type(self, payload: Dict) -> str:
        """Extrait le type d'événement Mailgun"""
        event_data = payload.get("event-data", {})
        return event_data.get("event", "unknown")

    def get_service_status(self) -> Dict:
        """
        Récupère le statut et les crédits Mailgun.

        Mailgun facture par email envoyé.

        Returns:
            Dict avec status, crédits, etc.
        """
        # TODO: Implémenter l'appel à l'API Mailgun
        # import requests
        #
        # try:
        #     api_key = self.config.get("MAILGUN_API_KEY")
        #     domain = self.config.get("MAILGUN_DOMAIN")
        #
        #     # Vérifier les stats du compte
        #     response = requests.get(
        #         f"https://api.mailgun.net/v3/{domain}/stats/total",
        #         auth=("api", api_key),
        #         params={"event": "delivered", "duration": "1m"},
        #         timeout=5
        #     )
        #
        #     if response.status_code == 200:
        #         data = response.json()
        #
        #         # Mailgun a des quotas par plan
        #         # À ajuster selon le plan de l'utilisateur
        #
        #         return {
        #             "status": "operational",
        #             "is_available": True,
        #             "services": self.services,
        #             "credits": {
        #                 "type": "emails",
        #                 "remaining": None,  # Dépend du plan
        #                 "currency": "emails",
        #                 "limit": None,
        #                 "percentage": None,
        #             },
        #             "rate_limits": {
        #                 "per_second": 100,  # Dépend du plan
        #                 "per_minute": 6000,
        #             },
        #             "sla": {
        #                 "uptime_percentage": 99.99,
        #             },
        #             "last_check": timezone.now(),
        #             "warnings": [],
        #             "details": {
        #                 "domain": domain,
        #                 "status_page": "https://status.mailgun.com/",
        #             }
        #         }
        # except Exception as e:
        #     return {
        #         "status": "unknown",
        #         "warnings": [str(e)]
        #     }

        from django.utils import timezone

        return {
            "status": "unknown",
            "is_available": None,
            "services": self.services,
            "credits": {
                "type": "emails",
                "remaining": None,
                "currency": "emails",
                "limit": None,
                "percentage": None,
            },
            "rate_limits": {
                "per_second": 100,
                "per_minute": 6000,
            },
            "sla": {
                "uptime_percentage": 99.99,
            },
            "last_check": timezone.now(),
            "warnings": ["API Mailgun non implémentée - décommenter le code"],
            "details": {
                "status_page": "https://status.mailgun.com/",
                "api_docs": "https://documentation.mailgun.com/en/latest/api-stats.html",
            },
        }
