"""Microsoft Teams provider."""

from typing import Any, Dict, Optional

from .base import BaseProvider


class TeamsProvider(BaseProvider):
    """
    Microsoft Teams provider.

    Required configuration:
        TEAMS_CLIENT_ID: Azure AD app Client ID
        TEAMS_CLIENT_SECRET: Client Secret
        TEAMS_TENANT_ID: Tenant ID

    Recipient must have:
    - Un user_id Microsoft (dans metadata.teams_user_id)
    - OU un channel_id Teams (dans metadata.teams_channel_id)
    """

    name = "teams"
    display_name = "Microsoft Teams"
    supported_types = ["BRANDED"]  # Uses generic BRANDED type
    services = ["teams", "messaging"]
    brands = ["teams"]  # Microsoft Teams uniquement
    config_keys = ["TEAMS_CLIENT_ID", "TEAMS_CLIENT_SECRET", "TEAMS_TENANT_ID"]
    required_packages = ["msgraph-core", "msal"]
    site_url = "https://www.microsoft.com/microsoft-teams/"
    status_url = "https://status.azure.com/en-us/status"
    documentation_url = "https://learn.microsoft.com/en-us/microsoftteams/"
    description_text = "Microsoft Teams - Enterprise communication (Microsoft 365)"

    def validate(self) -> Dict[str, Any]:
        """Validate that the recipient has a Teams user_id or channel_id"""
        if not self.missive:
            return {"is_valid": False, "error": "Missive not defined"}

        recipient = self.missive.recipient
        if not recipient:
            return {"is_valid": False, "error": "Recipient not defined"}

        metadata = recipient.metadata or {}
        user_id = metadata.get("teams_user_id")
        channel_id = metadata.get("teams_channel_id")

        if not user_id and not channel_id:
            return {
                "is_valid": False,
                "error": "Recipient must have a teams_user_id or teams_channel_id in metadata",
            }

        return {"is_valid": True}

    def send_teams(self) -> bool:
        """
        Send a Teams message via Microsoft Graph API.

        TODO: Implement actual sending via:
        POST https://graph.microsoft.com/v1.0/chats/{chat-id}/messages
        """
        from ..models import MissiveStatus

        validation = self.validate()
        if not validation["is_valid"]:
            self._update_status(MissiveStatus.FAILED, error_message=validation["error"])
            return False

        # TODO: Implement actual sending
        # 1. Obtenir un access token OAuth
        # 2. Envoyer le message via Graph API
        # 3. Gérer les adaptive cards pour rich content

        self._update_status(
            MissiveStatus.SENT,
            external_id=f"teams_sim_{self.missive.id}",
        )

        return True

    def check_status(self, external_id: Optional[str] = None) -> Optional[str]:
        """Check status via Graph API"""
        # TODO: Implement via Microsoft Graph API
        return None
