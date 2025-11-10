"""
Provider FCM (Firebase Cloud Messaging) pour notifications push Android/iOS.

Documentation: https://firebase.google.com/docs/cloud-messaging
"""

from typing import Any, Dict, Optional

from .base import BaseProvider


class FCMProvider(BaseProvider):
    """
    Provider pour Firebase Cloud Messaging (notifications push).

    Configuration requise:
        FCM_SERVER_KEY: Clé serveur Firebase
        ou
        FCM_SERVICE_ACCOUNT_JSON: Chemin vers le fichier JSON du compte de service

    Le destinataire doit avoir un device_token FCM stocké dans metadata.
    """

    name = "fcm"
    display_name = "Firebase Cloud Messaging"
    supported_types = ["PUSH_NOTIFICATION"]
    config_keys = ["FCM_SERVER_KEY"]
    required_packages = ["firebase-admin"]
    site_url = "https://firebase.google.com/products/cloud-messaging"
    description_text = "Notifications push mobile Android et iOS (Google Firebase)"

    def validate(self) -> Dict[str, Any]:
        """Valide que le destinataire a un device token FCM"""
        if not self.missive:
            return {"is_valid": False, "error": "Missive non définie"}

        recipient = self.missive.recipient
        if not recipient:
            return {"is_valid": False, "error": "Destinataire non défini"}

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
        Envoie une notification push via FCM.

        TODO: Implémenter l'envoi réel via firebase-admin SDK:
        from firebase_admin import messaging
        """
        validation = self.validate()
        if not validation["is_valid"]:
            self._update_status("FAILED", error_message=validation["error"])
            return {"success": False, "error": validation["error"]}

        # TODO: Implémenter l'envoi réel
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
        Vérifie le statut de livraison.

        Note: FCM fournit des callbacks via webhooks.
        """
        return None
