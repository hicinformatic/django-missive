"""
Provider Slack pour l'envoi de messages dans des canaux ou en privé.

Documentation: https://api.slack.com/messaging/sending
"""

from typing import Any, Dict, Optional

from .base import BaseProvider


class SlackProvider(BaseProvider):
    """
    Provider pour Slack.
    
    Configuration requise:
        SLACK_BOT_TOKEN: Token du bot Slack (xoxb-...)
        SLACK_SIGNING_SECRET: Secret pour vérifier les webhooks
        
    Le destinataire doit avoir:
    - Un user_id Slack (dans metadata.slack_user_id)
    - OU un channel_id Slack (dans metadata.slack_channel_id)
    """

    name = "slack"
    display_name = "Slack"
    config_keys = ["SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET"]
    required_package = "slack_sdk"

    def validate(self) -> Dict[str, Any]:
        """Valide que le destinataire a un user_id ou channel_id Slack"""
        if not self.missive:
            return {"is_valid": False, "error": "Missive non définie"}

        recipient = self.missive.recipient
        if not recipient:
            return {"is_valid": False, "error": "Destinataire non défini"}

        metadata = recipient.metadata or {}
        user_id = metadata.get('slack_user_id')
        channel_id = metadata.get('slack_channel_id')

        if not user_id and not channel_id:
            return {
                "is_valid": False,
                "error": "Le destinataire doit avoir un slack_user_id ou slack_channel_id dans metadata",
            }

        return {"is_valid": True}

    def send(self) -> Dict[str, Any]:
        """
        Envoie un message Slack via Web API.
        
        TODO: Implémenter l'envoi réel via slack_sdk:
        from slack_sdk import WebClient
        """
        validation = self.validate()
        if not validation["is_valid"]:
            self._update_status("FAILED", error_message=validation["error"])
            return {"success": False, "error": validation["error"]}

        # TODO: Implémenter l'envoi réel
        # client = WebClient(token=settings.SLACK_BOT_TOKEN)
        # response = client.chat_postMessage(
        #     channel=channel_id or user_id,
        #     text=self.missive.body_text,
        #     blocks=[...]  # Pour rich formatting
        # )

        self._update_status(
            "SENT",
            external_id=f"slack_sim_{self.missive.id}",
        )

        return {
            "success": True,
            "ts": f"slack_sim_{self.missive.id}",
        }

    def check_status(self, external_id: Optional[str] = None) -> Optional[str]:
        """Vérifie si le message a été lu (nécessite Events API)"""
        # TODO: Implémenter via Slack Events API
        return None

