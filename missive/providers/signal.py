"""
Provider Signal pour l'envoi de messages via Signal Messenger.

Documentation: https://github.com/bbernhard/signal-cli-rest-api
"""

from typing import Any, Dict, Optional

from .base import BaseProvider


class SignalProvider(BaseProvider):
    """
    Provider pour Signal Messenger.

    Configuration requise:
        SIGNAL_CLI_REST_API_URL: URL de l'API signal-cli-rest-api
        SIGNAL_SENDER_NUMBER: Numéro expéditeur enregistré

    Le destinataire doit avoir un numéro de téléphone mobile.
    """

    name = "signal"
    display_name = "Signal"
    supported_types = ["BRANDED"]
    brands = ["signal"]  # Signal uniquement
    config_keys = ["SIGNAL_API_KEY"]
    required_packages = ["requests"]
    site_url = "https://signal.org/"
    description_text = "Messagerie sécurisée et chiffrée de bout en bout"

    def validate(self) -> Dict[str, Any]:
        """Valide que le destinataire a un numéro mobile"""
        if not self.missive:
            return {"is_valid": False, "error": "Missive non définie"}

        recipient = self.missive.recipient
        if not recipient or not recipient.mobile:
            return {
                "is_valid": False,
                "error": "Le destinataire doit avoir un numéro de mobile pour Signal",
            }

        return {"is_valid": True}

    def send(self) -> Dict[str, Any]:
        """
        Envoie un message via Signal.

        TODO: Implémenter l'envoi réel via signal-cli-rest-api
        """
        validation = self.validate()
        if not validation["is_valid"]:
            self._update_status("FAILED", error_message=validation["error"])
            return {"success": False, "error": validation["error"]}

        # TODO: Implémenter l'envoi réel
        self._update_status(
            "SENT",
            external_id=f"signal_sim_{self.missive.id}",
        )

        return {
            "success": True,
            "message_id": f"signal_sim_{self.missive.id}",
        }

    def check_status(self, external_id: Optional[str] = None) -> Optional[str]:
        """Vérifie le statut d'un message Signal"""
        # TODO: Implémenter si besoin
        return None
