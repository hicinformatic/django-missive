"""
Implémentation de référence pour Microsoft Teams utilisant BaseProfessionalMixin.
"""

from typing import Any, Dict


class BaseTeamsMixin:
    """
    Mixin de référence pour les fonctionnalités Microsoft Teams.

    Utilise la nouvelle architecture générique avec :
    - missive_type = PROFESSIONAL
    - brand_name = 'teams'

    Les providers concrets qui héritent de ce mixin doivent implémenter
    les méthodes d'envoi spécifiques à l'API Microsoft Graph.
    """

    def send_teams(self) -> bool:
        """
        Envoie un message Microsoft Teams.

        À implémenter dans les providers concrets selon leur méthode :
        - Microsoft Graph API (recommandé)
        - Incoming Webhooks
        - Bot Framework

        Returns:
            bool: True si succès, False sinon
        """
        from ...models import MissiveStatus

        # Récupérer le contexte d'organisation
        context = (
            self._get_organization_context()
            if hasattr(self, "_get_organization_context")
            else {}
        )

        if not context or not context.get("team_id"):
            self._update_status(
                MissiveStatus.FAILED,
                error_message="team_id manquant pour Microsoft Teams",
            )
            return False

        # À implémenter dans les sous-classes
        raise NotImplementedError(
            f"{self.name} doit implémenter la méthode send_teams()"
        )

    def get_teams_service_info(self) -> Dict[str, Any]:
        """
        Récupère les informations de l'organisation Microsoft Teams.

        Retourne :
        - Informations de l'organisation Microsoft 365
        - Quotas et limites d'API
        - État du service
        - Informations du tenant

        Returns:
            Dict contenant les informations du service Teams
        """
        return {
            "credits": None,  # Généralement illimité pour Teams
            "credits_type": "unlimited",
            "is_available": None,
            "limits": {
                "messages_per_second": 4,  # Rate limiting Graph API
                "attachment_size_mb": 250,  # 250MB max par fichier
                "max_message_length": 28000,  # Caractères max
            },
            "warnings": [
                "Méthode get_teams_service_info() non implémentée pour ce provider"
            ],
            "organization": {},
            "details": {},
        }

    def validate_teams_identifier(
        self, identifier: str, organization_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Valide un identifiant Microsoft Teams.

        Teams supporte plusieurs formats :
        - User ID : GUID Azure AD (ex: 48d31887-5fad-4d73-a9f5-3c356e68a038)
        - Channel ID : Format spécifique Teams
        - Email : user@domain.com (résolu via Graph API)
        - UPN : User Principal Name

        Args:
            identifier: Identifiant Teams
            organization_context: Contexte de l'organisation

        Returns:
            Dict avec résultats de validation
        """
        import re

        warnings = []

        # Vérifications basiques
        if not identifier:
            return {
                "is_valid": False,
                "warnings": ["Identifiant vide"],
            }

        # GUID format (Azure AD User ID)
        guid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        if re.match(guid_pattern, identifier.lower()):
            identifier_type = "user_id"
        # Email/UPN format
        elif "@" in identifier:
            identifier_type = "email"
        # Channel ID format (contient des caractères spéciaux)
        elif "%" in identifier or identifier.startswith("19:"):
            identifier_type = "channel_id"
        else:
            identifier_type = "unknown"
            warnings.append("Format d'identifiant Teams non reconnu")

        return {
            "is_valid": identifier_type != "unknown",
            "identifier_type": identifier_type,
            "warnings": warnings,
        }

    def format_teams_message(self, body: str, body_text: str = None) -> str:
        """
        Formate un message pour Microsoft Teams.

        Teams supporte plusieurs formats :
        - Texte simple
        - Markdown
        - Adaptive Cards (format JSON complexe)

        Pour le formatage Markdown :
        - **texte** pour gras
        - *texte* pour italique
        - ~~texte~~ pour barré
        - `texte` pour code
        - ```texte``` pour bloc de code

        Args:
            body: Corps du message (peut contenir du HTML)
            body_text: Version texte brut (prioritaire)

        Returns:
            str: Message formaté pour Teams
        """
        # Utiliser body_text si disponible
        message = body_text if body_text else body

        # TODO: Convertir le HTML basique en Markdown Teams
        # message = message.replace('<b>', '**').replace('</b>', '**')
        # message = message.replace('<i>', '*').replace('</i>', '*')
        # message = message.replace('<strong>', '**').replace('</strong>', '**')
        # message = message.replace('<em>', '*').replace('</em>', '*')
        # message = message.replace('<strike>', '~~').replace('</strike>', '~~')
        # message = message.replace('<code>', '`').replace('</code>', '`')

        return message

    def list_teams_channels(self, team_id: str = None) -> Dict[str, Any]:
        """
        Liste les channels disponibles dans une équipe Teams.

        Nécessite l'API Microsoft Graph avec les permissions appropriées :
        - Channel.ReadBasic.All
        - ChannelSettings.Read.All

        Args:
            team_id: ID de l'équipe (utilise organization_context si None)

        Returns:
            Dict contenant la liste des channels
        """
        # À implémenter dans les providers concrets avec l'API Graph
        return {
            "channels": [],
            "warnings": ["Méthode list_teams_channels() non implémentée"],
        }

    def get_teams_user_info(self, user_identifier: str) -> Dict[str, Any]:
        """
        Récupère les informations d'un utilisateur Teams via Graph API.

        Args:
            user_identifier: ID, email ou UPN de l'utilisateur

        Returns:
            Dict avec les informations de l'utilisateur
        """
        # À implémenter dans les providers concrets avec l'API Graph
        return {
            "user_id": None,
            "email": None,
            "display_name": None,
            "upn": None,
            "warnings": ["Méthode get_teams_user_info() non implémentée"],
        }

    def create_teams_adaptive_card(
        self, title: str, body: str, actions: list = None
    ) -> Dict[str, Any]:
        """
        Crée une Adaptive Card pour Teams.

        Les Adaptive Cards sont des cartes interactives riches en contenu
        avec support de boutons, images, formulaires, etc.

        Args:
            title: Titre de la carte
            body: Corps de la carte
            actions: Liste d'actions (boutons)

        Returns:
            Dict représentant l'Adaptive Card au format JSON
        """
        card = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": title,
                    "size": "Large",
                    "weight": "Bolder",
                },
                {"type": "TextBlock", "text": body, "wrap": True},
            ],
        }

        if actions:
            card["actions"] = actions

        return card
