"""
Provider Certeurope pour l'envoi de Lettres Recommandées Électroniques (LRE).

Documentation: https://www.certeurope.fr/services/lettre-recommandee-electronique
"""

from typing import Any, Dict, Optional

from .base import BaseProvider


class CerteuropeProvider(BaseProvider):
    """
    Provider pour Certeurope (Lettre Recommandée Électronique).

    Configuration requise:
        CERTEUROPE_API_KEY: Clé API Certeurope
        CERTEUROPE_API_SECRET: Secret API
        CERTEUROPE_API_URL: URL de l'API
        CERTEUROPE_SENDER_EMAIL: Email de l'expéditeur enregistré

    Le destinataire doit avoir un email et une adresse postale complète.
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
    description_text = "Email recommandé électronique avec valeur juridique (LRE)"

    def validate(self) -> Dict[str, Any]:
        """Valide que le destinataire a un email et une adresse"""
        if not self.missive:
            return {"is_valid": False, "error": "Missive non définie"}

        recipient = self.missive.recipient
        if not recipient or not recipient.email:
            return {
                "is_valid": False,
                "error": "Le destinataire doit avoir un email pour une LRE Certeurope",
            }

        # Vérifier l'adresse postale (souvent requise)
        warnings = []
        if not recipient.address_line1:
            warnings.append("Adresse postale manquante")
        if not recipient.postal_code or not recipient.city:
            warnings.append("Code postal et ville requis")
        if not recipient.name:
            warnings.append("Nom du destinataire requis")

        if warnings:
            return {"is_valid": False, "error": "; ".join(warnings)}

        return {"is_valid": True}

    def send(self) -> Dict[str, Any]:
        """
        Envoie une LRE via Certeurope.

        TODO: Implémenter l'envoi réel via l'API Certeurope
        """
        validation = self.validate()
        if not validation["is_valid"]:
            self._update_status("FAILED", error_message=validation["error"])
            return {"success": False, "error": validation["error"]}

        # TODO: Implémenter l'envoi réel
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
            "deposit_certificate": "Certificat de dépôt Certeurope (simulation)",
        }

    def check_status(self, external_id: Optional[str] = None) -> Optional[str]:
        """
        Vérifie le statut de la LRE (envoi, réception, AR).

        TODO: Implémenter la vérification via API Certeurope
        """
        return None

    def get_proofs_of_delivery(self, service_type: Optional[str] = None) -> list:
        """
        Récupère toutes les preuves Certeurope.

        Certeurope génère plusieurs documents :
        1. Certificat de dépôt (preuve d'envoi)
        2. Copie du document envoyé (archivé)
        3. Accusé de réception (preuve de lecture)
        4. Certificat de présentation (si recommandé)
        5. Horodatage qualifié

        TODO: Implémenter via l'API Certeurope
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

        # 1. Certificat de dépôt (toujours disponible)
        proofs.append(
            {
                "type": "deposit_certificate",
                "label": "Certificat de dépôt",
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

        # 3. Horodatage qualifié
        proofs.append(
            {
                "type": "qualified_timestamp",
                "label": "Horodatage qualifié",
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
                    "label": "Accusé de réception",
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
                    "label": "Accusé de réception",
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
