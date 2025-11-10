"""
Provider AR24 pour l'envoi de Lettres Recommandées Électroniques (LRE).

Documentation: https://www.ar24.fr/api
"""

from typing import Any, Dict, Optional

from .base import BaseProvider


class AR24Provider(BaseProvider):
    """
    Provider pour AR24 (Lettre Recommandée Électronique).

    Configuration requise:
        AR24_API_TOKEN: Token d'API AR24
        AR24_API_URL: URL de l'API (production ou sandbox)
        AR24_SENDER_ID: ID de l'expéditeur enregistré sur AR24

    Le destinataire doit avoir un email et idéalement une adresse postale complète.
    """

    name = "ar24"
    display_name = "AR24 (LRE)"
    supported_types = ["LRE"]
    config_keys = ["AR24_API_TOKEN", "AR24_API_URL", "AR24_SENDER_ID"]
    required_packages = ["requests"]
    site_url = "https://www.ar24.fr/"
    description_text = "Email recommandé électronique (LRE) avec valeur juridique"

    def validate(self) -> Dict[str, Any]:
        """Valide que le destinataire a un email et une adresse"""
        if not self.missive:
            return {"is_valid": False, "error": "Missive non définie"}

        recipient = self.missive.recipient
        if not recipient or not recipient.email:
            return {
                "is_valid": False,
                "error": "Le destinataire doit avoir un email pour une LRE AR24",
            }

        # Vérifier l'adresse postale (recommandé mais pas obligatoire)
        warnings = []
        if not recipient.address_line1:
            warnings.append("Adresse postale manquante (recommandée pour AR24)")
        if not recipient.postal_code or not recipient.city:
            warnings.append("Code postal et ville manquants")

        return {"is_valid": True, "warnings": warnings}

    def send(self) -> Dict[str, Any]:
        """
        Envoie une LRE via AR24.

        TODO: Implémenter l'envoi réel via:
        POST https://api.ar24.fr/api/v2/mail/send
        """
        validation = self.validate()
        if not validation["is_valid"]:
            self._update_status("FAILED", error_message=validation["error"])
            return {"success": False, "error": validation["error"]}

        # TODO: Implémenter l'envoi réel
        # 1. Générer le PDF du courrier
        # 2. Préparer le payload AR24 avec destinataire(s)
        # 3. POST vers /api/v2/mail/send
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
        Vérifie le statut de la LRE (dépôt, envoi, réception, lecture).

        TODO: Implémenter via:
        GET https://api.ar24.fr/api/v2/mail/{mail_id}/status
        """
        return None

    def get_proofs_of_delivery(self, service_type: Optional[str] = None) -> list:
        """
        Récupère toutes les preuves AR24.

        AR24 génère plusieurs documents :
        1. Certificat de dépôt (immédiat)
        2. Copie du document envoyé
        3. Accusé de réception (quand le destinataire lit)
        4. Certificat de refus (si non réclamé après 15 jours)

        TODO: Implémenter via:
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
        #         # Certificat de dépôt (toujours disponible)
        #         if data.get('deposit_certificate'):
        #             proofs_list.append({...})
        #
        #         # Copie du document
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

        # 1. Certificat de dépôt (toujours disponible dès l'envoi)
        proofs.append(
            {
                "type": "deposit_certificate",
                "label": "Certificat de dépôt",
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

        # 2. Copie du document envoyé
        proofs.append(
            {
                "type": "sent_document",
                "label": "Document envoyé",
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
                    "label": "Accusé de réception",
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
                    "label": "Accusé de réception",
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
