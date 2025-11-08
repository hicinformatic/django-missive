"""
Vue webhook unifiée qui dispatch vers le bon provider.
"""

import json
import logging

from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from ..providers import (
    BaseProvider,
    LaPosteProvider,
    MailgunProvider,
    SendGridProvider,
    SendinBlueProvider,
    SMSPartnerProvider,
    TwilioProvider,
)

logger = logging.getLogger(__name__)


# Mapping provider name -> classe
PROVIDER_CLASSES = {
    "sendgrid": SendGridProvider,
    "mailgun": MailgunProvider,
    "twilio": TwilioProvider,
    "smspartner": SMSPartnerProvider,
    "laposte": LaPosteProvider,
    "sendinblue": SendinBlueProvider,
    "brevo": SendinBlueProvider,
}


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
            # Parser le payload
            content_type = request.META.get("CONTENT_TYPE", "")

            if "application/json" in content_type:
                payload = json.loads(request.body.decode("utf-8"))
            else:
                # Form data (Twilio notamment)
                payload = dict(request.POST.items())

            # Extraire les headers
            headers = {
                key: value
                for key, value in request.META.items()
                if key.startswith("HTTP_") or key in ["CONTENT_TYPE", "CONTENT_LENGTH"]
            }

            # Obtenir le provider depuis l'URL
            if not provider:
                return JsonResponse(
                    {"error": "Provider manquant dans l'URL"}, status=400
                )

            # Obtenir la classe du provider
            provider_class = PROVIDER_CLASSES.get(provider.lower())
            if not provider_class:
                logger.error(f"Provider inconnu : {provider}")
                return JsonResponse(
                    {"error": f"Provider inconnu: {provider}"}, status=400
                )

            # Créer une instance et traiter le webhook
            provider_instance = provider_class()
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
            data = json.loads(request.body.decode("utf-8"))
            provider_name = data.get("provider", "sendgrid")
            payload = data.get("payload", {})

            provider_class = PROVIDER_CLASSES.get(provider_name)
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
