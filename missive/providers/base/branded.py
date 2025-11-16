"""Generic mixin for app messaging (WhatsApp, Telegram, Slack, Teams, etc.)."""

from typing import Any, Dict, Optional


class BaseBrandedMixin:
    """Generic mixin for ALL app messaging platforms."""

    def send_branded(self, brand_name: Optional[str] = None, **kwargs) -> bool:
        """Sends app message. Auto-dispatches to send_{brand_name}() method."""
        from ...models import MissiveStatus

        target_name = brand_name if brand_name else getattr(self, "name", None)

        if not target_name:
            self._update_status(
                MissiveStatus.FAILED,
                error_message="Provider name or brand_name missing",
            )
            return False

        method_name = f"send_{target_name.lower()}"

        if not hasattr(self, method_name):
            self._update_status(
                MissiveStatus.FAILED,
                error_message=f"{method_name}() method not implemented for this provider",
            )
            return False

        result = getattr(self, method_name)(**kwargs)
        return bool(result)  # type: ignore[no-any-return]

    def get_branded_service_info(
        self, brand_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Gets messaging service info. Auto-dispatches to get_{brand_name}_service_info()."""
        target_name = brand_name if brand_name else getattr(self, "name", None)

        if not target_name:
            return {
                "credits": None,
                "is_available": None,
                "limits": {},
                "warnings": ["Provider name or brand_name missing"],
                "details": {},
            }

        method_name = f"get_{target_name.lower()}_service_info"

        if hasattr(self, method_name):
            result = getattr(self, method_name)()
            return result if isinstance(result, dict) else {}  # type: ignore[no-any-return]

        return {
            "credits": None,
            "is_available": None,
            "limits": {},
            "warnings": [f"{method_name}() method not implemented for this provider"],
            "details": {},
        }

    def check_branded_delivery_status(
        self, brand_name: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """Checks branded message delivery status. Auto-dispatches to check_{brand_name}_delivery_status()."""
        target_name = brand_name if brand_name else getattr(self, "name", None)

        if not target_name:
            return {
                "status": "unknown",
                "delivered_at": None,
                "read_at": None,
                "error_code": None,
                "error_message": "Provider name or brand_name missing",
                "details": {},
            }

        method_name = f"check_{target_name.lower()}_delivery_status"

        try:
            result = getattr(self, method_name)(**kwargs)
            return result if isinstance(result, dict) else {}  # type: ignore[no-any-return]

        except AttributeError:
            return {
                "status": "unknown",
                "delivered_at": None,
                "read_at": None,
                "error_code": None,
                "error_message": f"{method_name}() method not implemented",
                "details": {},
            }

    def _get_organization_context(self) -> Optional[Dict[str, Any]]:
        """Retrieves organization context from missive metadata."""
        if not self.missive or not self.missive.metadata:
            return None

        metadata = self.missive.metadata
        context = {}

        for key in [
            "workspace_id",
            "team_id",
            "channel_id",
            "organization_id",
            "server_id",
            "guild_id",
            "chat_id",
        ]:
            if key in metadata:
                context[key] = metadata[key]

        return context if context else None

    def cancel_branded(self, brand_name: Optional[str] = None, **kwargs) -> bool:
        """Cancels branded message. Auto-dispatches to cancel_{brand_name}() method."""
        target_name = brand_name if brand_name else getattr(self, "name", None)

        if not target_name:
            return False

        # Automatic dispatch to cancel_{target_name}()
        method_name = f"cancel_{target_name.lower()}"

        if hasattr(self, method_name):
            result = getattr(self, method_name)()
            return bool(result)  # type: ignore[no-any-return]

        # Par défaut, retourne False si la méthode n'est pas implémentée
        return False
