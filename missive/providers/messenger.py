"""
Provider Facebook Messenger pour l'envoi de messages.

Documentation: https://developers.facebook.com/docs/messenger-platform
"""

from typing import Any, Dict, Optional

from .base import BaseProvider


class MessengerProvider(BaseProvider):
    """
    Provider pour Facebook Messenger.
    
    Configuration requise:
        MESSENGER_PAGE_ACCESS_TOKEN: Token d'accès de la page Facebook
        MESSENGER_APP_SECRET: Secret de l'application
        
    Le destinataire doit avoir un PSID (Page-Scoped ID) Messenger stocké dans metadata.
    """

    name = "messenger"
    display_name = "Facebook Messenger"
    config_keys = ["MESSENGER_PAGE_ACCESS_TOKEN", "MESSENGER_VERIFY_TOKEN"]
    required_package = "requests"

    def validate(self) -> Dict[str, Any]:
        """Valide que le destinataire a un PSID Messenger"""
        if not self.missive:
            return {"is_valid": False, "error": "Missive non définie"}

        recipient = self.missive.recipient
        if not recipient:
            return {"is_valid": False, "error": "Destinataire non défini"}

        psid = recipient.metadata.get('messenger_psid') if recipient.metadata else None
        if not psid:
            return {
                "is_valid": False,
                "error": "Le destinataire n'a pas de PSID Messenger (ajouter dans metadata)",
            }

        return {"is_valid": True}

    def send(self) -> Dict[str, Any]:
        """
        Envoie un message via Messenger Send API.
        
        TODO: Implémenter l'envoi réel via:
        POST https://graph.facebook.com/v18.0/me/messages
        """
        validation = self.validate()
        if not validation["is_valid"]:
            self._update_status("FAILED", error_message=validation["error"])
            return {"success": False, "error": validation["error"]}

        # TODO: Implémenter l'envoi réel
        self._update_status(
            "SENT",
            external_id=f"messenger_sim_{self.missive.id}",
        )

        return {
            "success": True,
            "message_id": f"messenger_sim_{self.missive.id}",
        }

    def check_status(self, external_id: Optional[str] = None) -> Optional[str]:
        """Vérifie le statut via webhooks Messenger"""
        # TODO: Implémenter webhook handlers
        return None

