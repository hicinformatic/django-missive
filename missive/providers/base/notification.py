"""In-app notification provider mixin."""

from typing import Any, Dict


class BaseNotificationMixin:
    """In-app notification-specific functionality mixin."""

    def get_notification_service_info(self) -> Dict[str, Any]:
        """Returns notification service info. Override in subclasses."""
        return {
            "credits": None,
            "credits_type": "unlimited",
            "is_available": None,
            "limits": {},
            "warnings": [
                "get_notification_service_info() method not implemented for this provider"
            ],
            "channels": [],
            "details": {},
        }

    def check_notification_delivery_status(self, **kwargs) -> Dict[str, Any]:
        """Checks notification delivery status. Override in subclasses."""
        return {
            "status": "unknown",
            "delivered_at": None,
            "read_at": None,
            "error_code": None,
            "error_message": "check_notification_delivery_status() method not implemented for this provider",
            "details": {},
        }

    def send_notification(self, **kwargs) -> bool:
        """
        Send an in-app notification. To be overridden in concrete providers.

        Args:
            **kwargs: Provider-specific options

        Returns:
            bool: True if successful, False otherwise
        """
        from ...models import MissiveStatus

        # Check that we have a recipient user
        if not self.missive.recipient_user:
            self._update_status(
                MissiveStatus.FAILED, error_message="No recipient user"
            )
            return False

        # To be implemented in subclasses
        raise NotImplementedError(
            f"{self.name} must implement the send_notification() method"
        )

    def format_notification_data(self) -> Dict[str, Any]:
        """
        Format notification data for frontend.

        Returns:
            Dict containing:
            - title (str): Notification title
            - body (str): Message body
            - icon (str): Icon to display
            - url (str): Redirect URL on click
            - priority (str): Display priority
            - metadata (Dict): Additional data

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

        # Redirect URL (from content_object if available)
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
            Dict containing:
            - accepts_notifications (bool): Accepts notifications
            - channels (List[str]): Canaux activés (web, mobile, email)
            - quiet_hours (bool): En période de silence
            - preferences (Dict): Préférences détaillées

        Example:
            prefs = provider.check_user_notification_preferences(user)
            if not prefs['accepts_notifications']:
                print("Utilisateur a désactivé les notifications")
        """
        # TODO: Implement according to your preferences model
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
        Cancel a scheduled notification.

        Args:
            **kwargs: Provider-specific options

        Base method that returns False. Providers that support
        cancellation must override this method with their API implementation.

        Returns:
            bool: True if cancellation succeeded, False otherwise
        """
        return False
