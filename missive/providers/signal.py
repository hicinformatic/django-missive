"""Signal Messenger provider."""

from typing import Any, Dict, Optional

from .base import BaseProvider


class SignalProvider(BaseProvider):
    """
    Signal Messenger provider.

    Required configuration:
        SIGNAL_CLI_REST_API_URL: signal-cli-rest-api URL
        SIGNAL_SENDER_NUMBER: Registered sender number

    Recipient must have a mobile phone number.
    """

    name = "signal"
    display_name = "Signal"
    supported_types = ["BRANDED"]
    brands = ["signal"]  # Signal uniquement
    config_keys = ["SIGNAL_API_KEY"]
    required_packages = ["requests"]
    site_url = "https://signal.org/"
    description_text = "Secure end-to-end encrypted messaging"

    def validate(self) -> Dict[str, Any]:
        """Validate that the recipient has a mobile number"""
        if not self.missive:
            return {"is_valid": False, "error": "Missive not defined"}

        recipient = self.missive.recipient
        if not recipient or not recipient.mobile:
            return {
                "is_valid": False,
                "error": "Recipient must have a mobile number for Signal",
            }

        return {"is_valid": True}

    def send(self) -> Dict[str, Any]:
        """
        Send a message via Signal.

        TODO: Implement actual sending via signal-cli-rest-api
        """
        validation = self.validate()
        if not validation["is_valid"]:
            self._update_status("FAILED", error_message=validation["error"])
            return {"success": False, "error": validation["error"]}

        # TODO: Implement actual sending
        self._update_status(
            "SENT",
            external_id=f"signal_sim_{self.missive.id}",
        )

        return {
            "success": True,
            "message_id": f"signal_sim_{self.missive.id}",
        }

    def check_status(self, external_id: Optional[str] = None) -> Optional[str]:
        """Check status of a Signal message"""
        # TODO: Implement if needed
        return None
