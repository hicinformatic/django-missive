"""
Provider Brevo (anciennement SendinBlue) pour Email ET SMS.
Exemple parfait de provider multi-types.
"""

from typing import Dict, Optional, Tuple

from ..models import MissiveStatus
from .base import BaseProvider


class BrevoProvider(BaseProvider):
    """
    Provider pour Brevo (anciennement SendinBlue).

    Supporte :
    - Email (transactionnel et marketing)
    - SMS
    """

    name = "Brevo"
    display_name = "Brevo"
    supported_types = ["EMAIL", "SMS"]
    services = [
        "email",
        "email_transactional",
        "email_marketing",
        "sms",
        "contacts",  # Gestion de contacts
        "automation",  # Marketing automation
    ]  # Multi-types !
    config_keys = ["BREVO_API_KEY"]
    required_packages = ["sib-api-v3-sdk"]
    site_url = "https://www.brevo.com/"
    status_url = "https://status.brevo.com/"
    documentation_url = "https://developers.brevo.com/"
    description_text = "Plateforme CRM complète (Email, SMS, Marketing automation)"

    def send_email(self) -> bool:
        """Envoie un email via Brevo API"""
        # Validation
        is_valid, error = self.validate()
        if not is_valid:
            self._update_status(MissiveStatus.FAILED, error_message=error)
            return False

        if not self.missive.recipient_email:
            self._update_status(MissiveStatus.FAILED, error_message="Email manquant")
            return False

        try:
            # TODO: Intégrer avec Brevo
            # import sib_api_v3_sdk
            # from sib_api_v3_sdk.rest import ApiException
            #
            # configuration = sib_api_v3_sdk.Configuration()
            # configuration.api_key['api-key'] = self.config.get('BREVO_API_KEY')
            #
            # api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            #     sib_api_v3_sdk.ApiClient(configuration)
            # )
            #
            # send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            #     to=[{"email": self.missive.recipient_email}],
            #     sender={"email": self.config.get('DEFAULT_FROM_EMAIL')},
            #     subject=self.missive.subject,
            #     text_content=self.missive.body,
            #     tags=[f"missive_{self.missive.id}"]
            # )
            #
            # result = api_instance.send_transac_email(send_smtp_email)
            # external_id = result.message_id

            # Simulation
            external_id = f"brevo_email_{self.missive.id}"

            self._update_status(
                MissiveStatus.SENT, provider=self.name, external_id=external_id
            )
            self._create_event("sent", "Email envoyé via Brevo")

            return True

        except Exception as e:
            self._update_status(MissiveStatus.FAILED, error_message=str(e))
            self._create_event("failed", str(e))
            return False

    def send_sms(self) -> bool:
        """Envoie un SMS via Brevo API"""
        # Validation
        is_valid, error = self.validate()
        if not is_valid:
            self._update_status(MissiveStatus.FAILED, error_message=error)
            return False

        if not self.missive.recipient_phone:
            self._update_status(MissiveStatus.FAILED, error_message="Numéro manquant")
            return False

        try:
            # TODO: Intégrer avec Brevo SMS
            # import sib_api_v3_sdk
            #
            # configuration = sib_api_v3_sdk.Configuration()
            # configuration.api_key['api-key'] = self.config.get('BREVO_API_KEY')
            #
            # api_instance = sib_api_v3_sdk.TransactionalSMSApi(
            #     sib_api_v3_sdk.ApiClient(configuration)
            # )
            #
            # send_transac_sms = sib_api_v3_sdk.SendTransacSms(
            #     sender=self.config.get('BREVO_SMS_SENDER'),
            #     recipient=self.missive.recipient_phone,
            #     content=self.missive.body,
            #     tag=f"missive_{self.missive.id}"
            # )
            #
            # result = api_instance.send_transac_sms(send_transac_sms)
            # external_id = result.reference

            # Simulation
            external_id = f"brevo_sms_{self.missive.id}"

            self._update_status(
                MissiveStatus.SENT, provider=self.name, external_id=external_id
            )
            self._create_event("sent", "SMS envoyé via Brevo")

            return True

        except Exception as e:
            self._update_status(MissiveStatus.FAILED, error_message=str(e))
            self._create_event("failed", str(e))
            return False

    def validate_webhook_signature(
        self, payload: Dict, headers: Dict
    ) -> Tuple[bool, str]:
        """Valide la signature Brevo"""
        # À implémenter selon la documentation Brevo
        return True, ""

    def extract_missive_id(self, payload: Dict) -> Optional[str]:
        """Extrait l'ID depuis Brevo webhook"""
        return payload.get("tag", "").replace("missive_", "")

    def extract_event_type(self, payload: Dict) -> str:
        """Extrait le type d'événement Brevo"""
        return payload.get("event", "unknown")

    def get_service_status(self) -> Dict:
        """
        Récupère le statut et les crédits Brevo.

        Brevo utilise un système de quota d'emails par jour + crédits SMS.

        Returns:
            Dict avec status, crédits email + SMS, etc.
        """
        # TODO: Implémenter l'appel à l'API Brevo
        # import requests
        #
        # try:
        #     api_key = self.config.get("BREVO_API_KEY")
        #     headers = {"api-key": api_key}
        #
        #     # Vérifier le compte
        #     response = requests.get(
        #         "https://api.brevo.com/v3/account",
        #         headers=headers,
        #         timeout=5
        #     )
        #
        #     if response.status_code == 200:
        #         data = response.json()
        #         plan = data.get("plan", [{}])[0]
        #
        #         # Email quota
        #         email_credits = plan.get("credits", 0)
        #         email_limit = plan.get("creditsType", "unlimited")
        #
        #         # SMS credits
        #         sms_credits = data.get("smsCredits", {}).get("remaining", 0)
        #
        #         warnings = []
        #         if email_limit != "unlimited" and email_credits < 1000:
        #             warnings.append(f"Quota email faible: {email_credits}")
        #         if sms_credits < 50:
        #             warnings.append(f"Crédits SMS faibles: {sms_credits}")
        #
        #         return {
        #             "status": "operational",
        #             "is_available": True,
        #             "services": self.services,
        #             "credits": {
        #                 "type": "mixed",  # Email + SMS
        #                 "email": {
        #                     "remaining": email_credits,
        #                     "limit": email_limit,
        #                     "type": "emails_per_day" if email_limit != "unlimited" else "unlimited"
        #                 },
        #                 "sms": {
        #                     "remaining": sms_credits,
        #                     "currency": "sms_units"
        #                 }
        #             },
        #             "rate_limits": {
        #                 "per_second": 10,
        #             },
        #             "sla": {
        #                 "uptime_percentage": 99.95,
        #             },
        #             "last_check": timezone.now(),
        #             "warnings": warnings,
        #             "details": {
        #                 "plan_type": plan.get("type", "unknown"),
        #                 "status_page": "https://status.brevo.com/",
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
                "type": "mixed",  # Email quota + SMS crédits
                "email": {
                    "remaining": None,
                    "limit": "unknown",
                },
                "sms": {
                    "remaining": None,
                    "currency": "sms_units",
                },
            },
            "rate_limits": {
                "per_second": 10,
            },
            "sla": {
                "uptime_percentage": 99.95,
            },
            "last_check": timezone.now(),
            "warnings": ["API Brevo non implémentée - décommenter le code"],
            "details": {
                "status_page": "https://status.brevo.com/",
                "api_docs": "https://developers.brevo.com/reference/getaccount-1",
            },
        }
