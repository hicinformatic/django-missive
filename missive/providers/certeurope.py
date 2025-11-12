"""Certeurope provider for electronic registered letters (LRE)."""

from typing import Any, Dict, Optional

from .base import BaseProvider


class CerteuropeProvider(BaseProvider):
    """
    Certeurope provider (Electronic Registered Letter).

    Required configuration:
        CERTEUROPE_API_KEY: Certeurope API key
        CERTEUROPE_API_SECRET: API Secret
        CERTEUROPE_API_URL: API URL
        CERTEUROPE_SENDER_EMAIL: Registered sender email

    Recipient must have an email and complete postal address.
    """

    name = "certeurope"
    display_name = "Certeurope (LRE)"
    supported_types = ["LRE"]
    config_keys = [
        "CERTEUROPE_API_KEY",
        "CERTEUROPE_API_SECRET",
        "CERTEUROPE_API_URL",
        "CERTEUROPE_SENDER_EMAIL",
    ]
    required_packages = ["requests"]
    site_url = "https://www.certeurope.fr/"
    description_text = "Electronic registered email with legal value (LRE)"

    def validate(self) -> Dict[str, Any]:
        """Validate that the recipient has an email and address"""
        if not self.missive:
            return {"is_valid": False, "error": "Missive not defined"}

        recipient = self.missive.recipient
        if not recipient or not recipient.email:
            return {
                "is_valid": False,
                "error": "Recipient must have an email for Certeurope ERL",
            }

        # Check postal address (often required)
        warnings = []
        if not recipient.address_line1:
            warnings.append("Postal address missing")
        if not recipient.postal_code or not recipient.city:
            warnings.append("Postal code and city required")
        if not recipient.name:
            warnings.append("Recipient name required")

        if warnings:
            return {"is_valid": False, "error": "; ".join(warnings)}

        return {"is_valid": True}

    def send(self) -> Dict[str, Any]:
        """
        Send an LRE via Certeurope.

        TODO: Implement actual sending via Certeurope API
        """
        validation = self.validate()
        if not validation["is_valid"]:
            self._update_status("FAILED", error_message=validation["error"])
            return {"success": False, "error": validation["error"]}

        # TODO: Implement actual sending
        # 1. Générer le PDF du courrier
        # 2. Créer la requête SOAP/REST Certeurope
        # 3. Envoyer le document signé
        # 4. Récupérer le certificat de dépôt

        self._update_status(
            "SENT",
            external_id=f"certeurope_sim_{self.missive.id}",
        )

        return {
            "success": True,
            "tracking_id": f"certeurope_sim_{self.missive.id}",
            "deposit_certificate": "Certeurope deposit certificate (simulation)",
        }

    def check_status(self, external_id: Optional[str] = None) -> Optional[str]:
        """
        Check the LRE status (sending, reception, AR).

        TODO: Implement verification via Certeurope API
        """
        return None

    def get_proofs_of_delivery(self, service_type: Optional[str] = None) -> list:
        """
        Get all Certeurope proofs.

        Certeurope generates several documents:
        1. Deposit certificate (proof of sending)
        2. Copy of sent document (archived)
        3. Acknowledgement of receipt (proof of reading)
        4. Presentation certificate (if registered)
        5. Qualified timestamp

        TODO: Implement via Certeurope API
        """
        if not self.missive:
            return []

        external_id = self.missive.external_id
        if not external_id or not external_id.startswith("certeurope_"):
            return []

        # TODO: Appel API réel (SOAP ou REST selon version)

        # Simulation
        from datetime import timedelta

        from django.utils import timezone

        sent_at = self.missive.sent_at or timezone.now()
        expiration = sent_at + timedelta(days=3650)  # 10 ans
        proofs = []

        # 1. Deposit certificate (always available)
        proofs.append(
            {
                "type": "deposit_certificate",
                "label": "Deposit Certificate",
                "available": True,
                "url": f"https://www.certeurope.fr/lre/deposit/{external_id}.pdf",
                "generated_at": sent_at,
                "expires_at": expiration,
                "format": "pdf",
                "metadata": {
                    "certificate_type": "deposit",
                    "legal_value": "Valeur probante eIDAS",
                    "provider": "certeurope",
                },
            }
        )

        # 2. Document archivé signé
        proofs.append(
            {
                "type": "archived_document",
                "label": "Document archivé",
                "available": True,
                "url": f"https://www.certeurope.fr/lre/archive/{external_id}.pdf",
                "generated_at": sent_at,
                "expires_at": expiration,
                "format": "pdf",
                "metadata": {
                    "document_type": "archived_signed",
                    "provider": "certeurope",
                },
            }
        )

        # 3. Qualified timestamp
        proofs.append(
            {
                "type": "qualified_timestamp",
                "label": "Qualified Timestamp",
                "available": True,
                "url": f"https://www.certeurope.fr/lre/timestamp/{external_id}.xml",
                "generated_at": sent_at,
                "expires_at": expiration,
                "format": "xml",
                "metadata": {
                    "timestamp_type": "qualified_eidas",
                    "provider": "certeurope",
                },
            }
        )

        # 4. AR électronique (si lu)
        if self.missive.read_at:
            proofs.append(
                {
                    "type": "acknowledgment_receipt",
                    "label": "Acknowledgement of Receipt",
                    "available": True,
                    "url": f"https://www.certeurope.fr/lre/ar/{external_id}.pdf",
                    "generated_at": self.missive.read_at,
                    "expires_at": expiration,
                    "format": "pdf",
                    "metadata": {
                        "certificate_type": "acknowledgment",
                        "read_date": (
                            self.missive.read_at.isoformat()
                            if self.missive.read_at
                            else None
                        ),
                        "provider": "certeurope",
                    },
                }
            )
        else:
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
                        "message": "En attente de lecture",
                        "provider": "certeurope",
                    },
                }
            )

        return proofs
