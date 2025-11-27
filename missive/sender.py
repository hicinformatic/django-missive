"""Missive sending with automatic provider fallback."""

import logging
from typing import Any, Dict, List

from django.utils.module_loading import import_string

from .helpers import get_provider_paths_from_config
from .models import Missive

logger = logging.getLogger(__name__)


class MissiveSender:
    """Sends missives with automatic provider fallback."""

    @staticmethod
    def get_provider_classes(missive: Missive) -> List[str]:
        """Returns ordered list of providers to try (by priority)."""
        # Vérifier d'abord si un provider est explicitement défini via _provider_path
        provider_path = getattr(missive, "_provider_path", None)
        if provider_path:
            logger.info(
                f"Missive {missive.id}: Explicit provider path '{provider_path}'"
            )
            return [provider_path]

        if missive.provider:
            logger.info(f"Missive {missive.id}: Explicit provider '{missive.provider}'")
            return [missive.provider]

        providers_by_type = get_provider_paths_from_config()
        provider_paths = providers_by_type.get(missive.missive_type)

        if provider_paths:
            logger.info(
                f"Missive {missive.id}: Configured providers for {missive.missive_type}: {provider_paths}"
            )
            return list(provider_paths) if provider_paths else []

        raise ValueError(f"No provider configured for {missive.missive_type}")

    @staticmethod
    def is_provider_healthy(provider_class) -> bool:
        """Checks if provider is operational via health check."""
        try:
            provider_instance = provider_class()
            health = provider_instance.health_check()

            is_healthy: bool = bool(health.get("is_healthy", False))
            status = health.get("status", "unknown")

            if not is_healthy:
                logger.warning(
                    f"Provider {provider_class.__name__} is not healthy: "
                    f"status={status}, summary={health.get('summary')}"
                )

            return is_healthy
        except Exception as e:
            logger.error(f"Error during health check of {provider_class.__name__}: {e}")
            return False

    @staticmethod
    def send(
        missive: Missive, skip_health_check: bool = False, enable_fallback: bool = True
    ) -> bool:
        """Sends missive via appropriate provider with automatic fallback."""
        if not missive.can_send():
            logger.warning(f"Missive {missive.id}: Cannot be sent (can_send()=False)")
            return False

        provider_paths = MissiveSender.get_provider_classes(missive)

        if not provider_paths:
            raise ValueError(f"No provider configured for {missive.missive_type}")

        logger.info(
            f"Missive {missive.id}: Attempting to send with {len(provider_paths)} available provider(s)"
        )

        last_error = None
        attempts = []

        for index, provider_path in enumerate(provider_paths, 1):
            try:
                provider_class = import_string(provider_path)
                provider_name = provider_class.__name__

                logger.info(
                    f"Missive {missive.id}: Attempt {index}/{len(provider_paths)} with {provider_name}"
                )

                # Health check (optional)
                if not skip_health_check:
                    if not MissiveSender.is_provider_healthy(provider_class):
                        logger.warning(
                            f"Missive {missive.id}: {provider_name} is not healthy, skip"
                        )
                        attempts.append(
                            {
                                "provider": provider_name,
                                "status": "skipped",
                                "reason": "health_check_failed",
                            }
                        )

                        if not enable_fallback:
                            raise RuntimeError(f"{provider_name} is not available")

                        continue  # Try the next one

                # Instantiate and send
                provider = provider_class(missive)
                success = provider.send()

                if success:
                    logger.info(
                        f"Missive {missive.id}: ✅ Sent successfully via {provider_name} "
                        f"(attempt {index}/{len(provider_paths)})"
                    )
                    attempts.append(
                        {
                            "provider": provider_name,
                            "status": "success",
                            "attempt": index,
                        }
                    )

                    # Provider is stored in the event, no need to update missive directly

                    return True
                else:
                    logger.warning(
                        f"Missive {missive.id}: ❌ Failed with {provider_name}"
                    )
                    attempts.append(
                        {
                            "provider": provider_name,
                            "status": "failed",
                            "attempt": index,
                        }
                    )

                    if not enable_fallback:
                        raise RuntimeError(f"Send failed with {provider_name}")

            except ImportError as e:
                error_msg = f"Provider '{provider_path}' not found: {e}"
                logger.error(f"Missive {missive.id}: {error_msg}")
                last_error = error_msg
                attempts.append(
                    {
                        "provider": provider_path,
                        "status": "import_error",
                        "error": str(e),
                    }
                )

                if not enable_fallback:
                    raise ValueError(error_msg)

            except Exception as e:
                error_msg = f"Error sending with {provider_path}: {e}"
                logger.error(f"Missive {missive.id}: {error_msg}")
                last_error = error_msg
                attempts.append(
                    {"provider": provider_path, "status": "exception", "error": str(e)}
                )

                if not enable_fallback:
                    raise

        # If we get here, all providers failed
        error_summary = f"All providers failed for missive {missive.id}. "
        error_summary += f"Attempts: {attempts}. "
        if last_error:
            error_summary += f"Last error: {last_error}"

        logger.error(error_summary)
        raise RuntimeError(error_summary)

    @classmethod
    def send_bulk(cls, missives: list, **kwargs) -> dict:
        """
        Send multiple missives in bulk.

        Args:
            missives: List of missives to send
            **kwargs: Arguments to pass to send() (skip_health_check, enable_fallback)

        Returns:
            dict: {'success': count, 'failed': count, 'errors': [...]}

        Example:
            missives = Missive.objects.filter(status='PENDING')
            results = MissiveSender.send_bulk(missives)
            print(f"Sent: {results['success']}, Failed: {results['failed']}")
        """
        results: Dict[str, Any] = {"success": 0, "failed": 0, "errors": []}

        for missive in missives:
            try:
                if cls.send(missive, **kwargs):
                    results["success"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({"missive_id": missive.id, "error": str(e)})
                logger.error(f"Error during bulk send of missive {missive.id}: {e}")

        return results
