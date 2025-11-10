"""
Implémentation de référence pour Slack utilisant BaseProfessionalMixin.
"""

from typing import Any, Dict


class BaseSlackMixin:
    """
    Mixin de référence pour les fonctionnalités Slack.

    Utilise la nouvelle architecture générique avec :
    - missive_type = PROFESSIONAL
    - brand_name = 'slack'

    Les providers concrets qui héritent de ce mixin doivent implémenter
    les méthodes d'envoi spécifiques à leur API Slack.
    """

    def send_slack(self) -> bool:
        """
        Envoie un message Slack.

        À implémenter dans les providers concrets selon leur API
        (Slack Web API, Incoming Webhooks, etc.)

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

        if not context or not context.get("workspace_id"):
            self._update_status(
                MissiveStatus.FAILED, error_message="workspace_id manquant pour Slack"
            )
            return False

        # À implémenter dans les sous-classes
        raise NotImplementedError(
            f"{self.name} doit implémenter la méthode send_slack()"
        )

    def get_slack_service_info(self) -> Dict[str, Any]:
        """
        Récupère les informations du workspace Slack.

        Retourne :
        - Nombre de messages disponibles (quota)
        - Informations du workspace
        - Liste des bots/integrations actifs
        - État du service

        Returns:
            Dict contenant les informations du service Slack
        """
        return {
            "credits": None,  # Généralement illimité pour Slack
            "credits_type": "unlimited",
            "is_available": None,
            "limits": {
                "messages_per_second": 1,  # Rate limiting Slack
                "attachment_size_mb": 1000,  # 1GB max par fichier
            },
            "warnings": [
                "Méthode get_slack_service_info() non implémentée pour ce provider"
            ],
            "organization": {},
            "details": {},
        }

    def validate_slack_identifier(
        self, identifier: str, organization_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Valide un identifiant Slack (user ID, channel ID, ou email).

        Slack supporte plusieurs formats :
        - User ID : U123456789
        - Channel ID : C123456789
        - Email : user@example.com (résolu via API)

        Args:
            identifier: Identifiant Slack
            organization_context: Contexte du workspace

        Returns:
            Dict avec résultats de validation
        """
        warnings = []

        # Vérifications basiques
        if not identifier:
            return {
                "is_valid": False,
                "warnings": ["Identifiant vide"],
            }

        # User ID format
        if identifier.startswith("U"):
            identifier_type = "user_id"
        # Channel ID format
        elif identifier.startswith("C") or identifier.startswith("G"):
            identifier_type = "channel_id"
        # Email format
        elif "@" in identifier:
            identifier_type = "email"
        else:
            identifier_type = "unknown"
            warnings.append("Format d'identifiant Slack non reconnu")

        return {
            "is_valid": identifier_type != "unknown",
            "identifier_type": identifier_type,
            "warnings": warnings,
        }

    def format_slack_message(self, body: str, body_text: str = None) -> str:
        """
        Formate un message pour Slack.

        Slack utilise mrkdwn (Markdown-like) :
        - *texte* pour gras
        - _texte_ pour italique
        - ~texte~ pour barré
        - `texte` pour code
        - ```texte``` pour bloc de code

        Args:
            body: Corps du message (peut contenir du HTML)
            body_text: Version texte brut (prioritaire)

        Returns:
            str: Message formaté pour Slack
        """
        # Utiliser body_text si disponible
        message = body_text if body_text else body

        # TODO: Convertir le HTML basique en mrkdwn Slack
        # message = message.replace('<b>', '*').replace('</b>', '*')
        # message = message.replace('<i>', '_').replace('</i>', '_')
        # message = message.replace('<strong>', '*').replace('</strong>', '*')
        # message = message.replace('<em>', '_').replace('</em>', '_')
        # message = message.replace('<strike>', '~').replace('</strike>', '~')
        # message = message.replace('<code>', '`').replace('</code>', '`')

        return message

    def list_slack_channels(self) -> Dict[str, Any]:
        """
        Liste les channels Slack disponibles dans le workspace.

        Nécessite l'API Slack avec les scopes appropriés :
        - channels:read (pour les channels publics)
        - groups:read (pour les channels privés)

        Returns:
            Dict contenant la liste des channels
        """
        # À implémenter dans les providers concrets avec l'API Slack
        return {
            "channels": [],
            "warnings": ["Méthode list_slack_channels() non implémentée"],
        }

    def get_slack_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Récupère les informations d'un utilisateur Slack.

        Args:
            user_id: ID de l'utilisateur Slack (format U123456789)

        Returns:
            Dict avec les informations de l'utilisateur
        """
        # À implémenter dans les providers concrets avec l'API Slack
        return {
            "user_id": user_id,
            "username": None,
            "email": None,
            "display_name": None,
            "warnings": ["Méthode get_slack_user_info() non implémentée"],
        }
