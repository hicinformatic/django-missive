"""Apple Push Notification provider for iOS push notifications."""

from typing import Any, Dict, Optional

from .base import BaseProvider


class APNProvider(BaseProvider):
    """
    Apple Push Notification Service provider.

    Required configuration:
        APN_CERTIFICATE_PATH: Path to .pem certificate
        APN_KEY_ID: Key ID (for token auth)
        APN_TEAM_ID: Apple Team ID
        APN_BUNDLE_ID: App Bundle ID
        APN_USE_SANDBOX: True for development, False for production

    Recipient must have an APN device_token stored in metadata.
    """

    name = "apn"
    display_name = "Apple Push Notification"
    supported_types = ["PUSH_NOTIFICATION"]
    config_keys = ["APN_CERTIFICATE_PATH", "APN_KEY_ID", "APN_TEAM_ID"]
    required_packages = ["aioapns"]
    site_url = "https://developer.apple.com/documentation/usernotifications"
    description_text = "Native iOS push notifications via APNs (Apple)"

    def validate(self) -> Dict[str, Any]:
        """Validate that the recipient has an APN device token"""
        if not self.missive:
            return {"is_valid": False, "error": "Missive not defined"}

        recipient = self.missive.recipient
        if not recipient:
            return {"is_valid": False, "error": "Recipient not defined"}

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
        Send a push notification via APN.

        TODO: Implement actual sending via aioapns or PyAPNs
        """
        validation = self.validate()
        if not validation["is_valid"]:
            self._update_status("FAILED", error_message=validation["error"])
            return {"success": False, "error": validation["error"]}

        # TODO: Implement actual sending
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
        """Check APN delivery status"""
        # APN doesn't provide delivery confirmation by default
        return None
