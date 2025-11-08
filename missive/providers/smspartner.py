"""
Provider SMSPartner pour SMS (provider français).
"""

from typing import Dict, Optional, Tuple

from ..models import MissiveStatus
from .base import BaseProvider


class SMSPartnerProvider(BaseProvider):
    """Provider pour SMSPartner (SMS uniquement)"""

    name = "SMS Partner"
    supported_types = ["SMS"]
    services = ["sms", "sms_low_cost", "sms_premium"]

    def send_sms(self) -> bool:
        """Envoie un SMS via SMSPartner API"""
        # Validation
        is_valid, error = self.validate()
        if not is_valid:
            self._update_status(MissiveStatus.FAILED, error_message=error)
            return False

        if not self.missive.recipient_phone:
            self._update_status(MissiveStatus.FAILED, error_message="Numéro manquant")
            return False

        try:
            # TODO: Intégrer avec SMSPartner
            # import requests
            #
            # api_key = self.config.get('SMSPARTNER_API_KEY')
            #
            # response = requests.post(
            #     'https://api.smspartner.fr/v1/send',
            #     json={
            #         'apiKey': api_key,
            #         'phoneNumbers': self.missive.recipient_phone,
            #         'message': self.missive.body,
            #         'sender': self.config.get('SMSPARTNER_SENDER'),
            #         'tag': f'missive_{self.missive.id}'
            #     }
            # )
            #
            # result = response.json()
            # external_id = result.get('messageId')

            # Simulation
            external_id = f"sp_{self.missive.id}"

            self._update_status(
                MissiveStatus.SENT, provider=self.name, external_id=external_id
            )
            self._create_event("sent", "SMS envoyé via SMSPartner")

            return True

        except Exception as e:
            self._update_status(MissiveStatus.FAILED, error_message=str(e))
            self._create_event("failed", str(e))
            return False

    def validate_webhook_signature(
        self, payload: Dict, headers: Dict
    ) -> Tuple[bool, str]:
        """Valide la signature SMSPartner"""
        # À implémenter selon la doc SMSPartner
        return True, ""

    def extract_missive_id(self, payload: Dict) -> Optional[str]:
        """Extrait l'ID depuis SMSPartner webhook"""
        return payload.get("messageId") or payload.get("tag", "").replace(
            "missive_", ""
        )

    def extract_event_type(self, payload: Dict) -> str:
        """Extrait le type d'événement SMSPartner"""
        return payload.get("status", "unknown")

    def get_service_status(self) -> Dict:
        """
        Récupère le statut et les crédits SMSPartner.
        
        SMSPartner fonctionne avec un système de prépaiement en euros.
        
        Returns:
            Dict avec status, crédits en euros, etc.
        """
        # TODO: Implémenter l'appel à l'API SMSPartner
        # import requests
        #
        # try:
        #     api_key = self.config.get("SMSPARTNER_API_KEY")
        #     
        #     # Vérifier le solde du compte
        #     response = requests.get(
        #         "https://api.smspartner.fr/v1/me",
        #         params={"apiKey": api_key},
        #         timeout=5
        #     )
        #
        #     if response.status_code == 200:
        #         data = response.json()
        #         credits_remaining = float(data.get("credit", 0))
        #         
        #         # Déterminer le statut
        #         is_operational = credits_remaining > 0
        #         status = "operational" if is_operational else "critical"
        #         
        #         # Avertissements
        #         warnings = []
        #         if credits_remaining < 10:
        #             warnings.append(f"Solde critique: {credits_remaining}€")
        #         elif credits_remaining < 50:
        #             warnings.append(f"Solde faible: {credits_remaining}€")
        #
        #         return {
        #             "status": status,
        #             "is_available": is_operational,
        #             "services": self.services,
        #             "credits": {
        #                 "type": "money",
        #                 "remaining": credits_remaining,
        #                 "currency": "EUR",
        #                 "limit": None,  # Pas de limite, prépayé
        #                 "percentage": None,
        #             },
        #             "rate_limits": {
        #                 "per_second": 5,
        #                 "per_minute": 300,
        #             },
        #             "sla": {
        #                 "uptime_percentage": 99.9,
        #             },
        #             "last_check": timezone.now(),
        #             "warnings": warnings,
        #             "details": {
        #                 "account_type": data.get("accountType", "unknown"),
        #                 "refill_url": "https://www.smspartner.fr/recharge",
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
                "type": "money",
                "remaining": None,
                "currency": "EUR",
                "limit": None,  # Prépayé
                "percentage": None,
            },
            "rate_limits": {
                "per_second": 5,
                "per_minute": 300,
            },
            "sla": {
                "uptime_percentage": 99.9,
            },
            "last_check": timezone.now(),
            "warnings": ["API SMSPartner non implémentée - décommenter le code"],
            "details": {
                "refill_url": "https://www.smspartner.fr/recharge",
                "api_docs": "https://www.smspartner.fr/api-sms/documentation-api/",
            },
        }
