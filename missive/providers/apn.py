"""
Provider APN (Apple Push Notification) pour notifications push iOS.

Documentation: https://developer.apple.com/documentation/usernotifications
"""

from typing import Any, Dict, Optional

from .base import BaseProvider


class APNProvider(BaseProvider):
    """
    Provider pour Apple Push Notification Service.

    Configuration requise:
        APN_CERTIFICATE_PATH: Chemin vers le certificat .pem
        APN_KEY_ID: Key ID (pour auth par token)
        APN_TEAM_ID: Team ID Apple
        APN_BUNDLE_ID: Bundle ID de l'app
        APN_USE_SANDBOX: True pour développement, False pour production

    Le destinataire doit avoir un device_token APN stocké dans metadata.
    """

    name = "apn"
    display_name = "Apple Push Notification"
    supported_types = ["PUSH_NOTIFICATION"]
    config_keys = ["APN_CERTIFICATE_PATH", "APN_KEY_ID", "APN_TEAM_ID"]
    required_packages = ["aioapns"]
    site_url = "https://developer.apple.com/documentation/usernotifications"
    description_text = "Notifications push iOS natives via APNs (Apple)"

    def validate(self) -> Dict[str, Any]:
        """Valide que le destinataire a un device token APN"""
        if not self.missive:
            return {"is_valid": False, "error": "Missive non définie"}

        recipient = self.missive.recipient
        if not recipient:
            return {"is_valid": False, "error": "Destinataire non défini"}

        device_token = (
            recipient.metadata.get("apn_device_token") if recipient.metadata else None
        )
        if not device_token:
            return {
                "is_valid": False,
                "error": "Le destinataire n'a pas de device token APN (ajouter dans metadata)",
            }

        return {"is_valid": True}

    def send(self) -> Dict[str, Any]:
        """
        Envoie une notification push via APN.

        TODO: Implémenter l'envoi réel via aioapns ou PyAPNs
        """
        validation = self.validate()
        if not validation["is_valid"]:
            self._update_status("FAILED", error_message=validation["error"])
            return {"success": False, "error": validation["error"]}

        # TODO: Implémenter l'envoi réel
        # from aioapns import APNs, NotificationRequest
        # apns = APNs(...)
        # request = NotificationRequest(
        #     device_token=device_token,
        #     message={
        #         "aps": {
        #             "alert": {
        #                 "title": self.missive.subject,
        #                 "body": self.missive.body_text[:100],
        #             },
        #             "sound": "default",
        #         }
        #     }
        # )

        self._update_status(
            "SENT",
            external_id=f"apn_sim_{self.missive.id}",
        )

        return {
            "success": True,
            "apns_id": f"apn_sim_{self.missive.id}",
        }

    def check_status(self, external_id: Optional[str] = None) -> Optional[str]:
        """Vérifie le statut de livraison APN"""
        # APN ne fournit pas de confirmation de livraison par défaut
        return None
