"""
Provider Microsoft Teams pour l'envoi de messages.

Documentation: https://learn.microsoft.com/en-us/graph/api/chat-post-messages
"""

from typing import Any, Dict, Optional

from .base import BaseProvider


class TeamsProvider(BaseProvider):
    """
    Provider pour Microsoft Teams.

    Configuration requise:
        TEAMS_CLIENT_ID: Client ID de l'app Azure AD
        TEAMS_CLIENT_SECRET: Client Secret
        TEAMS_TENANT_ID: Tenant ID

    Le destinataire doit avoir:
    - Un user_id Microsoft (dans metadata.teams_user_id)
    - OU un channel_id Teams (dans metadata.teams_channel_id)
    """

    name = "teams"
    display_name = "Microsoft Teams"
    supported_types = ["BRANDED"]  # Utilise le type générique BRANDED
    services = ["teams", "messaging"]
    brands = ["teams"]  # Microsoft Teams uniquement
    config_keys = ["TEAMS_CLIENT_ID", "TEAMS_CLIENT_SECRET", "TEAMS_TENANT_ID"]
    required_packages = ["msgraph-core", "msal"]
    site_url = "https://www.microsoft.com/microsoft-teams/"
    status_url = "https://status.azure.com/en-us/status"
    documentation_url = "https://learn.microsoft.com/en-us/microsoftteams/"
    description_text = "Microsoft Teams - Communication d'entreprise (Microsoft 365)"

    def validate(self) -> Dict[str, Any]:
        """Valide que le destinataire a un user_id ou channel_id Teams"""
        if not self.missive:
            return {"is_valid": False, "error": "Missive non définie"}

        recipient = self.missive.recipient
        if not recipient:
            return {"is_valid": False, "error": "Destinataire non défini"}

        metadata = recipient.metadata or {}
        user_id = metadata.get("teams_user_id")
        channel_id = metadata.get("teams_channel_id")

        if not user_id and not channel_id:
            return {
                "is_valid": False,
                "error": "Le destinataire doit avoir un teams_user_id ou teams_channel_id dans metadata",
            }

        return {"is_valid": True}

    def send_teams(self) -> bool:
        """
        Envoie un message Teams via Microsoft Graph API.

        TODO: Implémenter l'envoi réel via:
        POST https://graph.microsoft.com/v1.0/chats/{chat-id}/messages
        """
        from ..models import MissiveStatus

        validation = self.validate()
        if not validation["is_valid"]:
            self._update_status(MissiveStatus.FAILED, error_message=validation["error"])
            return False

        # TODO: Implémenter l'envoi réel
        # 1. Obtenir un access token OAuth
        # 2. Envoyer le message via Graph API
        # 3. Gérer les adaptive cards pour rich content

        self._update_status(
            MissiveStatus.SENT,
            external_id=f"teams_sim_{self.missive.id}",
        )

        return True

    def check_status(self, external_id: Optional[str] = None) -> Optional[str]:
        """Vérifie le statut via Graph API"""
        # TODO: Implémenter via Microsoft Graph API
        return None
