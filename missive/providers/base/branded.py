"""
Mixin générique pour les messageries d'applications (branded).
Supporte : WhatsApp, Telegram, Signal, Discord, Messenger, Slack, Teams, etc.

Architecture ultra-simplifiée : le nom du provider (self.name) détermine
automatiquement quelle méthode appeler (send_{name}).
"""

from typing import Any, Dict, Optional


class BaseBrandedMixin:
    """
    Mixin générique pour TOUTES les messageries d'applications.

    Architecture simplifiée : le provider définit son nom (self.name) et
    implémente send_{name}(). Le dispatch se fait automatiquement.

    Kwargs standardisés pour send_branded() :
        channel_id (str): ID du canal/conversation
        user_id (str): ID de l'utilisateur destinataire
        thread_id (str): ID du thread/fil de discussion
        reply_to (str): ID du message auquel répondre
        attachments (list): Liste de fichiers/médias à joindre
        buttons (list): Boutons interactifs
        parse_mode (str): Mode de parsing ('markdown', 'html', etc.)
        disable_notification (bool): Envoyer silencieusement
        scheduled_time (datetime|str): Envoi programmé
        priority (str): 'low', 'normal', 'high'

    Exemples :
        class WhatsAppProvider(BaseProvider):
            name = "whatsapp"
            supported_types = [MissiveType.BRANDED]

            def send_whatsapp(self):  # ← Automatiquement appelé
                pass

        class SlackProvider(BaseProvider):
            name = "slack"
            supported_types = [MissiveType.BRANDED]

            def send_slack(self):  # ← Automatiquement appelé
                pass

    Plus besoin de brand_name ! Le nom du provider suffit.
    """

    def send_branded(self, brand_name: Optional[str] = None, **kwargs) -> bool:
        """
        Envoie un message via une messagerie d'application.
        Dispatch automatique vers send_{brand_name}() ou send_{self.name}().

        Args:
            brand_name: Nom de la brand à utiliser (optionnel).
                       Si non fourni, utilise self.name.
                       Utile pour les providers multi-brands (ex: Twilio avec whatsapp).
            **kwargs: Options propriétaires du provider

        Returns:
            bool: True si succès, False sinon

        Example:
            # Provider mono-brand (Slack)
            provider.send_branded()  # → send_slack()

            # Provider multi-brand (Twilio)
            provider.send_branded("whatsapp")  # → send_whatsapp()
            provider.send_branded()  # → send_twilio()

            # Avec options
            provider.send_branded(sender="MyApp", tag="promo-01")
        """
        from ...models import MissiveStatus

        # Déterminer le nom à utiliser
        target_name = brand_name if brand_name else getattr(self, "name", None)

        if not target_name:
            self._update_status(
                MissiveStatus.FAILED,
                error_message="Provider name ou brand_name manquant",
            )
            return False

        # Dispatch automatique vers send_{target_name}()
        method_name = f"send_{target_name.lower()}"

        if not hasattr(self, method_name):
            self._update_status(
                MissiveStatus.FAILED,
                error_message=f"Méthode {method_name}() non implémentée pour ce provider",
            )
            return False

        # Appel de la méthode spécifique avec les kwargs
        return getattr(self, method_name)(**kwargs)

    def get_branded_service_info(
        self, brand_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Récupère les informations du service de messagerie.
        Dispatch automatique vers get_{brand_name}_service_info() ou get_{self.name}_service_info().

        Args:
            brand_name: Nom de la brand à utiliser (optionnel).
                       Si non fourni, utilise self.name.
                       Utile pour les providers multi-brands.

        Returns:
            Dict contenant les informations du service

        Example:
            # Provider multi-brand (Twilio)
            provider.get_branded_service_info("whatsapp")  # → get_whatsapp_service_info()
            provider.get_branded_service_info()  # → get_twilio_service_info()
        """
        # Déterminer le nom à utiliser
        target_name = brand_name if brand_name else getattr(self, "name", None)

        if not target_name:
            return {
                "credits": None,
                "is_available": None,
                "limits": {},
                "warnings": ["Provider name ou brand_name manquant"],
                "details": {},
            }

        # Dispatch automatique vers get_{target_name}_service_info()
        method_name = f"get_{target_name.lower()}_service_info"

        if hasattr(self, method_name):
            return getattr(self, method_name)()

        return {
            "credits": None,
            "is_available": None,
            "limits": {},
            "warnings": [f"Méthode {method_name}() non implémentée pour ce provider"],
            "details": {},
        }

    def check_branded_delivery_status(
        self, brand_name: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Vérifie le statut de livraison d'un message branded spécifique.
        Dispatch automatique vers check_{brand_name}_delivery_status() ou check_{self.name}_delivery_status().

        Args:
            brand_name: Nom de la brand à utiliser (optionnel).
                       Si non fourni, utilise self.name.
                       Utile pour les providers multi-brands.
            **kwargs: Options supplémentaires pour le provider

        Returns:
            Dict contenant :
                - status: Statut actuel ('delivered', 'read', 'failed', 'sent', etc.)
                - delivered_at: Date/heure de livraison
                - read_at: Date/heure de lecture
                - error_code: Code d'erreur (si échec)
                - error_message: Message d'erreur (si échec)
                - details: Infos supplémentaires du provider

        Example:
            # Provider multi-brand (Twilio)
            provider.check_branded_delivery_status("whatsapp")  # → check_whatsapp_delivery_status()
            provider.check_branded_delivery_status()  # → check_twilio_delivery_status()
        """
        # Déterminer le nom à utiliser
        target_name = brand_name if brand_name else getattr(self, "name", None)

        if not target_name:
            return {
                "status": "unknown",
                "delivered_at": None,
                "read_at": None,
                "error_code": None,
                "error_message": "Provider name ou brand_name manquant",
                "details": {},
            }

        # Générer le nom de la méthode : check_{brand_name}_delivery_status
        method_name = f"check_{target_name.lower()}_delivery_status"

        # Chercher la méthode dans la classe
        try:
            return getattr(self, method_name)(**kwargs)

        except AttributeError:
            # La méthode n'existe pas
            return {
                "status": "unknown",
                "delivered_at": None,
                "read_at": None,
                "error_code": None,
                "error_message": f"Méthode {method_name}() non implémentée",
                "details": {},
            }

    def _get_organization_context(self) -> Optional[Dict[str, Any]]:
        """
        Helper optionnel pour récupérer le contexte d'organisation depuis metadata.

        Utile pour les messageries qui nécessitent un contexte (Slack, Teams, Discord servers).
        Le contexte est stocké dans missive.metadata.

        Returns:
            Dict avec workspace_id, team_id, channel_id, server_id, etc. ou None
        """
        if not self.missive or not self.missive.metadata:
            return None

        metadata = self.missive.metadata
        context = {}

        # Identifiants courants
        for key in [
            "workspace_id",
            "team_id",
            "channel_id",
            "organization_id",
            "server_id",
            "guild_id",
            "chat_id",
        ]:
            if key in metadata:
                context[key] = metadata[key]

        return context if context else None

    # ==================== MÉTHODES SPÉCIFIQUES PAR APPLICATION ====================
    # Les providers concrets implémentent ces méthodes selon leurs besoins.
    # Le nom de la méthode doit correspondre au nom du provider.

    # Exemple pour WhatsApp :
    #
    # class WhatsAppProvider(BaseProvider):
    #     name = "whatsapp"
    #     supported_types = [MissiveType.BRANDED]
    #
    #     def send_whatsapp(self) -> bool:
    #         """Envoie un message WhatsApp"""
    #         phone = self.missive.get_recipient_phone()
    #         # Implémentation...
    #         pass
    #
    #     def get_whatsapp_service_info(self) -> Dict[str, Any]:
    #         """Info service WhatsApp"""
    #         return {"credits": 1000, ...}

    # Exemple pour Slack :
    #
    # class SlackProvider(BaseProvider):
    #     name = "slack"
    #     supported_types = [MissiveType.BRANDED]
    #
    #     def send_slack(self) -> bool:
    #         """Envoie un message Slack"""
    #         context = self._get_organization_context()
    #         workspace_id = context.get('workspace_id')
    #         channel_id = context.get('channel_id')
    #         # Implémentation...
    #         pass
    #
    #     def get_slack_service_info(self) -> Dict[str, Any]:
    #         """Info service Slack"""
    #         return {"credits": None, "is_available": True, ...}

    # ==================== CANCELLATION (Méthode générique) ====================

    def cancel_branded(self, brand_name: Optional[str] = None, **kwargs) -> bool:
        """
        Annule l'envoi d'un message de messagerie de marque (WhatsApp, Slack, Teams, etc.).
        Dispatch automatique vers cancel_{brand_name}() ou cancel_{self.name}().

        Args:
            brand_name: Nom de la brand à utiliser (optionnel).
                       Si non fourni, utilise self.name.
                       Utile pour les providers multi-brands.
            **kwargs: Options propriétaires du provider

        Returns:
            bool: True si annulation réussie, False sinon

        Example:
            # Provider mono-brand (Slack)
            provider.cancel_branded()  # → cancel_slack()

            # Provider multi-brand (Twilio)
            provider.cancel_branded("whatsapp")  # → cancel_whatsapp()
            provider.cancel_branded()  # → cancel_twilio()
        """
        # Déterminer le nom à utiliser
        target_name = brand_name if brand_name else getattr(self, "name", None)

        if not target_name:
            return False

        # Dispatch automatique vers cancel_{target_name}()
        method_name = f"cancel_{target_name.lower()}"

        if hasattr(self, method_name):
            return getattr(self, method_name)()

        # Par défaut, retourne False si la méthode n'est pas implémentée
        return False
