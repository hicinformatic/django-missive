"""
Provider SendGrid pour emails.
"""

import base64
import hashlib
import hmac
import json
from typing import Dict, Optional, Tuple

from ..models import MissiveStatus
from .base import BaseProvider


class SendGridProvider(BaseProvider):
    """Provider pour SendGrid (Email uniquement)"""

    name = "SendGrid"
    display_name = "SendGrid"
    supported_types = ["EMAIL"]
    services = ["email", "email_transactional", "email_marketing"]
    config_keys = ["SENDGRID_API_KEY"]
    required_package = "sendgrid"

    def send_email(self) -> bool:
        """Envoie un email via SendGrid API"""
        # Validation
        is_valid, error = self.validate()
        if not is_valid:
            self._update_status(MissiveStatus.FAILED, error_message=error)
            return False

        if not self.missive.recipient_email:
            self._update_status(MissiveStatus.FAILED, error_message="Email manquant")
            return False

        try:
            # TODO: Intégrer avec SendGrid
            # from sendgrid import SendGridAPIClient
            # from sendgrid.helpers.mail import Mail
            #
            # api_key = self.config.get('SENDGRID_API_KEY')
            # sg = SendGridAPIClient(api_key)
            #
            # message = Mail(
            #     from_email=self.config.get('DEFAULT_FROM_EMAIL'),
            #     to_emails=recipient_email,
            #     subject=self.missive.subject,
            #     plain_text_content=self.missive.body
            # )
            #
            # # Ajouter custom_args pour le webhook
            # message.custom_arg = {
            #     'missive_id': str(self.missive.id),
            # }
            #
            # response = sg.send(message)
            # external_id = response.headers.get('X-Message-Id')

            # Simulation
            external_id = f"sg_{self.missive.id}"

            self._update_status(
                MissiveStatus.SENT, provider=self.name, external_id=external_id
            )
            self._create_event("sent", "Email envoyé via SendGrid")

            return True

        except Exception as e:
            self._update_status(MissiveStatus.FAILED, error_message=str(e))
            self._create_event("failed", str(e))
            return False

    def validate_webhook_signature(
        self, payload: Dict, headers: Dict
    ) -> Tuple[bool, str]:
        """Valide la signature SendGrid"""
        webhook_key = self.config.get("SENDGRID_WEBHOOK_KEY")
        if not webhook_key:
            return True, ""  # Pas de validation

        signature = headers.get("HTTP_X_TWILIO_EMAIL_EVENT_WEBHOOK_SIGNATURE", "")
        timestamp = headers.get("HTTP_X_TWILIO_EMAIL_EVENT_WEBHOOK_TIMESTAMP", "")

        if not signature or not timestamp:
            return False, "Signature ou timestamp manquant"

        # Reconstruire la signature
        payload_str = json.dumps(payload, separators=(",", ":"))
        signed_payload = timestamp + payload_str

        expected_signature = base64.b64encode(
            hmac.new(
                webhook_key.encode(), signed_payload.encode(), hashlib.sha256
            ).digest()
        ).decode()

        if hmac.compare_digest(signature, expected_signature):
            return True, ""
        return False, "Signature ne correspond pas"

    def extract_missive_id(self, payload: Dict) -> Optional[str]:
        """Extrait l'ID depuis SendGrid webhook"""
        # SendGrid envoie un array d'événements
        if isinstance(payload, list) and len(payload) > 0:
            event = payload[0]
            return event.get("missive_id") or event.get("custom_args", {}).get(
                "missive_id"
            )
        elif isinstance(payload, dict):
            return payload.get("missive_id") or payload.get("custom_args", {}).get(
                "missive_id"
            )
        return None

    def extract_event_type(self, payload: Dict) -> str:
        """Extrait le type d'événement SendGrid"""
        if isinstance(payload, list) and len(payload) > 0:
            return payload[0].get("event", "unknown")
        elif isinstance(payload, dict):
            return payload.get("event", "unknown")
        return "unknown"

    def get_service_status(self) -> Dict:
        """
        Récupère le statut et les crédits SendGrid.

        Returns:
            Dict avec status, crédits, etc.
        """
        # TODO: Implémenter l'appel à l'API SendGrid
        # import requests
        #
        # try:
        #     api_key = self.config.get("SENDGRID_API_KEY")
        #     headers = {"Authorization": f"Bearer {api_key}"}
        #
        #     # Vérifier les crédits
        #     response = requests.get(
        #         "https://api.sendgrid.com/v3/user/credits",
        #         headers=headers,
        #         timeout=5
        #     )
        #
        #     if response.status_code == 200:
        #         data = response.json()
        #         credits_remaining = data.get("total", 0)
        #         credits_limit = data.get("overage", 0)
        #
        #         # Statut général depuis status page
        #         status_response = requests.get(
        #             "https://status.sendgrid.com/api/v2/status.json",
        #             timeout=5
        #         )
        #         status_data = status_response.json()
        #         is_operational = status_data.get("status", {}).get("indicator") == "none"
        #
        #         return {
        #             "status": "operational" if is_operational else "degraded",
        #             "is_available": is_operational,
        #             "services": self.services,
        #             "credits": {
        #                 "type": "emails",
        #                 "remaining": credits_remaining,
        #                 "currency": "emails",
        #                 "limit": credits_limit,
        #                 "percentage": (credits_remaining / credits_limit * 100) if credits_limit else None
        #             },
        #             "rate_limits": {
        #                 "per_second": 10,  # Dépend du plan
        #                 "per_minute": 600,
        #             },
        #             "sla": {
        #                 "uptime_percentage": 99.99,
        #                 "response_time_ms": 100,
        #             },
        #             "last_check": timezone.now(),
        #             "warnings": [],
        #             "details": {"plan": data.get("plan", "unknown")}
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
                "per_second": 10,  # Dépend du plan SendGrid
                "per_minute": 600,
            },
            "sla": {
                "uptime_percentage": 99.99,  # SLA SendGrid
                "response_time_ms": 100,
            },
            "last_check": timezone.now(),
            "warnings": ["API SendGrid non implémentée - décommenter le code"],
            "details": {
                "status_page": "https://status.sendgrid.com/",
                "api_docs": "https://docs.sendgrid.com/api-reference/stats/retrieve-email-statistics",
            },
        }
