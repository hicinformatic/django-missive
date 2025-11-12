"""AR24 provider for electronic registered letters (LRE)."""

from typing import Any, Dict, Optional

from .base import BaseProvider


class AR24Provider(BaseProvider):
    """
    AR24 provider (Electronic Registered Letter).

    Required configuration:
        AR24_API_TOKEN: AR24 API token
        AR24_API_URL: API URL (production or sandbox)
        AR24_SENDER_ID: Registered sender ID on AR24

    Recipient must have an email and ideally a complete postal address.
    """

    name = "ar24"
    display_name = "AR24 (LRE)"
    supported_types = ["LRE"]
    config_keys = ["AR24_API_TOKEN", "AR24_API_URL", "AR24_SENDER_ID"]
    required_packages = ["requests"]
    site_url = "https://www.ar24.fr/"
    description_text = "Electronic registered email (LRE) with legal value"

    def validate(self) -> Dict[str, Any]:
        """Validate that the recipient has an email and address"""
        if not self.missive:
            return {"is_valid": False, "error": "Missive not defined"}

        recipient = self.missive.recipient
        if not recipient or not recipient.email:
            return {
                "is_valid": False,
                "error": "Recipient must have an email for AR24 ERL",
            }

        # Vérifier l'adresse postale (recommandé mais pas obligatoire)
        warnings = []
        if not recipient.address_line1:
            warnings.append("Postal address missing (recommended for AR24)")
        if not recipient.postal_code or not recipient.city:
            warnings.append("Postal code and city missing")

        return {"is_valid": True, "warnings": warnings}

    def send(self) -> Dict[str, Any]:
        """
        Send an LRE via AR24.

        TODO: Implement actual sending via:
        POST https://api.ar24.fr/api/v2/mail/send
        """
        validation = self.validate()
        if not validation["is_valid"]:
            self._update_status("FAILED", error_message=validation["error"])
            return {"success": False, "error": validation["error"]}

        # TODO: Implement actual sending
        # 1. Generate the mail PDF
        # 2. Prepare the AR24 payload with recipient(s)
        # 3. POST to /api/v2/mail/send
        # 4. Récupérer l'ID de suivi et le certificat de dépôt

        self._update_status(
            "SENT",
            external_id=f"ar24_sim_{self.missive.id}",
        )

        return {
            "success": True,
            "tracking_id": f"ar24_sim_{self.missive.id}",
            "deposit_certificate_url": f"https://www.ar24.fr/certificate/sim_{self.missive.id}",
        }

    def check_status(self, external_id: Optional[str] = None) -> Optional[str]:
        """
        Check the LRE status (deposit, sending, reception, reading).

        TODO: Implement via:
        GET https://api.ar24.fr/api/v2/mail/{mail_id}/status
        """
        return None

    def get_proofs_of_delivery(self, service_type: Optional[str] = None) -> list:
        """
        Get all AR24 proofs.

        AR24 generates several documents:
        1. Deposit certificate (immediate)
        2. Copy of sent document
        3. Acknowledgement of receipt (when recipient reads)
        4. Refusal certificate (if not claimed after 15 days)

        TODO: Implement via:
        GET https://api.ar24.fr/api/v2/mail/{mail_id}/proofs
        """
        if not self.missive:
            return []

        external_id = self.missive.external_id
        if not external_id or not external_id.startswith("ar24_"):
            return []

        # TODO: Appel API réel
        # try:
        #     api_token = self.config.get('AR24_API_TOKEN')
        #     headers = {'Authorization': f'Bearer {api_token}'}
        #
        #     response = requests.get(
        #         f'https://api.ar24.fr/api/v2/mail/{external_id}/proofs',
        #         headers=headers,
        #         timeout=10
        #     )
        #
        #     if response.status_code == 200:
        #         data = response.json()
        #         proofs_list = []
        #
        #         # Deposit certificate (always available)
        #         if data.get('deposit_certificate'):
        #             proofs_list.append({...})
        #
        #         # Document copy
        #         if data.get('document_copy'):
        #             proofs_list.append({...})
        #
        #         # AR (si lu)
        #         if data.get('acknowledgment_receipt'):
        #             proofs_list.append({...})
        #
        #         return proofs_list
        # except Exception as e:
        #     return []

        # Simulation
        from django.utils import timezone

        sent_at = self.missive.sent_at or timezone.now()
        proofs = []

        # 1. Deposit certificate (always available from sending)
        proofs.append(
            {
                "type": "deposit_certificate",
                "label": "Deposit Certificate",
                "available": True,
                "url": f"https://www.ar24.fr/certificate/deposit/{external_id}.pdf",
                "generated_at": sent_at,
                "expires_at": None,
                "format": "pdf",
                "metadata": {
                    "certificate_type": "deposit",
                    "legal_value": "Valeur probante",
                    "provider": "ar24",
                },
            }
        )

        # 2. Copy of sent document
        proofs.append(
            {
                "type": "sent_document",
                "label": "Sent Document",
                "available": True,
                "url": f"https://www.ar24.fr/mail/{external_id}/document.pdf",
                "generated_at": sent_at,
                "expires_at": None,
                "format": "pdf",
                "metadata": {
                    "document_type": "sent_copy",
                    "provider": "ar24",
                },
            }
        )

        # 3. AR électronique (si déjà lu)
        if self.missive.read_at:
            proofs.append(
                {
                    "type": "acknowledgment_receipt",
                    "label": "Acknowledgement of Receipt",
                    "available": True,
                    "url": f"https://www.ar24.fr/certificate/ar/{external_id}.pdf",
                    "generated_at": self.missive.read_at,
                    "expires_at": None,
                    "format": "pdf",
                    "metadata": {
                        "certificate_type": "acknowledgment",
                        "read_date": (
                            self.missive.read_at.isoformat()
                            if self.missive.read_at
                            else None
                        ),
                        "provider": "ar24",
                    },
                }
            )
        else:
            # AR en attente
            proofs.append(
                {
                    "type": "acknowledgment_receipt",
                    "label": "Acknowledgement of Receipt",
                    "available": False,
                    "url": None,
                    "generated_at": None,
                    "expires_at": None,
                    "format": "pdf",
                    "metadata": {
                        "status": "pending",
                        "message": "En attente de lecture par le destinataire",
                        "provider": "ar24",
                    },
                }
            )

        return proofs
