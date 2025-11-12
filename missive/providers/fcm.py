"""Firebase Cloud Messaging provider for push notifications."""

from typing import Any, Dict, Optional

from .base import BaseProvider


class FCMProvider(BaseProvider):
    """
    Firebase Cloud Messaging provider (push notifications).

    Required configuration:
        FCM_SERVER_KEY: Firebase server key
        or
        FCM_SERVICE_ACCOUNT_JSON: Path to service account JSON file

    Recipient must have an FCM device_token stored in metadata.
    """

    name = "fcm"
    display_name = "Firebase Cloud Messaging"
    supported_types = ["PUSH_NOTIFICATION"]
    config_keys = ["FCM_SERVER_KEY"]
    required_packages = ["firebase-admin"]
    site_url = "https://firebase.google.com/products/cloud-messaging"
    description_text = "Mobile push notifications for Android and iOS (Google Firebase)"

    def validate(self) -> Dict[str, Any]:
        """Validate that the recipient has an FCM device token"""
        if not self.missive:
            return {"is_valid": False, "error": "Missive not defined"}

        recipient = self.missive.recipient
        if not recipient:
            return {"is_valid": False, "error": "Recipient not defined"}

        device_token = (
            recipient.metadata.get("fcm_device_token") if recipient.metadata else None
        )
        if not device_token:
            return {
                "is_valid": False,
                "error": "Le destinataire n'a pas de device token FCM (ajouter dans metadata)",
            }

        return {"is_valid": True}

    def send(self) -> Dict[str, Any]:
        """
        Send a push notification via FCM.

        TODO: Implement actual sending via firebase-admin SDK:
        from firebase_admin import messaging
        """
        validation = self.validate()
        if not validation["is_valid"]:
            self._update_status("FAILED", error_message=validation["error"])
            return {"success": False, "error": validation["error"]}

        # TODO: Implement actual sending
        # message = messaging.Message(
        #     notification=messaging.Notification(
        #         title=self.missive.subject,
        #         body=self.missive.body_text or self.missive.body[:100],
        #     ),
        #     token=device_token,
        # )
        # response = messaging.send(message)

        self._update_status(
            "SENT",
            external_id=f"fcm_sim_{self.missive.id}",
        )

        return {
            "success": True,
            "message_id": f"fcm_sim_{self.missive.id}",
        }

    def check_status(self, external_id: Optional[str] = None) -> Optional[str]:
        """
        Check delivery status.

        Note: FCM fournit des callbacks via webhooks.
        """
        return None
