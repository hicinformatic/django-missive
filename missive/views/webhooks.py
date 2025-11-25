"""Unified webhook view that dispatches to the right provider."""

import json
import logging

from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.utils.module_loading import import_string
from django.views import View
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Get client IP address."""
    # B110: request.META is a controlled Django dict, safe to access
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")  # nosec B110
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")  # nosec B110
    return ip


@method_decorator(csrf_exempt, name="dispatch")
class WebhookView(View):
    """Unified webhook view for all providers at /missive/webhook/{provider}/."""

    def post(self, request, provider=None, *args, **kwargs):
        """Receives and processes webhook."""
        try:
            logger.info(f"Webhook received from {provider} ({get_client_ip(request)})")

            from django.conf import settings

            # B110: getattr on settings is safe, settings are controlled
            MAX_BODY_SIZE = getattr(  # nosec B110
                settings, "MISSIVE_WEBHOOK_MAX_BODY_SIZE", 10 * 1024 * 1024
            )
            # B110: request.META is a controlled Django dict, safe to access
            content_length = int(request.META.get("CONTENT_LENGTH", 0))  # nosec B110
            if content_length > MAX_BODY_SIZE:
                logger.warning(f"Webhook payload too large: {content_length} bytes")
                return JsonResponse({"error": "Payload too large"}, status=413)

            # B110: request.META is a controlled Django dict, safe to access
            content_type = request.META.get("CONTENT_TYPE", "")  # nosec B110

            if "application/json" in content_type:
                # B301: json.loads is safe here, we validate content_length first
                payload = json.loads(request.body.decode("utf-8"))  # nosec B301
            else:
                payload = dict(request.POST.items())

            logger.debug(f"Webhook keys: {list(payload.keys())}")

            # B110: request.META is a controlled Django dict, safe to access
            headers = {
                key: value
                for key, value in request.META.items()  # nosec B110
                if key.startswith("HTTP_")
                or key in ["CONTENT_TYPE", "CONTENT_LENGTH", "REMOTE_ADDR"]
            }

            if not provider:
                return JsonResponse({"error": "Provider missing in URL"}, status=400)

            from ..helpers import get_providers_from_config

            providers_config = get_providers_from_config()
            provider_path = None

            # Find provider in config
            for type_providers in providers_config.values():
                for path in type_providers:
                    try:
                        # import_string is safe here, path comes from config
                        provider_class = import_string(path)
                        provider_name = (
                            provider_class.name.lower()
                            .replace(" ", "")
                            .replace("-", "")
                        )
                        if provider_name == provider.lower().replace("-", ""):
                            provider_path = path
                            break
                    except Exception:
                        continue
                if provider_path:
                    break

            if not provider_path:
                logger.error(f"Unknown provider: {provider}")
                return JsonResponse(
                    {"error": f"Unknown provider: {provider}"}, status=400
                )

            # Load provider class
            # import_string is safe here, provider_path comes from config
            provider_class = import_string(provider_path)
            provider_instance = provider_class()

            # SECURITY: Validate webhook signature
            is_valid, validation_error = provider_instance.validate_webhook_signature(
                payload, headers
            )
            if not is_valid:
                logger.warning(
                    f"Invalid signature for webhook {provider} from {get_client_ip(request)}"
                )
                # Return 200 to avoid revealing rejection
                return HttpResponse(status=200)

            # Process webhook
            success, error, missive = provider_instance.handle_webhook(payload, headers)

            if success:
                logger.info(
                    f"Webhook {provider} processed successfully for missive #{missive.id if missive else 'N/A'}"
                )
                return HttpResponse(status=200)

            logger.error(f"Webhook {provider} failed: {error}")
            # Return 200 anyway to avoid useless retries
            return HttpResponse(status=200)

        except Exception as e:
            logger.exception(f"Webhook error {provider}: {e}")
            # Don't expose error details in production (security)
            return JsonResponse(
                {"status": "error", "message": "Error processing webhook"},
                status=500,
            )


@csrf_exempt
def webhook_test_view(request):
    """
    Test endpoint to simulate webhook sending.
    Development only.

    Usage:
        POST /missive/webhook/test/
        {
            "provider": "sendgrid",
            "payload": {"missive_id": "sg_123", "event": "delivered"}
        }
    """
    from django.conf import settings

    if not settings.DEBUG:
        return JsonResponse({"error": "Not available in production"}, status=403)

    if request.method == "POST":
        try:
            from ..helpers import get_providers_from_config

            # B301: json.loads is safe here, only in DEBUG mode
            data = json.loads(request.body.decode("utf-8"))  # nosec B301
            provider_name = data.get("provider", "sendgrid")
            payload = data.get("payload", {})

            providers_config = get_providers_from_config()
            provider_class = None

            for type_providers in providers_config.values():
                for path in type_providers:
                    try:
                        # import_string is safe here, path comes from config
                        cls = import_string(path)
                        if cls.name.lower().replace(" ", "") == provider_name.lower():
                            provider_class = cls
                            break
                    except Exception:
                        continue
                if provider_class:
                    break

            if not provider_class:
                return JsonResponse(
                    {"error": f"Unknown provider: {provider_name}"}, status=400
                )

            provider = provider_class()
            success, error, missive = provider.handle_webhook(payload, {})

            return JsonResponse(
                {
                    "status": "success" if success else "failed",
                    "error": error if not success else None,
                    "missive_id": missive.id if missive else None,
                    "provider": provider_name,
                }
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    # GET: Show available providers
    from ..helpers import get_providers_from_config

    providers_config = get_providers_from_config()
    all_providers = set()
    for provider_list in providers_config.values():
        for provider_path in provider_list:
            try:
                # import_string is safe here, path comes from config
                provider_class = import_string(provider_path)
                all_providers.add(provider_class.name.lower())
            except Exception:
                continue
    return JsonResponse(
        {
            "message": "POST a webhook here",
            "providers_available": sorted(list(all_providers)),
            "example": {
                "provider": "sendgrid",
                "payload": {
                    "missive_id": "sg_123",
                    "event": "delivered",
                    "email": "user@example.com",
                },
            },
        }
    )


@csrf_exempt
def webhook_status_view(request):
    """
    Webhook status check endpoint.

    Always returns "ok" to allow providers to test connectivity.
    If user is admin, shows full provider list and URLs.
    """
    from django.conf import settings

    from ..helpers import get_providers_from_config

    response_data = {
        "status": "ok",
        "message": "Webhooks are ready to receive notifications",
    }

    # If admin, add details
    if request.user.is_authenticated and request.user.is_staff:
        providers_by_type = get_providers_from_config()
        # B110: getattr on settings is safe, settings are controlled
        base_url = getattr(  # nosec B110
            settings, "MISSIVE_WEBHOOK_BASE_URL", "https://example.com"
        ).rstrip("/")

        all_providers = set()
        for provider_names in providers_by_type.values():
            all_providers.update(provider_names)

        webhook_urls = {}
        for provider_name in sorted(all_providers):
            provider_slug = provider_name.lower().replace(" ", "")

            provider_types = []
            for missive_type, provider_names in providers_by_type.items():
                if provider_name in provider_names:
                    provider_types.append(missive_type)

            urls = {}
            for missive_type in provider_types:
                type_slug = missive_type.lower().replace("_", "-")
                urls[missive_type] = f"{base_url}/webhooks/{provider_slug}/{type_slug}/"

            webhook_urls[provider_name] = {
                "types": provider_types,
                "urls": urls,
            }

        # B110: getattr on settings is safe, settings are controlled
        response_data.update(
            {
                "admin": True,
                "sandbox_mode": getattr(settings, "MISSIVE_SANDBOX", False),  # nosec B110
                "webhook_base_url": base_url,
                "providers_count": len(all_providers),
                "providers": webhook_urls,
            }
        )

    return JsonResponse(response_data, json_dumps_params={"indent": 2})
