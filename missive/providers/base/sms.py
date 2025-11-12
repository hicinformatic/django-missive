"""SMS provider mixin."""

import re
from typing import Any, Dict


class BaseSMSMixin:
    """SMS-specific functionality mixin."""

    def get_sms_service_info(self) -> Dict[str, Any]:
        """Returns SMS service info. Override in subclasses."""
        return {
            "credits": None,
            "credits_type": "count",
            "is_available": None,
            "limits": {},
            "warnings": [
                "get_sms_service_info() method not implemented for this provider"
            ],
            "details": {},
        }

    def check_sms_delivery_status(self, **kwargs) -> Dict[str, Any]:
        """Checks SMS delivery status. Override in subclasses."""
        return {
            "status": "unknown",
            "delivered_at": None,
            "error_code": None,
            "error_message": "check_sms_delivery_status() method not implemented for this provider",
            "details": {},
        }

    def send_sms(self, **kwargs) -> bool:
        """Sends SMS. Override in subclasses."""
        from ...models import MissiveStatus

        if not self.missive.get_recipient_phone():
            self._update_status(
                MissiveStatus.FAILED, error_message="No phone number"
            )
            return False

        raise NotImplementedError(f"{self.name} must implement the send_sms() method")

    def validate_phone_number(
        self, phone: str, country_code: str = "FR"
    ) -> Dict[str, Any]:
        """Validates phone number and assesses delivery risk."""
        warnings = []
        details = {}

        cleaned = re.sub(r"[^\d+]", "", phone)
        details["cleaned"] = cleaned

        if not cleaned.startswith("+"):
            warnings.append("International format recommended (+33...)")

        risk_score = len(warnings) * 20

        return {
            "is_valid": len(cleaned) >= 10,  # Validation basique
            "is_mobile": None,  # Nécessite phonenumbers
            "formatted": cleaned,
            "carrier": "",
            "line_type": "unknown",
            "risk_score": risk_score,
            "warnings": warnings,
        }

    def calculate_sms_segments(self, message: str) -> Dict[str, Any]:
        """
        Calculate the number of SMS segments and estimated cost.

        A standard SMS is 160 characters (GSM-7) or 70 (Unicode).
        Longer messages are split into segments.

        Args:
            message: The SMS message

        Returns:
            Dict containing:
            - segments (int): Number of segments
            - characters (int): Number of characters
            - encoding (str): GSM-7 or Unicode
            - estimated_cost (float): Estimated cost (according to config)
            - per_segment_limit (int): Character limit per segment

        Example:
            info = provider.calculate_sms_segments("Your SMS message")
            print(f"Will cost {info['segments']} segment(s)")
        """
        # Encoding detection
        gsm7_chars = set(
            "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?"
            "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà"
        )

        is_gsm7 = all(c in gsm7_chars for c in message)
        encoding = "GSM-7" if is_gsm7 else "Unicode"

        # Limits per segment
        if is_gsm7:
            single_limit = 160
            multi_limit = 153  # For multi-segment messages
        else:
            single_limit = 70
            multi_limit = 67

        # Calculate number of segments
        length = len(message)
        if length == 0:
            segments = 0
        elif length <= single_limit:
            segments = 1
        else:
            segments = (length + multi_limit - 1) // multi_limit

        # Coût estimé (à configurer selon provider)
        cost_per_segment = self.config.get("SMS_COST_PER_SEGMENT", 0.05)
        estimated_cost = segments * cost_per_segment

        return {
            "segments": segments,
            "characters": length,
            "encoding": encoding,
            "estimated_cost": estimated_cost,
            "per_segment_limit": single_limit if segments == 1 else multi_limit,
            "is_multipart": segments > 1,
        }

    def format_phone_international(self, phone: str, country_code: str = "FR") -> str:
        """
        Format a phone number in international format.

        Args:
            phone: Phone number
            country_code: Default country code

        Returns:
            str: Formatted number (+33...)

        Example:
            formatted = provider.format_phone_international("0612345678", "FR")
            # → "+33612345678"
        """
        # Nettoyage
        cleaned = re.sub(r"[^\d+]", "", phone)

        # Déjà en format international
        if cleaned.startswith("+"):
            return cleaned

        # TODO: Implement with phonenumbers
        # import phonenumbers
        # parsed = phonenumbers.parse(phone, country_code)
        # return phonenumbers.format_number(
        #     parsed, phonenumbers.PhoneNumberFormat.E164
        # )

        # Simple conversion for France
        if country_code == "FR" and cleaned.startswith("0"):
            return "+33" + cleaned[1:]

        return "+" + cleaned

    def cancel_sms(self, **kwargs) -> bool:
        """
        Cancel sending of a scheduled SMS.

        Args:
            **kwargs: Provider-specific options

        Base method that returns False. Providers that support
        cancellation must override this method with their API implementation.

        Returns:
            bool: True if cancellation succeeded, False otherwise

        Example:
            if provider.cancel_sms():
                print("SMS cancelled successfully")
        """
        return False
