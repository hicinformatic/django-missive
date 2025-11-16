"""Base provider with all features (composition of mixins)."""

from typing import Any, Dict, Optional, Tuple

from django.utils import timezone

from ...models import Missive
from .branded import BaseBrandedMixin
from .common import BaseProviderCommon
from .email import BaseEmailMixin
from .monitoring import BaseMonitoringMixin
from .notification import BaseNotificationMixin
from .postal import BasePostalMixin
from .sms import BaseSMSMixin
from .voice_call import BaseVoiceCallMixin


class BaseProvider(
    BaseProviderCommon,
    BaseEmailMixin,
    BaseSMSMixin,
    BasePostalMixin,
    BaseNotificationMixin,
    BaseVoiceCallMixin,
    BaseMonitoringMixin,
    BaseBrandedMixin,
):
    """
    Base class for all providers.

    Inherits all mixins to support all missive types. Concrete providers
    inherit this class and implement only the send_* methods they need.

    To implement in subclasses:
    - name: Provider name
    - supported_types: List of supported MissiveType
    - send_email() / send_sms() / send_postal() / send_notification() / send_voice_call()
    - send_{name}() for BRANDED type (e.g., send_whatsapp, send_slack)
    - handle_webhook(): Process webhooks
    """

    def send(self) -> bool:
        """Sends missive by dispatching to the appropriate method based on type."""
        if not self.missive:
            return False

        from ...models import MissiveStatus

        if not self.supports(self.missive.missive_type):
            error = (
                f"{self.name} does not support {self.missive.get_missive_type_display()}"
            )
            self._update_status(MissiveStatus.FAILED, error_message=error)  # type: ignore[arg-type]
            return False

        from ...models import MissiveType

        if self.missive.missive_type == MissiveType.EMAIL:
            return self.send_email()
        elif self.missive.missive_type == MissiveType.SMS:
            return self.send_sms()
        elif self.missive.missive_type == MissiveType.POSTAL:
            return self.send_postal()
        elif self.missive.missive_type == MissiveType.NOTIFICATION:
            return self.send_notification()
        elif self.missive.missive_type == MissiveType.VOICE_CALL:
            return self.send_voice_call()
        elif self.missive.missive_type == MissiveType.BRANDED:
            return self.send_branded()

        return False

    def cancel(self) -> bool:
        """Cancels missive by dispatching to appropriate cancel method."""
        if not self.missive:
            return False

        if not self.missive.external_id:
            return False

        from ...models import MissiveType

        if self.missive.missive_type == MissiveType.EMAIL:
            return self.cancel_email()
        elif self.missive.missive_type == MissiveType.SMS:
            return self.cancel_sms()
        elif self.missive.missive_type == MissiveType.POSTAL:
            return self.cancel_postal()
        elif self.missive.missive_type == MissiveType.NOTIFICATION:
            return self.cancel_notification()
        elif self.missive.missive_type == MissiveType.VOICE_CALL:
            return self.cancel_voice_call()
        elif self.missive.missive_type == MissiveType.BRANDED:
            return self.cancel_branded()

        return False

    def handle_webhook(
        self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Tuple[bool, str, Optional[Missive]]:
        """Processes webhook from provider. Returns (success, error, missive)."""
        raise NotImplementedError(
            f"{self.name} must implement the handle_webhook() method"
        )

    def validate_webhook_signature(
        self, payload: Any, headers: Dict[str, str]
    ) -> Tuple[bool, str]:
        """Validates webhook signature. Returns (is_valid, error_message)."""
        return True, ""

    def extract_missive_id(self, payload: Dict[str, Any]) -> Optional[str]:
        """Extracts missive external_id from webhook payload."""
        raise NotImplementedError(
            f"{self.name} must implement the extract_missive_id() method"
        )

    def check_service_availability(self) -> Dict[str, Any]:
        """Checks provider service availability and status."""
        return {
            "is_available": None,
            "response_time_ms": 0,
            "quota_remaining": None,
            "status": "unknown",
            "last_check": timezone.now(),
            "warnings": ["Service check not implemented for this provider"],
        }

    def calculate_delivery_risk(
        self, missive: Optional[Missive] = None
    ) -> Dict[str, Any]:
        """Calculates delivery failure risk score (0-100) for a missive."""
        if missive is None:
            missive = self.missive

        if not missive:
            return {
                "risk_score": 100,
                "risk_level": "critical",
                "factors": {},
                "recommendations": ["No missive to analyze"],
                "should_send": False,
            }

        factors = {}
        recommendations = []
        total_risk = 0

        from ...models import MissiveType

        if missive.missive_type == MissiveType.EMAIL:
            email = missive.get_recipient_email()
            if email:
                email_validation = self.validate_email(email)
                factors["email_validation"] = email_validation
                total_risk += email_validation["risk_score"] * 0.6
                if email_validation["warnings"]:
                    recommendations.extend(email_validation["warnings"])

        elif missive.missive_type in [MissiveType.SMS, MissiveType.BRANDED]:
            phone = missive.get_recipient_phone()
            if phone:
                phone_validation = self.validate_phone_number(phone)
                factors["phone_validation"] = phone_validation
                total_risk += phone_validation["risk_score"] * 0.6
                if phone_validation["warnings"]:
                    recommendations.extend(phone_validation["warnings"])

        service_check = self.check_service_availability()
        factors["service_availability"] = service_check
        if not service_check.get("is_available"):
            total_risk += 20
            recommendations.append("Service temporarily unavailable")

        risk_score = min(int(total_risk), 100)

        if risk_score < 25:
            risk_level = "low"
        elif risk_score < 50:
            risk_level = "medium"
        elif risk_score < 75:
            risk_level = "high"
        else:
            risk_level = "critical"

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "factors": factors,
            "recommendations": recommendations,
            "should_send": risk_score < 70,
        }


__all__ = ["BaseProvider"]
