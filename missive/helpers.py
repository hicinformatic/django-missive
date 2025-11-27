"""Helper functions for missive creation and provider administration."""

import importlib
import inspect
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from python_missive.helpers import (
    get_provider_paths_from_config as pm_get_provider_paths_from_config,
)
from python_missive.helpers import (
    get_providers_from_config as pm_get_providers_from_config,
)
from python_missive.providers import (
    get_provider_name_from_path as pm_get_provider_name_from_path,
)

from .models import Missive, MissivePriority, MissiveType
from .providers import normalize_provider_path

if TYPE_CHECKING:
    from django.contrib.auth.models import User as UserType
else:
    UserType = get_user_model()

SenderInput = Union["UserType", Dict[str, Any], None]
logger = logging.getLogger(__name__)


class MissiveBuilder:
    """Builder to create missives linked to any object."""

    @staticmethod
    def from_object(
        source_object: Any,
        sender: SenderInput,
        missive_type: str,
        subject: str,
        body: str,
        body_text: Optional[str] = None,
        recipient_user: Optional["UserType"] = None,
        recipient_email: Optional[str] = None,
        recipient_phone: Optional[str] = None,
        recipient_address: Optional[str] = None,
        recipient_name: Optional[str] = None,
        priority: str = MissivePriority.NORMAL.value,  # type: ignore[attr-defined]
        is_registered: bool = False,
        requires_signature: bool = False,
        scheduled_at: Optional[Any] = None,
        metadata: Optional[Dict] = None,
        **kwargs,
    ) -> Missive:
        """Creates a missive linked to a source object."""
        # Extract sender data
        sender_data = MissiveBuilder._extract_sender_data(sender)

        # Extract recipient data
        recipient_data = MissiveBuilder._extract_recipient_data(
            recipient_user,
            recipient_email,
            recipient_phone,
            recipient_address,
            recipient_name,
        )

        missive = Missive(
            content_object=source_object,
            missive_type=missive_type,
            subject=subject,
            body=body,
            body_text=body_text or body,
            recipient_user=recipient_user,
            priority=priority,
            is_registered=is_registered,
            requires_signature=requires_signature,
            scheduled_at=scheduled_at,
            metadata=metadata or {},
            **sender_data,
            **recipient_data,
            **kwargs,
        )
        missive.save()
        return missive

    @staticmethod
    def get_missives_for_object(obj: Any):
        """
        Return every missive linked to the provided object.

        Example:
            order = Order.objects.get(id=123)
            missives = MissiveBuilder.get_missives_for_object(order)

            for missive in missives:
                print(f"{missive.subject} - {missive.status}")
        """
        from django.contrib.contenttypes.models import ContentType

        content_type = ContentType.objects.get_for_model(obj)
        return Missive.objects.filter(content_type=content_type, object_id=obj.pk)

    @staticmethod
    def create_notification(
        source_object: Any,
        sender: SenderInput,
        recipient_user: "UserType",
        subject: str,
        body: str,
        priority: str = MissivePriority.NORMAL.value,  # type: ignore[attr-defined]
        metadata: Optional[Dict] = None,
    ) -> Missive:
        """
        Convenience helper to create an in-app notification.

        Example:
            MissiveBuilder.create_notification(
                source_object=comment,
                sender=comment.author,
                recipient_user=post.author,
                subject="New comment",
                body=f"{comment.author} commented on your post"
            )
        """
        return MissiveBuilder.from_object(
            source_object=source_object,
            sender=sender,
            missive_type=MissiveType.NOTIFICATION.value,  # type: ignore[attr-defined]
            recipient_user=recipient_user,
            subject=subject,
            body=body,
            priority=priority,
            metadata=metadata,
        )

    @staticmethod
    def create_email(
        source_object: Any,
        sender: SenderInput,
        recipient_email: str,
        subject: str,
        body: str,
        body_text: Optional[str] = None,
        is_registered: bool = False,
        priority: str = MissivePriority.NORMAL.value,  # type: ignore[attr-defined]
        metadata: Optional[Dict] = None,
    ) -> Missive:
        """
        Convenience helper to create an email missive.

        Example:
            MissiveBuilder.create_email(
                source_object=invoice,
                sender=request.user,
                recipient_email=invoice.customer_email,
                subject=f"Invoice #{invoice.number}",
                body="Please find your invoice attached...",
                is_registered=True
            )
        """
        return MissiveBuilder.from_object(
            source_object=source_object,
            sender=sender,
            missive_type=MissiveType.EMAIL.value,  # type: ignore[attr-defined]
            recipient_email=recipient_email,
            subject=subject,
            body=body,
            body_text=body_text,
            is_registered=is_registered,
            priority=priority,
            metadata=metadata,
        )

    @staticmethod
    def create_sms(
        source_object: Any,
        sender: SenderInput,
        recipient_phone: str,
        subject: str,
        body: str,
        priority: str = MissivePriority.NORMAL.value,  # type: ignore[attr-defined]
        metadata: Optional[Dict] = None,
    ) -> Missive:
        """
        Convenience helper to create an SMS missive.

        Example:
            MissiveBuilder.create_sms(
                source_object=appointment,
                sender=system_user,
                recipient_phone=appointment.patient_phone,
                subject="Appointment reminder",
                body=f"Reminder tomorrow at {appointment.time}",
                priority=MissivePriority.HIGH.value  # type: ignore[attr-defined]
            )
        """
        return MissiveBuilder.from_object(
            source_object=source_object,
            sender=sender,
            missive_type=MissiveType.SMS.value,  # type: ignore[attr-defined]
            recipient_phone=recipient_phone,
            subject=subject,
            body=body,
            body_text=body,  # For SMS we reuse the plain body content
            priority=priority,
            metadata=metadata,
        )

    @staticmethod
    def _extract_user_data(user: "UserType") -> Dict[str, Any]:
        """Extract data from a Django user."""
        return {
            "name": (
                (user.get_full_name() if hasattr(user, "get_full_name") else "")
                or getattr(user, "username", str(user))
            ),
            "email": getattr(user, "email", None),
        }

    @staticmethod
    def _extract_sender_data(sender: SenderInput) -> Dict[str, Any]:
        """Extract sender data from various input types."""
        if sender is None:
            return {}

        if isinstance(sender, dict):
            # Already a dict with sender fields
            return {
                "sender_name": sender.get("name", ""),
                "sender_email": sender.get("email"),
                "sender_phone": sender.get("phone"),
                "sender_address_line1": sender.get("address_line1", ""),
                "sender_address_line2": sender.get("address_line2", ""),
                "sender_address_line3": sender.get("address_line3", ""),
                "sender_postal_code": sender.get("postal_code", ""),
                "sender_city": sender.get("city", ""),
                "sender_state": sender.get("state", ""),
                "sender_country": sender.get("country", "FR"),
            }

        # Assume it's a User
        user_data = MissiveBuilder._extract_user_data(sender)
        return {
            "sender_name": user_data.get("name", ""),
            "sender_email": user_data.get("email"),
        }

    @staticmethod
    def _extract_recipient_data(
        recipient_user: Optional["UserType"],
        recipient_email: Optional[str],
        recipient_phone: Optional[str],
        recipient_address: Optional[str],
        recipient_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Extract recipient data from various input types."""
        data: Dict[str, Any] = {}

        if recipient_user is not None:
            user_data = MissiveBuilder._extract_user_data(recipient_user)
            data["recipient_name"] = recipient_name or user_data.get("name", "")
            data["recipient_email"] = recipient_email or user_data.get("email")
        else:
            data["recipient_name"] = recipient_name or ""
            data["recipient_email"] = recipient_email

        data["recipient_phone"] = recipient_phone

        # Parse address if provided as string
        if recipient_address:
            # Simple parsing: assume format "line1\nline2\npostal_code city"
            address_lines = recipient_address.split("\n")
            if len(address_lines) > 0:
                data["recipient_address_line1"] = address_lines[0]
            if len(address_lines) > 1:
                data["recipient_address_line2"] = address_lines[1]
            if len(address_lines) > 2:
                data["recipient_address_line3"] = address_lines[2]
            if len(address_lines) > 3:
                # Try to parse postal code and city
                last_line = address_lines[-1].strip()
                parts = last_line.split()
                if parts:
                    # Assume last part is city, rest is postal code
                    data["recipient_postal_code"] = (
                        " ".join(parts[:-1]) if len(parts) > 1 else ""
                    )
                    data["recipient_city"] = parts[-1] if parts else ""

        return data


def get_missives_stats_for_object(obj: Any) -> Dict[str, int]:
    """
    Return aggregated stats for all missives linked to the provided object.
    """
    from .models import MissiveStatus

    missives = MissiveBuilder.get_missives_for_object(obj)

    return {
        "total": missives.count(),
        "draft": missives.filter(status=MissiveStatus.DRAFT).count(),
        "pending": missives.filter(status=MissiveStatus.PENDING).count(),
        "sent": missives.filter(status=MissiveStatus.SENT).count(),
        "delivered": missives.filter(status=MissiveStatus.DELIVERED).count(),
        "read": missives.filter(status=MissiveStatus.READ).count(),
        "failed": missives.filter(status=MissiveStatus.FAILED).count(),
        "cancelled": missives.filter(status=MissiveStatus.CANCELLED).count(),
    }


# ==============================================================================
# Provider admin helpers
# ==============================================================================


DEFAULT_PROVIDERS_BY_TYPE: Dict[str, list[str]] = {}
DEFAULT_PROVIDER_PATHS_BY_TYPE: Dict[str, list[str]] = {}


def _normalize_providers_config() -> Optional[list[str]]:
    """
    Normalize `settings.MISSIVE_PROVIDERS` into a list of python_missive paths.

    Legacy configs sometimes stored a dict grouped by missive type. In that case
    we flatten the values while preserving order.
    """
    providers_config = getattr(settings, "MISSIVE_PROVIDERS", None)
    if not providers_config:
        return None

    normalized: list[str] = []

    if isinstance(providers_config, dict):
        groups = [list(value) for value in providers_config.values()]
    else:
        groups = [list(providers_config)]

    for value in groups:
        for provider_path in value:
            normalized_path = normalize_provider_path(provider_path)
            if normalized_path not in normalized:
                normalized.append(normalized_path)

    return normalized or None


def _provider_error_logger(provider_path: str, exc: Exception) -> None:
    logger.warning("Could not load provider %s: %s", provider_path, exc)


def get_providers_from_config():
    """
    Read `MISSIVE_PROVIDERS` from Django settings and build
    `{missive_type: [short_provider_name]}`.

    Configuration example with automatic categorization:
        MISSIVE_PROVIDERS = [
            "python_missive.providers.twilio.TwilioProvider",
            "python_missive.providers.sendgrid.SendGridProvider",
        ]

    Every provider is categorized according to its `supported_types`.
    """
    normalized_config = _normalize_providers_config()
    providers_by_type = pm_get_providers_from_config(
        normalized_config, on_error=_provider_error_logger
    )

    if not providers_by_type:
        raise ImproperlyConfigured(
            "MISSIVE_PROVIDERS must declare at least one provider."
        )

    return providers_by_type


def get_provider_paths_from_config():
    """
    Same as `get_providers_from_config()` but return fully qualified class
    paths instead of short names.

    Used by `MissiveSender` during failover resolution.
    """
    normalized_config = _normalize_providers_config()
    providers_by_type = pm_get_provider_paths_from_config(
        normalized_config, on_error=_provider_error_logger
    )

    if not providers_by_type:
        raise ImproperlyConfigured(
            "MISSIVE_PROVIDERS must declare at least one provider path."
        )

    return providers_by_type


# Re-export python-missive helper for backward compatibility
get_provider_name_from_path = pm_get_provider_name_from_path


def discover_providers():
    """
    Discover legacy providers inside `missive/providers/` and return a
    mapping `{short_name: display_name}` for admin dropdowns.
    """
    providers_dict = {}

    # Add special "custom" provider
    providers_dict["custom"] = _("Custom Provider")

    # Look for legacy local providers
    providers_dir = Path(__file__).parent / "providers"

    if not providers_dir.exists():
        return providers_dict

    # Iterate over every python file in the folder
    for file_path in providers_dir.glob("*.py"):
        # Ignore __init__.py and private files
        if file_path.name.startswith("_"):
            continue

        module_name = file_path.stem  # Nom du fichier sans .py

        try:
            # Importer dynamiquement le module
            module = importlib.import_module(f"missive.providers.{module_name}")

            # Search for all classes that inherit from BaseProvider
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Ensure the provider class is defined in this module
                if (
                    name.endswith("Provider")
                    and hasattr(obj, "name")
                    and obj.__module__ == f"missive.providers.{module_name}"
                ):
                    # Use the module name (file) as identifier, not obj.name
                    provider_name = module_name.lower()

                    # Get display_name or fallback to name
                    if hasattr(obj, "display_name"):
                        display_name = obj.display_name
                    else:
                        display_name = (
                            obj.name
                            if hasattr(obj, "name")
                            else module_name.capitalize()
                        )

                    providers_dict[provider_name] = display_name
                    break  # Une seule classe provider par fichier

        except (ImportError, AttributeError):
            # Silently ignore import errors (missing dependencies, etc.)
            continue

    return providers_dict


def get_all_provider_choices():
    """
    Generate the list of all available providers for form choices.
    Uses automatic provider discovery from their classes.
    """
    providers_by_type = get_providers_from_config()
    all_providers = set()

    # Collect all unique provider short names
    for providers in providers_by_type.values():
        all_providers.update(providers)

    # Automatically discover display_name from provider classes
    providers_display = discover_providers()

    # Create sorted choices
    choices = []
    for provider in sorted(all_providers):
        # Use discovered display_name or fallback to capitalized name
        label = providers_display.get(provider, provider.capitalize())
        choices.append((provider, label))

    return choices


# ==============================================================================
# Delayed send helpers
# ==============================================================================


def send_delayed_missives(
    max_missives: Optional[int] = None,
    skip_health_check: bool = False,
    enable_fallback: bool = True,
) -> Dict[str, Any]:
    """
    Send all missives that have reached their delayed_send_at datetime.

    This function is designed to be called by any queue backend (Celery, RQ, etc.)
    as a periodic task.

    Args:
        max_missives: Maximum number of missives to process in one run.
                     If None, processes all eligible missives.
        skip_health_check: Whether to skip provider health checks (faster but less safe).
        enable_fallback: Whether to enable automatic provider fallback on failure.

    Returns:
        dict: Summary with keys:
            - 'processed': Total number of missives processed
            - 'success': Number of successfully sent missives
            - 'failed': Number of failed missives
            - 'errors': List of error details (missive_id, error message)

    Example with Celery:
        @shared_task
        def send_delayed_missives_task():
            from missive.helpers import send_delayed_missives
            return send_delayed_missives(max_missives=100)

    Example with RQ:
        from missive.helpers import send_delayed_missives
        job = queue.enqueue(send_delayed_missives, max_missives=50)
    """
    from .models import MissiveStatus
    from .sender import MissiveSender

    now = timezone.now()

    # Find missives that should be sent now
    queryset = Missive.objects.filter(
        delayed_send_at__isnull=False,
        delayed_send_at__lte=now,
        status__in=[MissiveStatus.DRAFT, MissiveStatus.PENDING],
    ).order_by("delayed_send_at", "priority", "created_at")

    if max_missives:
        queryset = queryset[:max_missives]

    missives = list(queryset)
    total = len(missives)

    if total == 0:
        logger.info("No delayed missives to send")
        return {
            "processed": 0,
            "success": 0,
            "failed": 0,
            "errors": [],
        }

    logger.info(f"Processing {total} delayed missive(s)")

    results: Dict[str, Any] = {
        "processed": total,
        "success": 0,
        "failed": 0,
        "errors": [],
    }

    for missive in missives:
        try:
            logger.info(
                f"Processing delayed missive {missive.id} "
                f"(delayed_send_at={missive.delayed_send_at})"
            )

            success = MissiveSender.send(
                missive,
                skip_health_check=skip_health_check,
                enable_fallback=enable_fallback,
            )

            if success:
                results["success"] += 1
                logger.info(f"Successfully sent delayed missive {missive.id}")
            else:
                results["failed"] += 1
                error_msg = f"Send returned False for missive {missive.id}"
                results["errors"].append({"missive_id": missive.id, "error": error_msg})
                logger.warning(error_msg)

        except Exception as e:
            results["failed"] += 1
            error_msg = str(e)
            results["errors"].append({"missive_id": missive.id, "error": error_msg})
            logger.error(
                f"Error sending delayed missive {missive.id}: {error_msg}",
                exc_info=True,
            )

    logger.info(
        f"Delayed send completed: {results['success']} success, "
        f"{results['failed']} failed out of {results['processed']} processed"
    )

    return results
