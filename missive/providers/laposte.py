"""
Provider La Poste pour courrier postal.
"""

from typing import Dict, Optional, Tuple

from ..models import MissiveStatus
from .base import BaseProvider


class LaPosteProvider(BaseProvider):
    """
    Provider pour La Poste.

    Supporte :
    - Courrier postal (simple, recommandé, avec signature)
    - Email AR (Email avec accusé de réception électronique)
    """

    name = "La Poste"
    supported_types = ["POSTAL", "EMAIL"]  # La Poste peut faire les 2 !
    services = [
        "postal",           # Courrier simple
        "postal_registered",  # Recommandé R1
        "postal_signature",   # Recommandé R2/R3 avec signature
        "email_ar",          # Email avec AR électronique
        "colissimo",         # Colis (future extension)
    ]

    def send_postal(self) -> bool:
        """Envoie du courrier postal via La Poste API"""
        # Validation
        is_valid, error = self.validate()
        if not is_valid:
            self._update_status(MissiveStatus.FAILED, error_message=error)
            return False

        if not self.missive.recipient_address:
            self._update_status(MissiveStatus.FAILED, error_message="Adresse manquante")
            return False

        try:
            # TODO: Intégrer avec La Poste API
            # import requests
            #
            # api_key = self.config.get('LAPOSTE_API_KEY')
            # address_lines = self.missive.recipient_address.split('\n')
            #
            # response = requests.post(
            #     'https://api.laposte.fr/controladresse/v2/send',
            #     headers={'Authorization': f'Bearer {api_key}'},
            #     json={
            #         'sender': self.config.get('LAPOSTE_SENDER_ADDRESS'),
            #         'recipient': {
            #             'name': address_lines[0] if address_lines else '',
            #             'address': '\n'.join(address_lines[1:]),
            #         },
            #         'content': self.missive.body,
            #         'options': {
            #             'registered': self.missive.is_registered,
            #             'signature_required': self.missive.requires_signature,
            #         }
            #     }
            # )
            #
            # result = response.json()
            # external_id = result.get('tracking_number')

            # Simulation
            external_id = f"lp_{self.missive.id}"

            letter_type = "recommandé" if self.missive.is_registered else "simple"
            if self.missive.requires_signature:
                letter_type += " avec signature"

            self._update_status(
                MissiveStatus.SENT, provider=self.name, external_id=external_id
            )
            self._create_event("sent", f"Courrier {letter_type} envoyé via La Poste")

            return True

        except Exception as e:
            self._update_status(MissiveStatus.FAILED, error_message=str(e))
            self._create_event("failed", str(e))
            return False

    def send_email(self) -> bool:
        """
        Envoie un email AR (avec accusé de réception) via La Poste.
        La Poste propose un service d'email recommandé électronique.
        """
        # Validation
        is_valid, error = self.validate()
        if not is_valid:
            self._update_status(MissiveStatus.FAILED, error_message=error)
            return False

        if not self.missive.recipient_email:
            self._update_status(MissiveStatus.FAILED, error_message="Email manquant")
            return False

        try:
            # TODO: Intégrer avec La Poste Email AR
            # import requests
            #
            # api_key = self.config.get('LAPOSTE_API_KEY')
            #
            # response = requests.post(
            #     'https://api.laposte.fr/email-ar/v1/send',
            #     headers={'Authorization': f'Bearer {api_key}'},
            #     json={
            #         'sender': self.config.get('DEFAULT_FROM_EMAIL'),
            #         'recipient': self.missive.recipient_email,
            #         'subject': self.missive.subject,
            #         'body': self.missive.body,
            #         'registered': self.missive.is_registered
            #     }
            # )
            #
            # result = response.json()
            # external_id = result.get('message_id')

            # Simulation
            external_id = f"lp_email_{self.missive.id}"

            self._update_status(
                MissiveStatus.SENT,
                provider=f"{self.name} Email AR",
                external_id=external_id,
            )
            self._create_event("sent", "Email AR envoyé via La Poste")

            return True

        except Exception as e:
            self._update_status(MissiveStatus.FAILED, error_message=str(e))
            self._create_event("failed", str(e))
            return False

    def validate_webhook_signature(
        self, payload: Dict, headers: Dict
    ) -> Tuple[bool, str]:
        """Valide la signature La Poste"""
        # À implémenter selon la documentation La Poste API
        return True, ""

    def extract_missive_id(self, payload: Dict) -> Optional[str]:
        """Extrait l'ID depuis La Poste webhook"""
        return payload.get("reference") or payload.get("tracking_number")

    def extract_event_type(self, payload: Dict) -> str:
        """Extrait le type d'événement La Poste"""
        return payload.get("status", "unknown")

    def get_service_status(self) -> Dict:
        """
        Récupère le statut et les crédits La Poste.
        
        La Poste fonctionne avec des crédits prépayés.
        
        Returns:
            Dict avec status, crédits, etc.
        """
        # TODO: Implémenter l'appel à l'API La Poste
        # import requests
        #
        # try:
        #     api_key = self.config.get("LAPOSTE_API_KEY")
        #     headers = {"X-Okapi-Key": api_key}
        #     
        #     # Vérifier le solde (endpoint hypothétique)
        #     response = requests.get(
        #         "https://api.laposte.fr/suivi/v2/account/balance",
        #         headers=headers,
        #         timeout=5
        #     )
        #
        #     if response.status_code == 200:
        #         data = response.json()
        #         credits_remaining = float(data.get("balance", 0))
        #         
        #         is_operational = credits_remaining > 0
        #         status = "operational" if is_operational else "critical"
        #         
        #         warnings = []
        #         if credits_remaining < 50:
        #             warnings.append(f"Solde critique: {credits_remaining}€")
        #         elif credits_remaining < 200:
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
        #                 "limit": None,
        #                 "percentage": None,
        #             },
        #             "rate_limits": {
        #                 "per_second": 2,
        #                 "per_minute": 120,
        #             },
        #             "sla": {
        #                 "uptime_percentage": 99.9,
        #             },
        #             "last_check": timezone.now(),
        #             "warnings": warnings,
        #             "details": {
        #                 "refill_url": "https://developer.laposte.fr/",
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
                "limit": None,
                "percentage": None,
            },
            "rate_limits": {
                "per_second": 2,
                "per_minute": 120,
            },
            "sla": {
                "uptime_percentage": 99.9,
            },
            "last_check": timezone.now(),
            "warnings": ["API La Poste non implémentée - décommenter le code"],
            "details": {
                "refill_url": "https://developer.laposte.fr/",
                "api_docs": "https://developer.laposte.fr/products",
            },
        }
