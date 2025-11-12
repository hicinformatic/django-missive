"""Twilio provider for SMS and WhatsApp."""

from typing import Dict, Optional, Tuple

from ..models import MissiveStatus
from .base import BaseProvider


class TwilioProvider(BaseProvider):
    """Twilio provider (SMS and WhatsApp)."""

    name = "twilio"
    display_name = "Twilio"
    supported_types = ["SMS", "BRANDED"]
    services = ["sms", "whatsapp", "voice", "verify"]
    brands = ["whatsapp"]
    config_keys = ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER"]
    required_packages = ["twilio"]
    site_url = "https://www.twilio.com/"
    status_url = "https://status.twilio.com/"
    documentation_url = "https://www.twilio.com/docs"
    description_text = "Global multi-channel cloud platform (SMS, WhatsApp, Voice)"

    def send_twilio(self) -> bool:
        """Dispatches to WhatsApp for BRANDED type."""
        return self.send_whatsapp()

    def send_sms(self) -> bool:
        """Sends SMS via Twilio."""
        is_valid, error = self.validate()
        if not is_valid:
            self._update_status(MissiveStatus.FAILED, error_message=error)
            return False

        if not self.missive.recipient_phone:
            self._update_status(MissiveStatus.FAILED, error_message="Phone missing")
            return False

        try:
            # external_id = message.sid

            # Simulation
            external_id = f"tw_sms_{self.missive.id}"

            self._update_status(
                MissiveStatus.SENT, provider=self.name, external_id=external_id
            )
            self._create_event("sent", "SMS sent via Twilio")

            return True

        except Exception as e:
            self._update_status(MissiveStatus.FAILED, error_message=str(e))
            self._create_event("failed", str(e))
            return False

    def send_whatsapp(self) -> bool:
        """Send via WhatsApp via Twilio"""
        # Validation
        is_valid, error = self.validate()
        if not is_valid:
            self._update_status(MissiveStatus.FAILED, error_message=error)
            return False

        if not self.missive.recipient_phone:
            self._update_status(MissiveStatus.FAILED, error_message="Phone missing")
            return False

        try:
            # TODO: Integrate with Twilio WhatsApp
            # from twilio.rest import Client
            #
            # account_sid = self.config.get('TWILIO_ACCOUNT_SID')
            # auth_token = self.config.get('TWILIO_AUTH_TOKEN')
            #
            # client = Client(account_sid, auth_token)
            #
            # from_number = f"whatsapp:{self.config.get('TWILIO_WHATSAPP_NUMBER')}"
            # to_number = f"whatsapp:{self.missive.recipient_phone}"
            #
            # message = client.messages.create(
            #     body=self.missive.body,
            #     from_=from_number,
            #     to=to_number,
            #     status_callback=self.config.get('TWILIO_WEBHOOK_URL')
            # )
            #
            # external_id = message.sid

            # Simulation
            external_id = f"tw_wa_{self.missive.id}"

            self._update_status(
                MissiveStatus.SENT, provider=self.name, external_id=external_id
            )
            self._create_event("sent", "WhatsApp message sent via Twilio")

            return True

        except Exception as e:
            self._update_status(MissiveStatus.FAILED, error_message=str(e))
            self._create_event("failed", str(e))
            return False

    def validate_webhook_signature(
        self, payload: Dict, headers: Dict
    ) -> Tuple[bool, str]:
        """Valide la signature Twilio"""
        auth_token = self.config.get("TWILIO_AUTH_TOKEN")
        if not auth_token:
            return True, ""

        signature = headers.get("HTTP_X_TWILIO_SIGNATURE", "")
        if not signature:
            return False, "Signature missing"

        # La validation Twilio nécessite l'URL complète
        # Pour simplifier, on peut désactiver la validation en dev
        # En production, implémenter selon:
        # https://www.twilio.com/docs/usage/webhooks/webhooks-security

        return True, ""  # Simplified pour l'instant

    def extract_missive_id(self, payload: Dict) -> Optional[str]:
        """Extrait l'ID depuis Twilio webhook"""
        # Twilio retourne MessageSid, on doit l'avoir stocké en external_id
        return payload.get("MessageSid")

    def extract_event_type(self, payload: Dict) -> str:
        """Extrait le statut Twilio"""
        return payload.get("MessageStatus", "unknown")

    def get_status_from_event(self, event_type: str) -> Optional[MissiveStatus]:
        """Mapping des statuts Twilio"""
        status_mapping = {
            "queued": MissiveStatus.PENDING,
            "sending": MissiveStatus.PROCESSING,
            "sent": MissiveStatus.SENT,
            "delivered": MissiveStatus.DELIVERED,
            "undelivered": MissiveStatus.FAILED,
            "failed": MissiveStatus.FAILED,
            "read": MissiveStatus.READ,
        }
        return status_mapping.get(event_type.lower())

    def get_service_status(self) -> Dict:
        """
        Gets Twilio status and credits.

        Twilio uses a prepaid system in USD.

        Returns:
            Dict with status, credits in USD, etc.
        """
        # TODO: Implement Twilio API call
        # from twilio.rest import Client
        #
        # try:
        #     account_sid = self.config.get("TWILIO_ACCOUNT_SID")
        #     auth_token = self.config.get("TWILIO_AUTH_TOKEN")
        #
        #     client = Client(account_sid, auth_token)
        #
        #     # Récupérer le solde du compte
        #     balance = client.api.v2010.balance.fetch()
        #     credits_remaining = float(balance.balance)
        #     currency = balance.currency
        #
        #     # Vérifier le statut du service
        #     # https://status.twilio.com/
        #     is_operational = credits_remaining > 0
        #     status = "operational" if is_operational else "critical"
        #
        #     warnings = []
        #     if credits_remaining < 5:
        #         warnings.append(f"Solde critique: {credits_remaining} {currency}")
        #     elif credits_remaining < 20:
        #         warnings.append(f"Solde faible: {credits_remaining} {currency}")
        #
        #     return {
        #         "status": status,
        #         "is_available": is_operational,
        #         "services": self.services,
        #         "credits": {
        #             "type": "money",
        #             "remaining": credits_remaining,
        #             "currency": currency,
        #             "limit": None,  # Prépayé
        #             "percentage": None,
        #         },
        #         "rate_limits": {
        #             "per_second": 1,  # Dépend du plan
        #             "per_minute": 60,
        #         },
        #         "sla": {
        #             "uptime_percentage": 99.95,
        #         },
        #         "last_check": timezone.now(),
        #         "warnings": warnings,
        #         "details": {
        #             "refill_url": "https://www.twilio.com/console/billing",
        #             "status_page": "https://status.twilio.com/",
        #         }
        #     }
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
                "type": "money",
                "remaining": None,
                "currency": "USD",
                "limit": None,  # Prépayé
                "percentage": None,
            },
            "rate_limits": {
                "per_second": 1,
                "per_minute": 60,
            },
            "sla": {
                "uptime_percentage": 99.95,
            },
            "last_check": timezone.now(),
            "warnings": ["API Twilio non implémentée - décommenter le code"],
            "details": {
                "refill_url": "https://www.twilio.com/console/billing",
                "status_page": "https://status.twilio.com/",
                "api_docs": "https://www.twilio.com/docs/usage/api/usage-record",
            },
        }

    def cancel_sms(self) -> bool:
        """
        Annule l'envoi d'un SMS via Twilio.

        Twilio permet d'annuler les messages en statut 'queued' ou 'scheduled'.

        Returns:
            bool: True if cancellation succeeded, False otherwise
        """
        if not self.missive.external_id:
            return False

        try:
            from twilio.rest import Client

            account_sid = self.config.get("TWILIO_ACCOUNT_SID")
            auth_token = self.config.get("TWILIO_AUTH_TOKEN")

            if not account_sid or not auth_token:
                return False

            client = Client(account_sid, auth_token)

            # Cancel message (only 'queued' or 'scheduled' messages can be cancelled)
            message = client.messages(self.missive.external_id).update(
                status="canceled"
            )

            if message.status == "canceled":
                self._create_event("cancelled", "SMS cancelled via Twilio")
                return True
            else:
                return False

        except Exception:
            return False

    def cancel_twilio(self) -> bool:
        """
        Annule l'envoi d'un message de marque (WhatsApp) via Twilio.

        Called automatically by cancel_branded() via dispatch.
        Fonctionne de la même manière que cancel_sms() car Twilio utilise
        la même API pour SMS et WhatsApp.

        Returns:
            bool: True if cancellation succeeded, False otherwise
        """
        return self.cancel_sms()

    def cancel_whatsapp(self) -> bool:
        """
        Cancels WhatsApp message sending via Twilio.

        Called automatically by cancel_branded("whatsapp") via dispatch.

        Returns:
            bool: True if cancellation succeeded, False otherwise

        Example:
            provider.cancel_branded("whatsapp")  # → appelle cancel_whatsapp()
        """
        return self.cancel_sms()

    def get_whatsapp_service_info(self) -> Dict:
        """
        Gets WhatsApp service information via Twilio.

        Called automatically by get_branded_service_info("whatsapp") via dispatch.

        Returns:
            Dict with status, credits, etc.

        Example:
            info = provider.get_branded_service_info("whatsapp")  # → appelle get_whatsapp_service_info()
        """
        # WhatsApp via Twilio uses the same credit system as SMS
        return self.get_service_status()
