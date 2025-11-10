"""
Provider Telegram pour l'envoi de messages via Telegram Bot API.

Documentation: https://core.telegram.org/bots/api
"""

from typing import Any, Dict, Optional

from .base import BaseProvider


class TelegramProvider(BaseProvider):
    """
    Provider pour Telegram.
    
    Configuration requise:
        TELEGRAM_BOT_TOKEN: Token du bot Telegram
        
    Le destinataire doit avoir un chat_id Telegram (stocker dans metadata du Recipient)
    """

    name = "telegram"
    display_name = "Telegram"
    config_keys = ["TELEGRAM_BOT_TOKEN"]
    required_package = "telegram"

    def validate(self) -> Dict[str, Any]:
        """Valide que le destinataire a un chat_id Telegram"""
        if not self.missive:
            return {"is_valid": False, "error": "Missive non définie"}

        # Vérifier que le recipient a un chat_id dans metadata
        recipient = self.missive.recipient
        if not recipient:
            return {"is_valid": False, "error": "Destinataire non défini"}

        chat_id = recipient.metadata.get('telegram_chat_id') if recipient.metadata else None
        if not chat_id:
            return {
                "is_valid": False,
                "error": "Le destinataire n'a pas de chat_id Telegram (ajouter dans metadata)",
            }

        return {"is_valid": True}

    def send(self) -> Dict[str, Any]:
        """
        Envoie un message via Telegram Bot API.
        
        TODO: Implémenter l'envoi réel via requests vers:
        https://api.telegram.org/bot{token}/sendMessage
        """
        validation = self.validate()
        if not validation["is_valid"]:
            self._update_status("FAILED", error_message=validation["error"])
            return {"success": False, "error": validation["error"]}

        # TODO: Implémenter l'envoi réel
        # Pour l'instant, simuler l'envoi
        self._update_status(
            "SENT",
            external_id=f"telegram_sim_{self.missive.id}",
        )

        return {
            "success": True,
            "message_id": f"telegram_sim_{self.missive.id}",
        }

    def check_status(self, external_id: Optional[str] = None) -> Optional[str]:
        """
        Vérifie le statut d'un message Telegram.
        
        Note: Telegram ne fournit pas de webhook automatique pour le statut de livraison.
        On ne peut savoir que si le message a été envoyé.
        """
        # TODO: Implémenter si besoin
        return None

