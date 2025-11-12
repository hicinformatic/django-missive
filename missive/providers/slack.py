"""Slack provider for channel and direct messaging."""

from typing import Any, Dict, Optional

from .base import BaseProvider


class SlackProvider(BaseProvider):
    """Slack provider."""

    name = "slack"
    display_name = "Slack"
    supported_types = ["BRANDED"]
    services = ["slack", "messaging"]
    brands = ["slack"]
    config_keys = ["SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET"]
    required_packages = ["slack-sdk"]
    site_url = "https://slack.com/"
    status_url = "https://status.slack.com/"
    documentation_url = "https://api.slack.com/"
    description_text = "Professional team collaboration messaging"

    def validate(self) -> Dict[str, Any]:
        """Validates recipient has Slack user_id or channel_id."""
        if not self.missive:
            return {"is_valid": False, "error": "Missive not defined"}

        recipient = self.missive.recipient
        if not recipient:
            return {"is_valid": False, "error": "Recipient not defined"}

        metadata = recipient.metadata or {}
        user_id = metadata.get("slack_user_id")
        channel_id = metadata.get("slack_channel_id")

        if not user_id and not channel_id:
            return {
                "is_valid": False,
                "error": "Recipient must have slack_user_id or slack_channel_id in metadata",
            }

        return {"is_valid": True}

    def send_slack(self) -> bool:
        """Sends Slack message via Web API."""
        from ..models import MissiveStatus

        validation = self.validate()
        if not validation["is_valid"]:
            self._update_status(MissiveStatus.FAILED, error_message=validation["error"])
            return False

        # TODO: Implement actual sending
        # client = WebClient(token=settings.SLACK_BOT_TOKEN)
        # response = client.chat_postMessage(
        #     channel=channel_id or user_id,
        #     text=self.missive.body_text,
        #     blocks=[...]  # Pour rich formatting
        # )

        self._update_status(
            MissiveStatus.SENT,
            external_id=f"slack_sim_{self.missive.id}",
        )

        return True

    def check_status(self, external_id: Optional[str] = None) -> Optional[str]:
        """Checks if message was read (requires Events API)."""
        # TODO: Implement via Slack Events API
        return None
