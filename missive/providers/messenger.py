"""Facebook Messenger provider."""

from typing import Any, Dict, Optional

from .base import BaseProvider


class MessengerProvider(BaseProvider):
    """
    Facebook Messenger provider.

    Required configuration:
        MESSENGER_PAGE_ACCESS_TOKEN: Facebook page access token
        MESSENGER_APP_SECRET: Application secret

    Recipient must have a PSID (Page-Scoped ID) Messenger stored in metadata.
    """

    name = "messenger"
    display_name = "Facebook Messenger"
    supported_types = ["BRANDED"]
    brands = ["messenger"]  # Facebook Messenger uniquement
    config_keys = ["MESSENGER_PAGE_ACCESS_TOKEN", "MESSENGER_VERIFY_TOKEN"]
    required_packages = ["requests"]
    site_url = "https://www.messenger.com/"
    description_text = "Facebook Messenger - Consumer instant messaging (Meta)"

    def validate(self) -> Dict[str, Any]:
        """Validate that the recipient has a Messenger PSID"""
        if not self.missive:
            return {"is_valid": False, "error": "Missive not defined"}

        recipient = self.missive.recipient
        if not recipient:
            return {"is_valid": False, "error": "Recipient not defined"}

        psid = recipient.metadata.get("messenger_psid") if recipient.metadata else None
        if not psid:
            return {
                "is_valid": False,
                "error": "Le destinataire n'a pas de PSID Messenger (ajouter dans metadata)",
            }

        return {"is_valid": True}

    def send(self) -> Dict[str, Any]:
        """
        Send a message via Messenger Send API.

        TODO: Implement actual sending via:
        POST https://graph.facebook.com/v18.0/me/messages
        """
        validation = self.validate()
        if not validation["is_valid"]:
            self._update_status("FAILED", error_message=validation["error"])
            return {"success": False, "error": validation["error"]}

        # TODO: Implement actual sending
        self._update_status(
            "SENT",
            external_id=f"messenger_sim_{self.missive.id}",
        )

        return {
            "success": True,
            "message_id": f"messenger_sim_{self.missive.id}",
        }

    def check_status(self, external_id: Optional[str] = None) -> Optional[str]:
        """Check status via Messenger webhooks"""
        # TODO: Implement webhook handlers
        return None
