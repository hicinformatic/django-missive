"""Email provider mixin."""

import re
from typing import Any, Dict, List


class BaseEmailMixin:
    """Email-specific functionality mixin."""

    def get_email_service_info(self) -> Dict[str, Any]:
        """Returns email service info. Override in subclasses."""
        return {
            "credits": None,
            "credits_type": "unlimited",
            "is_available": None,
            "limits": {},
            "warnings": [
                "get_email_service_info() method not implemented for this provider"
            ],
            "reputation": {},
            "details": {},
        }

    def check_email_delivery_status(self, **kwargs) -> Dict[str, Any]:
        """Checks email delivery status. Override in subclasses."""
        return {
            "status": "unknown",
            "delivered_at": None,
            "opened_at": None,
            "clicked_at": None,
            "opens_count": 0,
            "clicks_count": 0,
            "bounce_type": None,
            "error_code": None,
            "error_message": "check_email_delivery_status() method not implemented for this provider",
            "details": {},
        }

    def send_email(self, **kwargs) -> bool:
        """Sends email. Override in subclasses."""
        from ...models import MissiveStatus

        if not self.missive.get_recipient_email():
            self._update_status(
                MissiveStatus.FAILED, error_message="No recipient email"
            )
            return False

        raise NotImplementedError(
            f"{self.name} must implement the send_email() method"
        )

    def validate_email(self, email: str) -> Dict[str, Any]:
        """Validates email and assesses delivery risk."""
        warnings: list[str] = []
        details: dict[str, Any] = {}

        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        is_valid = bool(re.match(email_regex, email))

        if not is_valid:
            return {
                "is_valid": False,
                "is_deliverable": False,
                "risk_score": 100,
                "warnings": ["Invalid email format"],
                "details": {},
            }

        domain = email.split("@")[1].lower()
        details["domain"] = domain

        risk_score = self._calculate_email_risk_score(email, domain, warnings, details)

        return {
            "is_valid": is_valid,
            "is_deliverable": len(warnings) == 0,
            "risk_score": risk_score,
            "warnings": warnings,
            "details": details,
        }

    def _calculate_email_risk_score(
        self, email: str, domain: str, warnings: List[str], details: Dict
    ) -> int:
        """Calculates email risk score (0-100)."""
        score = 0

        if "Disposable domain detected" in warnings:
            score += 80
        if "No MX record found" in warnings:
            score += 60
        if "SMTP server unreachable" in warnings:
            score += 50

        return min(score, 100)

    def test_smtp_server(self, domain: str) -> Dict[str, Any]:
        """Tests SMTP server availability and configuration."""
        return {
            "is_reachable": None,
            "mx_records": [],
            "supports_tls": None,
            "smtp_banner": "",
            "response_time_ms": 0,
            "warnings": ["Test SMTP non implémenté"],
        }

    def add_attachment_email(self, attachment) -> Any:
        """
        Prépare une pièce jointe pour un email.

        Args:
            attachment: Instance de MissiveAttachment

        Returns:
            Objet d'attachment formaté selon le provider
            (ex: tuple (filename, content, mimetype) pour certains providers)
        """
        # Par défaut, retourne un dict standard
        # Les providers concrets peuvent override pour leur format spécifique
        return {
            "filename": attachment.filename,
            "content": attachment.file.read() if attachment.file else None,
            "url": attachment.external_url,
            "mime_type": attachment.mime_type,
        }

    def calculate_spam_score(self, subject: str, body: str) -> Dict[str, Any]:
        """
        Calcule un score de spam pour le contenu d'un email.

        Vérifie :
        - Mots-clés spam courants
        - Ratio majuscules/minuscules
        - Nombre de liens
        - Utilisation excessive de ponctuation

        Args:
            subject: Sujet de l'email
            body: Corps de l'email

        Returns:
            Dict containing:
            - spam_score (int): Score 0-100 (0=safe, 100=spam)
            - triggers (List[str]): Mots/patterns déclencheurs
            - recommendations (List[str]): Conseils d'amélioration
        """
        score = 0
        triggers: list[str] = []
        recommendations: list[str] = []

        # TODO: Implement spam detection
        # - Mots-clés : GRATUIT, URGENT, CLIQUEZ ICI, etc.
        # - Ratio ALL CAPS
        # - Trop de liens
        # - Trop de ! ou ???
        # - Utiliser SpamAssassin ou un service externe

        return {
            "spam_score": score,
            "triggers": triggers,
            "recommendations": recommendations,
        }

    def cancel_email(self, **kwargs) -> bool:
        """
        Cancel sending of a scheduled email.

        Args:
            **kwargs: Provider-specific options

        Base method that returns False. Providers that support
        cancellation must override this method with their API implementation.

        Returns:
            bool: True if cancellation succeeded, False otherwise
        """
        return False
