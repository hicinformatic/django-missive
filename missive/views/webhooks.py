"""
Vue webhook unifiée qui dispatch vers le bon provider.
"""

import json
import logging

from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.utils.module_loading import import_string
from django.views import View
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Récupère l'IP du client"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


@method_decorator(csrf_exempt, name="dispatch")
class WebhookView(View):
    """
    Vue webhook unifiée.

    Reçoit les webhooks de tous les providers sur une seule URL :
    /missive/webhook/{provider}/

    Exemple :
    - /missive/webhook/sendgrid/
    - /missive/webhook/twilio/
    - /missive/webhook/laposte/
    """

    def post(self, request, provider=None, *args, **kwargs):
        """Reçoit et traite le webhook"""
        try:
            # Logger la réception du webhook
            logger.info(
                f"🔔 Webhook reçu de {provider} depuis {get_client_ip(request)}"
            )

            # Parser le payload
            content_type = request.META.get("CONTENT_TYPE", "")

            if "application/json" in content_type:
                payload = json.loads(request.body.decode("utf-8"))
            else:
                # Form data (Twilio notamment)
                payload = dict(request.POST.items())

            # Logger le payload pour debug
            logger.debug(f"📦 Payload reçu: {json.dumps(payload, indent=2)}")

            # Extraire les headers
            headers = {
                key: value
                for key, value in request.META.items()
                if key.startswith("HTTP_")
                or key in ["CONTENT_TYPE", "CONTENT_LENGTH", "REMOTE_ADDR"]
            }

            # Obtenir le provider depuis l'URL
            if not provider:
                return JsonResponse(
                    {"error": "Provider manquant dans l'URL"}, status=400
                )

            # Charger dynamiquement le provider depuis la config
            from django.conf import settings

            from ..helpers import get_providers_from_config

            providers_config = get_providers_from_config()
            provider_path = None

            # Chercher le provider dans la config
            for type_providers in providers_config.values():
                for path in type_providers:
                    try:
                        provider_class = import_string(path)
                        # Normaliser le nom du provider pour la comparaison
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
                logger.error(f"Provider inconnu : {provider}")
                return JsonResponse(
                    {"error": f"Provider inconnu: {provider}"}, status=400
                )

            # Charger la classe du provider
            provider_class = import_string(provider_path)

            # Créer une instance du provider
            provider_instance = provider_class()

            # SÉCURITÉ : Valider la signature du webhook
            is_valid, validation_error = provider_instance.validate_webhook_signature(
                payload, headers
            )
            if not is_valid:
                logger.warning(
                    f"Signature invalide pour webhook {provider}: {validation_error}"
                )
                # Retourner 200 pour ne pas révéler qu'on a rejeté
                return HttpResponse(status=200)

            # Traiter le webhook
            success, error, missive = provider_instance.handle_webhook(payload, headers)

            if success:
                logger.info(
                    f"Webhook {provider} traité avec succès pour missive #{missive.id if missive else 'N/A'}"
                )
                return HttpResponse(status=200)
            else:
                logger.error(f"Échec webhook {provider}: {error}")
                # On retourne 200 quand même pour éviter les retry inutiles
                # Le provider peut retry manuellement si nécessaire
                return HttpResponse(status=200)

        except Exception as e:
            logger.exception(f"Erreur webhook {provider}: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)


# Vue pour tester les webhooks (développement uniquement)
@csrf_exempt
def webhook_test_view(request):
    """
    Endpoint de test pour simuler l'envoi de webhooks.
    À utiliser uniquement en développement.

    Usage:
        POST /missive/webhook/test/
        {
            "provider": "sendgrid",
            "payload": {
                "missive_id": "sg_123",
                "event": "delivered"
            }
        }
    """
    from django.conf import settings

    if not settings.DEBUG:
        return JsonResponse({"error": "Not available in production"}, status=403)

    if request.method == "POST":
        try:
            from ..helpers import get_providers_from_config

            data = json.loads(request.body.decode("utf-8"))
            provider_name = data.get("provider", "sendgrid")
            payload = data.get("payload", {})

            # Charger dynamiquement le provider
            providers_config = get_providers_from_config()
            provider_class = None

            for type_providers in providers_config.values():
                for path in type_providers:
                    try:
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
                    {"error": f"Provider {provider_name} inconnu"}, status=400
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

    # GET : Afficher les providers disponibles
    return JsonResponse(
        {
            "message": "POST a webhook here",
            "providers_available": list(PROVIDER_CLASSES.keys()),
            "example": {
                "provider": "sendgrid",
                "payload": {
                    "missive_id": "sg_123",  # external_id de la missive
                    "event": "delivered",
                    "email": "user@example.com",
                },
            },
        }
    )


@csrf_exempt
def webhook_status_view(request):
    """
    Vue de vérification du statut des webhooks.

    Répond toujours "ok" pour permettre aux providers de tester la connectivité.
    Si l'utilisateur est admin, affiche la liste complète des providers et leurs URLs.

    Usage:
        GET /webhooks/status/
        → {"status": "ok", "message": "Webhooks are ready..."}

        GET /webhooks/status/ (en tant qu'admin)
        → {"status": "ok", "admin": true, "providers": {...}, ...}
    """
    from django.conf import settings

    from ..helpers import get_providers_from_config

    # Réponse de base (toujours accessible)
    response_data = {
        "status": "ok",
        "message": "Webhooks are ready to receive notifications",
    }

    # Si utilisateur admin, ajouter les détails
    if request.user.is_authenticated and request.user.is_staff:
        providers_by_type = get_providers_from_config()
        base_url = getattr(
            settings, "MISSIVE_WEBHOOK_BASE_URL", "https://example.com"
        ).rstrip("/")

        # Récupérer tous les providers uniques
        all_providers = set()
        for provider_names in providers_by_type.values():
            all_providers.update(provider_names)

        # Construire la liste des URLs de webhook
        webhook_urls = {}
        for provider_name in sorted(all_providers):
            provider_slug = provider_name.lower().replace(" ", "")

            # Récupérer les types supportés pour ce provider
            provider_types = []
            for missive_type, provider_names in providers_by_type.items():
                if provider_name in provider_names:
                    provider_types.append(missive_type)

            # Générer les URLs pour chaque type
            urls = {}
            for missive_type in provider_types:
                type_slug = missive_type.lower().replace("_", "-")
                urls[missive_type] = f"{base_url}/webhooks/{provider_slug}/{type_slug}/"

            webhook_urls[provider_name] = {
                "types": provider_types,
                "urls": urls,
            }

        response_data.update(
            {
                "admin": True,
                "sandbox_mode": getattr(settings, "MISSIVE_SANDBOX", False),
                "webhook_base_url": base_url,
                "providers_count": len(all_providers),
                "providers": webhook_urls,
            }
        )

    return JsonResponse(response_data, json_dumps_params={"indent": 2})
