"""Vonage provider for SMS and Voice."""

from typing import Dict

from ..models import MissiveStatus
from .base import BaseProvider


class VonageProvider(BaseProvider):
    """
    Vonage (ex-Nexmo) provider.

    Required configuration:
        VONAGE_API_KEY: Vonage API key
        VONAGE_API_SECRET: Secret API Vonage
        VONAGE_FROM_NUMBER: Sender number

    Supports:
    - SMS
    - Voice (voice calls)
    - Verify (vérification 2FA)
    """

    name = "vonage"
    display_name = "Vonage"
    supported_types = ["SMS", "VOICE_CALL"]
    services = ["sms", "voice", "verify", "number_insight"]
    config_keys = ["VONAGE_API_KEY", "VONAGE_API_SECRET", "VONAGE_FROM_NUMBER"]
    required_packages = ["vonage"]
    site_url = "https://www.vonage.com/"
    status_url = "https://vonage.statuspage.io/"
    documentation_url = "https://developer.vonage.com/"
    description_text = "Global SMS and Voice platform (formerly Nexmo)"

    def send_sms(self, **kwargs) -> bool:
        """Send an SMS via Vonage API"""
        from vonage import Client, Sms

        # Validation
        is_valid, error = self.validate()
        if not is_valid:
            self._update_status(MissiveStatus.FAILED, error_message=error)
            return False

        if not self.missive.recipient_phone:
            self._update_status(MissiveStatus.FAILED, error_message="Phone missing")
            return False

        try:
            api_key = self.config.get("VONAGE_API_KEY")
            api_secret = self.config.get("VONAGE_API_SECRET")
            from_number = self.config.get("VONAGE_FROM_NUMBER")

            if not all([api_key, api_secret, from_number]):
                self._update_status(
                    MissiveStatus.FAILED,
                    error_message="Configuration Vonage incomplète",
                )
                return False

            # Créer le client Vonage
            client = Client(key=api_key, secret=api_secret)
            sms = Sms(client)

            # Prepare message with default values
            message_params = {
                "from": kwargs.get("sender", from_number),  # Standardisé: sender
                "to": self.missive.recipient_phone,
                "text": self.missive.body_text or self.missive.body,
            }

            # Ajouter client-ref (tag)
            if "tag" in kwargs:
                message_params["client-ref"] = kwargs["tag"]
            elif self.missive.id:
                message_params["client-ref"] = f"missive_{self.missive.id}"

            # Mapping des kwargs standardisés Django → API Vonage
            kwargs_mapping = {
                "is_unicode": "type",  # True → "unicode", False → "text"
                "webhook_url": "callback",  # URL de callback DLR
                "ttl": "ttl",  # Time to live (peut rester identique)
                "priority": "message-class",  # Priorité du message
            }

            # Appliquer le mapping
            for django_key, api_key in kwargs_mapping.items():
                if django_key in kwargs:
                    value = kwargs[django_key]
                    # Conversions spéciales
                    if django_key == "is_unicode":
                        # Convertir bool → "unicode" ou "text"
                        message_params[api_key] = "unicode" if value else "text"
                    elif django_key == "priority":
                        # Convertir priority en message-class Vonage (0-3)
                        priority_map = {"low": 0, "normal": 1, "high": 2}
                        message_params[api_key] = priority_map.get(value, 1)
                    else:
                        message_params[api_key] = value

            # Request DLR by default
            if "status-report-req" not in message_params:
                message_params["status-report-req"] = 1

            # Send the SMS
            response = sms.send_message(message_params)

            # Vérifier le statut
            if response["messages"][0]["status"] == "0":
                # Succès
                message_id = response["messages"][0]["message-id"]
                message_price = response["messages"][0].get("message-price", "0")
                network = response["messages"][0].get("network", "N/A")

                self._update_status(
                    MissiveStatus.SENT,
                    provider=self.name,
                    external_id=message_id,
                )
                self._create_event(
                    "sent",
                    f"SMS sent via Vonage (ID: {message_id}, Price: {message_price}, Network: {network})",
                )

                return True
            else:
                # Erreur
                error_code = response["messages"][0]["status"]
                error_text = response["messages"][0].get(
                    "error-text", "Erreur inconnue"
                )

                self._update_status(
                    MissiveStatus.FAILED,
                    error_message=f"Vonage error {error_code}: {error_text}",
                )
                self._create_event("failed", f"Erreur {error_code}: {error_text}")
                return False

        except Exception as e:
            self._update_status(MissiveStatus.FAILED, error_message=str(e))
            self._create_event("failed", str(e))
            return False

    def get_sms_service_info(self) -> Dict:
        """
        Gets Vonage service information.

        Returns:
            Dict with balance, limits, etc.
        """
        from vonage import Client

        try:
            api_key = self.config.get("VONAGE_API_KEY")
            api_secret = self.config.get("VONAGE_API_SECRET")

            if not all([api_key, api_secret]):
                return {
                    "credits": None,
                    "credits_type": "amount",
                    "is_available": False,
                    "limits": {},
                    "warnings": ["Configuration Vonage incomplète"],
                    "details": {},
                }

            # Créer le client
            client = Client(key=api_key, secret=api_secret)

            # Récupérer le solde
            balance = client.get_balance()
            balance_value = float(balance.get("value", 0))
            currency = "EUR"

            # Warnings
            warnings = []
            if balance_value < 5:
                warnings.append(f"⚠️ Solde critique: {balance_value:.2f}{currency}")
            elif balance_value < 20:
                warnings.append(f"⚠️ Solde faible: {balance_value:.2f}{currency}")

            return {
                "credits": f"{balance_value:.2f}{currency}",
                "credits_type": "amount",
                "is_available": balance_value > 0,
                "limits": {
                    "auto_reload": balance.get("autoReload", False),
                },
                "warnings": warnings,
                "details": {
                    "currency": currency,
                    "balance": balance_value,
                },
            }

        except Exception as e:
            return {
                "credits": None,
                "credits_type": "amount",
                "is_available": False,
                "limits": {},
                "warnings": [f"Erreur: {str(e)}"],
                "details": {},
            }
