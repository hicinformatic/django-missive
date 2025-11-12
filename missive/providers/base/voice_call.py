"""Voice call provider mixin."""

from typing import Any, Dict


class BaseVoiceCallMixin:
    """Voice call-specific functionality mixin."""

    def get_voice_call_service_info(self) -> Dict[str, Any]:
        """Returns voice call service info. Override in subclasses."""
        return {
            "credits": None,
            "credits_type": "time",
            "is_available": None,
            "limits": {},
            "warnings": [
                "get_voice_call_service_info() method not implemented for this provider"
            ],
            "options": [],
            "details": {},
        }

    def check_voice_call_delivery_status(self, **kwargs) -> Dict[str, Any]:
        """Checks voice call delivery status. Override in subclasses."""
        return {
            "status": "unknown",
            "delivered_at": None,
            "duration": None,
            "error_code": None,
            "error_message": "check_voice_call_delivery_status() method not implemented for this provider",
            "details": {},
        }

    def send_voice_call(self, **kwargs) -> bool:
        """Sends voice call. Override in subclasses."""
        from ...models import MissiveStatus

        if not self.missive.get_recipient_phone():
            self._update_status(
                MissiveStatus.FAILED, error_message="No phone number"
            )
            return False

        raise NotImplementedError(
            f"{self.name} must implement the send_voice_call() method"
        )

    def cancel_voice_call(self, **kwargs) -> bool:
        """Cancels scheduled voice call. Override in subclasses."""
        return False
