"""
Mixin pour les fonctionnalités notification in-app des providers.
"""

from typing import Any, Dict


class BaseNotificationMixin:
    """
    Mixin fournissant les fonctionnalités spécifiques aux notifications in-app.
    """

    def get_notification_service_info(self) -> Dict[str, Any]:
        """
        Récupère les informations du compte/service Notification.

        Retourne les informations importantes pour le service de notifications :
        - Nombre de notifications envoyées/limites
        - État du service (actif/inactif)
        - Channels disponibles (in-app, push, etc.)

        Returns:
            Dict contenant :
                - credits: Généralement 'unlimited' pour les notifications in-app
                - credits_type: 'unlimited' ou 'count'
                - is_available: bool, service accessible
                - limits: Dict avec les limites (notifications/jour, etc.)
                - warnings: Liste des alertes
                - channels: Liste des canaux disponibles
                - details: Dict avec infos supplémentaires

        À surcharger dans les providers concrets.
        """
        return {
            "credits": None,
            "credits_type": "unlimited",
            "is_available": None,
            "limits": {},
            "warnings": [
                "Méthode get_notification_service_info() non implémentée pour ce provider"
            ],
            "channels": [],
            "details": {},
        }

    def check_notification_delivery_status(self, **kwargs) -> Dict[str, Any]:
        """
        Vérifie le statut de livraison d'une notification spécifique.

        Returns:
            Dict contenant :
                - status: Statut actuel ('delivered', 'read', 'dismissed', etc.)
                - delivered_at: Date/heure de livraison
                - read_at: Date/heure de lecture
                - error_code: Code d'erreur (si échec)
                - error_message: Message d'erreur (si échec)
                - details: Infos supplémentaires du provider

        À surcharger dans les providers concrets.
        """
        return {
            "status": "unknown",
            "delivered_at": None,
            "read_at": None,
            "error_code": None,
            "error_message": "Méthode check_notification_delivery_status() non implémentée pour ce provider",
            "details": {},
        }

    def send_notification(self, **kwargs) -> bool:
        """
        Envoie une notification in-app. À surcharger dans les providers concrets.

        Args:
            **kwargs: Options propriétaires du provider

        Returns:
            bool: True si succès, False sinon
        """
        from ...models import MissiveStatus

        # Vérifier qu'on a un utilisateur destinataire
        if not self.missive.recipient_user:
            self._update_status(
                MissiveStatus.FAILED, error_message="Pas d'utilisateur destinataire"
            )
            return False

        # À implémenter dans les sous-classes
        raise NotImplementedError(
            f"{self.name} doit implémenter la méthode send_notification()"
        )

    def format_notification_data(self) -> Dict[str, Any]:
        """
        Formate les données de notification pour le frontend.

        Returns:
            Dict contenant :
            - title (str): Titre de la notification
            - body (str): Corps du message
            - icon (str): Icône à afficher
            - url (str): URL de redirection au clic
            - priority (str): Priorité d'affichage
            - metadata (Dict): Données additionnelles

        Example:
            data = provider.format_notification_data()
            # → {'title': '...', 'body': '...', 'icon': '🔔', ...}
        """
        if not self.missive:
            return {}

        # Icônes par type de contenu
        icon_map = {
            "order": "🛒",
            "invoice": "📄",
            "appointment": "📅",
            "message": "💬",
            "alert": "⚠️",
            "success": "✅",
        }

        # Déterminer l'icône depuis les métadonnées
        notification_type = self.missive.metadata.get("notification_type", "message")
        icon = icon_map.get(notification_type, "🔔")

        # URL de redirection (depuis content_object si disponible)
        redirect_url = ""
        if self.missive.content_object:
            # TODO: Générer l'URL selon le type d'objet
            # if isinstance(self.missive.content_object, Order):
            #     redirect_url = f'/orders/{self.missive.content_object.id}/'

            redirect_url = self.missive.metadata.get("redirect_url", "")

        return {
            "title": self.missive.subject,
            "body": self.missive.body_text or self.missive.body,
            "icon": icon,
            "url": redirect_url,
            "priority": self.missive.priority,
            "metadata": self.missive.metadata,
        }

    def check_user_notification_preferences(self, user) -> Dict[str, Any]:
        """
        Vérifie les préférences de notification de l'utilisateur.

        Args:
            user: Utilisateur Django

        Returns:
            Dict contenant :
            - accepts_notifications (bool): Accepte les notifications
            - channels (List[str]): Canaux activés (web, mobile, email)
            - quiet_hours (bool): En période de silence
            - preferences (Dict): Préférences détaillées

        Example:
            prefs = provider.check_user_notification_preferences(user)
            if not prefs['accepts_notifications']:
                print("Utilisateur a désactivé les notifications")
        """
        # TODO: Implémenter selon votre modèle de préférences
        # from myapp.models import UserNotificationPreferences
        # prefs = UserNotificationPreferences.objects.get(user=user)

        return {
            "accepts_notifications": True,  # Par défaut
            "channels": ["web"],
            "quiet_hours": False,
            "preferences": {},
        }

    def cancel_notification(self, **kwargs) -> bool:
        """
        Annule une notification programmée.

        Args:
            **kwargs: Options propriétaires du provider

        Méthode de base qui retourne False. Les providers qui supportent
        l'annulation doivent surcharger cette méthode avec leur implémentation API.

        Returns:
            bool: True si annulation réussie, False sinon
        """
        return False
