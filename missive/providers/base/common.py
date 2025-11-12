"""Common provider functionality."""

from typing import Any, Dict, Optional

from django.conf import settings
from django.utils import timezone

from ...models import Missive, MissiveEvent, MissiveStatus


class BaseProviderCommon:
    """Base provider with common functionality."""

    name = "Base"
    supported_types = []
    services = []
    brands = []
    config_keys = []
    required_packages = []
    status_url = None
    documentation_url = None
    site_url = None
    description_text = None

    def __init__(self, missive: Optional[Missive] = None):
        """Initializes provider with optional missive."""
        self.missive = missive
        self.config = self._get_config()

    def _get_config(self) -> Dict[str, Any]:
        """Gets provider config from Django settings."""
        config = {}
        for key in self.config_keys:
            value = getattr(settings, key, None)
            if value is not None:
                config[key] = value
        return config

    def supports(self, missive_type: str) -> bool:
        """Checks if provider supports this missive type."""
        return missive_type in self.supported_types

    def has_service(self, service: str) -> bool:
        """Checks if provider offers this service."""
        return service in self.services

    def _update_status(
        self,
        status: MissiveStatus,
        provider: str = None,
        external_id: str = None,
        error_message: str = None,
    ):
        """Updates missive status and creates event."""
        if not self.missive:
            return

        self.missive.status = status
        if provider:
            self.missive.provider = provider
        if external_id:
            self.missive.external_id = external_id
        if error_message:
            self.missive.error_message = error_message

        if status == MissiveStatus.SENT:
            self.missive.sent_at = timezone.now()
        elif status == MissiveStatus.DELIVERED:
            self.missive.delivered_at = timezone.now()
        elif status == MissiveStatus.READ:
            self.missive.read_at = timezone.now()

        self.missive.save()

    def _create_event(
        self,
        event_type: str,
        description: str = "",
        status: Optional[MissiveStatus] = None,
        metadata: Dict = None,
    ):
        """Creates tracking event."""
        if not self.missive:
            return

        MissiveEvent.objects.create(
            missive=self.missive,
            event_type=event_type,
            provider=self.name,
            description=description,
            status=status,
            metadata=metadata or {},
        )

    def get_status_from_event(self, event_type: str) -> Optional[MissiveStatus]:
        """Maps event type to MissiveStatus."""
        event_mapping = {
            "delivered": MissiveStatus.DELIVERED,
            "opened": MissiveStatus.READ,
            "clicked": MissiveStatus.READ,
            "read": MissiveStatus.READ,
            "bounced": MissiveStatus.FAILED,
            "failed": MissiveStatus.FAILED,
            "rejected": MissiveStatus.FAILED,
            "dropped": MissiveStatus.FAILED,
        }
        return event_mapping.get(event_type.lower())

    def get_proofs_of_delivery(self, service_type: Optional[str] = None) -> list:
        """Returns list of delivery proofs for the missive."""
        if not self.missive:
            return []

        if not service_type:
            service_type = self._detect_service_type()

        return []

    def _detect_service_type(self) -> str:
        """Detects service type from missive."""
        if not self.missive:
            return "unknown"

        missive_type = self.missive.missive_type

        if missive_type == "LRE":
            return "lre"
        elif missive_type == "POSTAL":
            if self.missive.is_registered:
                return "postal_registered"
            return "postal"
        elif missive_type == "EMAIL":
            if self.missive.is_registered:
                return "email_ar"
            return "email"
        elif missive_type == "SMS":
            return "sms"
        elif missive_type == "BRANDED":
            return self.name.lower() if hasattr(self, "name") else "branded"
        elif missive_type == "RCS":
            return "rcs"

        return missive_type.lower()

    def list_available_proofs(self) -> Dict[str, bool]:
        """
        List all available proof types for this missive.

        Returns:
            Dict {service_type: available}

        Example:
            {
                "lre": True,
                "deposit_certificate": True,
                "delivery_receipt": False,
            }
        """
        if not self.missive:
            return {}

        service_type = self._detect_service_type()

        proof_services = {"lre", "postal_registered", "postal_signature", "email_ar"}

        return {service_type: service_type in proof_services}

    def get_service_status(self) -> Dict[str, Any]:
        """Returns provider service status. Override in subclasses."""
        return {
            "status": "unknown",
            "is_available": None,
            "services": self.services,
            "credits": None,
            "rate_limits": {},
            "sla": {},
            "last_check": timezone.now(),
            "warnings": [
                "get_service_status() method not implemented for this provider"
            ],
            "details": {},
        }
