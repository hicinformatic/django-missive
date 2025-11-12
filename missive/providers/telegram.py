"""Telegram Bot API provider."""

from typing import Any, Dict, Optional

from .base import BaseProvider


class TelegramProvider(BaseProvider):
    """Telegram provider."""

    name = "telegram"
    display_name = "Telegram"
    supported_types = ["BRANDED"]
    brands = ["telegram"]
    config_keys = ["TELEGRAM_BOT_TOKEN"]
    required_packages = ["python-telegram-bot"]
    site_url = "https://telegram.org/"
    description_text = "Secure instant messaging with bots"

    def validate(self) -> Dict[str, Any]:
        """Validates recipient has Telegram chat_id."""
        if not self.missive:
            return {"is_valid": False, "error": "Missive not defined"}

        recipient = self.missive.recipient
        if not recipient:
            return {"is_valid": False, "error": "Recipient not defined"}

        chat_id = (
            recipient.metadata.get("telegram_chat_id") if recipient.metadata else None
        )
        if not chat_id:
            return {
                "is_valid": False,
                "error": "Recipient has no telegram_chat_id in metadata",
            }

        return {"is_valid": True}

    def send(self) -> Dict[str, Any]:
        """Sends message via Telegram Bot API."""
        validation = self.validate()
        if not validation["is_valid"]:
            self._update_status("FAILED", error_message=validation["error"])
            return {"success": False, "error": validation["error"]}

        # TODO: Implement actual sending
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
        Check status of a Telegram message.

        Note: Telegram does not provide automatic webhooks for delivery status.
        Can only know if message was sent.
        """
        # TODO: Implement if needed
        return None
