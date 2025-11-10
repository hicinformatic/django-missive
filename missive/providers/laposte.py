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
    display_name = "La Poste"
    supported_types = ["POSTAL", "EMAIL", "LRE"]  # Courrier, Email AR, et LRE
    services = [
        "postal",  # Courrier simple
        "postal_registered",  # Recommandé R1
        "postal_signature",  # Recommandé R2/R3 avec signature
        "email_ar",  # Email avec AR électronique
        "colissimo",  # Colis (future extension)
    ]
    config_keys = ["LAPOSTE_API_KEY"]
    required_packages = ["requests"]
    site_url = "https://www.laposte.fr/"
    description_text = (
        "Envoi de courrier recommandé et email AR sur le territoire français"
    )

    def send_postal(self, **kwargs) -> bool:
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

    def get_proofs_of_delivery(self, service_type: Optional[str] = None) -> list:
        """
        Récupère toutes les preuves La Poste.

        La Poste génère plusieurs documents selon le service :
        - Courrier simple : Preuve de dépôt
        - Courrier recommandé R1 : Preuve de dépôt + AR + avis de passage
        - Courrier recommandé R2/R3 : Preuve de dépôt + AR + signature + copie scannée
        - Email AR : Accusé de réception électronique

        TODO: Implémenter via l'API La Poste
        GET https://api.laposte.fr/sls/v2/suivi/{tracking_number}/proofs
        """
        if not self.missive:
            return []

        external_id = self.missive.external_id
        if not external_id or not external_id.startswith("laposte_"):
            return []

        # Déterminer le type de service
        if not service_type:
            if self.missive.missive_type == "EMAIL":
                service_type = "email_ar"
            elif self.missive.requires_signature:
                service_type = "postal_signature"
            elif self.missive.is_registered:
                service_type = "postal_registered"
            else:
                service_type = "postal"

        # TODO: Appel API réel

        # Simulation
        from django.utils import timezone

        sent_at = self.missive.sent_at or timezone.now()
        tracking_number = external_id.replace("laposte_", "")
        proofs = []

        # 1. Preuve de dépôt (toujours disponible)
        proofs.append(
            {
                "type": "deposit_receipt",
                "label": "Preuve de dépôt",
                "available": True,
                "url": f"https://www.laposte.fr/suivi/proof/deposit/{tracking_number}.pdf",
                "generated_at": sent_at,
                "expires_at": None,
                "format": "pdf",
                "metadata": {
                    "proof_type": "deposit",
                    "provider": "laposte",
                    "tracking_number": tracking_number,
                },
            }
        )

        # 2. Copie du document (si courrier postal)
        if "postal" in service_type:
            proofs.append(
                {
                    "type": "document_copy",
                    "label": "Copie du courrier",
                    "available": True,
                    "url": f"https://www.laposte.fr/suivi/document/{tracking_number}.pdf",
                    "generated_at": sent_at,
                    "expires_at": None,
                    "format": "pdf",
                    "metadata": {
                        "document_type": "copy",
                        "provider": "laposte",
                    },
                }
            )

        # 3. Avis de passage (si recommandé et non livré)
        if self.missive.is_registered and not self.missive.delivered_at:
            proofs.append(
                {
                    "type": "delivery_notice",
                    "label": "Avis de passage",
                    "available": False,
                    "url": None,
                    "generated_at": None,
                    "expires_at": None,
                    "format": "pdf",
                    "metadata": {
                        "status": "pending",
                        "message": "Disponible si le destinataire est absent",
                        "provider": "laposte",
                    },
                }
            )

        # 4. AR (si recommandé et livré)
        if self.missive.is_registered:
            if self.missive.delivered_at:
                proofs.append(
                    {
                        "type": "acknowledgment_receipt",
                        "label": "Accusé de réception",
                        "available": True,
                        "url": f"https://www.laposte.fr/suivi/ar/{tracking_number}.pdf",
                        "generated_at": self.missive.delivered_at,
                        "expires_at": None,
                        "format": "pdf",
                        "metadata": {
                            "ar_type": (
                                "R1" if not self.missive.requires_signature else "R2/R3"
                            ),
                            "delivery_date": (
                                self.missive.delivered_at.isoformat()
                                if self.missive.delivered_at
                                else None
                            ),
                            "provider": "laposte",
                        },
                    }
                )
            else:
                proofs.append(
                    {
                        "type": "acknowledgment_receipt",
                        "label": "Accusé de réception",
                        "available": False,
                        "url": None,
                        "generated_at": None,
                        "expires_at": None,
                        "format": "pdf",
                        "metadata": {
                            "status": "pending",
                            "message": "En attente de livraison",
                            "provider": "laposte",
                        },
                    }
                )

        # 5. Signature (si R2/R3 et livré)
        if self.missive.requires_signature and self.missive.delivered_at:
            proofs.append(
                {
                    "type": "signature_proof",
                    "label": "Preuve de signature",
                    "available": True,
                    "url": f"https://www.laposte.fr/suivi/signature/{tracking_number}.pdf",
                    "generated_at": self.missive.delivered_at,
                    "expires_at": None,
                    "format": "pdf",
                    "metadata": {
                        "signature_type": "handwritten",
                        "signer_name": "À récupérer via API",
                        "provider": "laposte",
                    },
                }
            )

        return proofs

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
