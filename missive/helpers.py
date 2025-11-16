"""Helper functions for missive creation and provider administration."""

import importlib
import inspect
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .models import Missive, MissivePriority, MissiveType

if TYPE_CHECKING:
    from django.contrib.auth.models import User as UserType
else:
    UserType = get_user_model()

User = get_user_model()
logger = logging.getLogger(__name__)


class MissiveBuilder:
    """Builder to create missives linked to any object."""

    @staticmethod
    def from_object(
        source_object: Any,
        sender: "UserType",
        missive_type: str,
        subject: str,
        body: str,
        body_text: Optional[str] = None,
        recipient_user: Optional["UserType"] = None,
        recipient_email: Optional[str] = None,
        recipient_phone: Optional[str] = None,
        recipient_address: Optional[str] = None,
        priority: str = MissivePriority.NORMAL.value,  # type: ignore[attr-defined]
        is_registered: bool = False,
        requires_signature: bool = False,
        scheduled_at: Optional[Any] = None,
        metadata: Optional[Dict] = None,
        **kwargs,
    ) -> Missive:
        """Creates a missive linked to a source object."""
        missive = Missive(
            content_object=source_object,
            sender=sender,
            missive_type=missive_type,
            subject=subject,
            body=body,
            body_text=body_text or body,
            recipient_user=recipient_user,
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            recipient_address=recipient_address,
            priority=priority,
            is_registered=is_registered,
            requires_signature=requires_signature,
            scheduled_at=scheduled_at,
            metadata=metadata or {},
            **kwargs,
        )
        missive.save()
        return missive

    @staticmethod
    def get_missives_for_object(obj: Any):
        """
        Récupère toutes les missives liées à un objet.

        Args:
            obj: L'objet source

        Returns:
            QuerySet: Les missives liées à cet objet

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
        sender: "UserType",
        recipient_user: "UserType",
        subject: str,
        body: str,
        priority: str = MissivePriority.NORMAL.value,  # type: ignore[attr-defined]
        metadata: Optional[Dict] = None,
    ) -> Missive:
        """
        Raccourci pour créer une notification in-app.

        Example:
            MissiveBuilder.create_notification(
                source_object=comment,
                sender=comment.author,
                recipient_user=post.author,
                subject="Nouveau commentaire",
                body=f"{comment.author} a commenté votre post"
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
        sender: "UserType",
        recipient_email: str,
        subject: str,
        body: str,
        body_text: Optional[str] = None,
        is_registered: bool = False,
        priority: str = MissivePriority.NORMAL.value,  # type: ignore[attr-defined]
        metadata: Optional[Dict] = None,
    ) -> Missive:
        """
        Raccourci pour créer un email.

        Example:
            MissiveBuilder.create_email(
                source_object=invoice,
                sender=request.user,
                recipient_email=invoice.customer_email,
                subject=f"Facture #{invoice.number}",
                body="Veuillez trouver ci-joint votre facture...",
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
        sender: "UserType",
        recipient_phone: str,
        subject: str,
        body: str,
        priority: str = MissivePriority.NORMAL.value,  # type: ignore[attr-defined]
        metadata: Optional[Dict] = None,
    ) -> Missive:
        """
        Raccourci pour créer un SMS.

        Example:
            MissiveBuilder.create_sms(
                source_object=appointment,
                sender=system_user,
                recipient_phone=appointment.patient_phone,
                subject="Rappel RDV",
                body=f"RDV demain à {appointment.time}",
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
            body_text=body,  # Pour SMS, body_text = body (texte brut)
            priority=priority,
            metadata=metadata,
        )


def get_missives_stats_for_object(obj: Any) -> Dict[str, int]:
    """
    Récupère des statistiques sur les missives liées à un objet.

    Args:
        obj: L'objet source

    Returns:
        Dict avec les stats (total, sent, delivered, failed, etc.)

    Example:
        order = Order.objects.get(id=123)
        stats = get_missives_stats_for_object(order)
        print(f"Total: {stats['total']}, Envoyés: {stats['sent']}")
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
# Utilitaires pour l'administration des providers
# ==============================================================================


def get_provider_name_from_path(provider_path):
    """
    Extrait le nom court du provider depuis son chemin complet.
    Ex: 'python_missive.providers.sendgrid.SendGridProvider' -> 'sendgrid'
    """
    if not provider_path:
        return "custom"

    # If it's already a short name, return it as is
    if "." not in provider_path:
        return provider_path.lower()

    # Extraire le nom du module provider
    parts = provider_path.split(".")
    if (
        len(parts) >= 3
        and parts[1] == "providers"
        and parts[0] in ("missive", "python_missive")
    ):
        return parts[2].lower()

    # Fallback: extraire le nom de la classe sans "Provider"
    class_name = parts[-1]
    provider_name = class_name.replace("Provider", "").lower()
    return provider_name or "custom"


def get_providers_from_config():
    """
    Récupère la configuration MISSIVE_PROVIDERS depuis les settings
    et retourne un dictionnaire {type_missive: [liste_noms_providers]}.

    Configuration (simple list with auto-categorization):
       MISSIVE_PROVIDERS = [
           'missive.providers.twilio.TwilioProvider',
           'missive.providers.sendgrid.SendGridProvider',
           ...
       ]

    Chaque provider est automatiquement catégorisé selon ses supported_types.

    Returns:
        Dict[str, List[str]]: Dictionnaire {type_missive: [noms_courts]}
    """
    from django.utils.module_loading import import_string

    providers_config = getattr(settings, "MISSIVE_PROVIDERS", None)
    providers_by_type = {}

    # Format: Simple list (auto-categorization)
    if isinstance(providers_config, list):
        for provider_path in providers_config:
            try:
                # Charger la classe du provider
                provider_class = import_string(provider_path)
                provider_name = get_provider_name_from_path(provider_path)

                # Get supported types
                supported_types = getattr(provider_class, "supported_types", [])

                # Add the provider to each type it supports
                for missive_type in supported_types:
                    if missive_type not in providers_by_type:
                        providers_by_type[missive_type] = []
                    if provider_name not in providers_by_type[missive_type]:
                        providers_by_type[missive_type].append(provider_name)

            except Exception as e:
                # En cas d'erreur de chargement, ignorer silencieusement
                print(f"Warning: Could not load provider {provider_path}: {e}")
                continue

    # If no config, use default values
    if not providers_by_type:
        providers_by_type = {
            "EMAIL": [
                "django_email",
                "sendgrid",
                "mailgun",
                "ses",
                "brevo",
                "smspartner",
            ],
            "SMS": ["twilio", "vonage", "smspartner", "brevo"],
            "RCS": ["twilio"],
            "POSTAL": ["laposte"],
            "LRE": ["ar24", "certeurope"],
            "VOICE_CALL": ["twilio", "vonage", "smspartner"],
            "NOTIFICATION": ["notification"],
            "PUSH_NOTIFICATION": ["fcm", "apn"],
            "BRANDED": ["twilio", "slack", "teams", "telegram", "signal", "messenger"],
        }

    return providers_by_type


def get_provider_paths_from_config():
    """
    Récupère la configuration MISSIVE_PROVIDERS depuis les settings
    et retourne un dictionnaire {type_missive: [liste_chemins_complets]}.

    Contrairement à get_providers_from_config(), cette fonction retourne
    les chemins complets vers les classes (ex: 'missive.providers.twilio.TwilioProvider')
    au lieu des noms courts (ex: 'twilio').

    Utilisé par MissiveSender pour le failover.

    Returns:
        Dict[str, List[str]]: Dictionnaire {type_missive: [chemins_complets]}
    """
    from django.utils.module_loading import import_string

    providers_config = getattr(settings, "MISSIVE_PROVIDERS", None)
    providers_by_type = {}

    # Format: Simple list (auto-categorization)
    if isinstance(providers_config, list):
        for provider_path in providers_config:
            try:
                # Charger la classe du provider
                provider_class = import_string(provider_path)

                # Get supported types
                supported_types = getattr(provider_class, "supported_types", [])

                # Add the full path to each type it supports
                for missive_type in supported_types:
                    if missive_type not in providers_by_type:
                        providers_by_type[missive_type] = []
                    if provider_path not in providers_by_type[missive_type]:
                        providers_by_type[missive_type].append(provider_path)

            except Exception as e:
                # En cas d'erreur de chargement, ignorer silencieusement
                logger.warning(f"Could not load provider {provider_path}: {e}")
                continue

    # If no config, use default values (with full paths, python-missive as backend)
    if not providers_by_type:
        providers_by_type = {
            "EMAIL": [
                "missive.providers.django_email.DjangoEmailProvider",
                "python_missive.providers.sendgrid.SendGridProvider",
                "python_missive.providers.mailgun.MailgunProvider",
                "python_missive.providers.ses.SESProvider",
                "python_missive.providers.brevo.BrevoProvider",
                "python_missive.providers.smspartner.SMSPartnerProvider",
            ],
            "SMS": [
                "python_missive.providers.twilio.TwilioProvider",
                "python_missive.providers.vonage.VonageProvider",
                "python_missive.providers.smspartner.SMSPartnerProvider",
                "python_missive.providers.brevo.BrevoProvider",
            ],
            "RCS": ["python_missive.providers.twilio.TwilioProvider"],
            "POSTAL": ["python_missive.providers.laposte.LaPosteProvider"],
            "LRE": [
                "python_missive.providers.ar24.AR24Provider",
                "python_missive.providers.certeurope.CertEuropeProvider",
            ],
            "VOICE_CALL": [
                "python_missive.providers.twilio.TwilioProvider",
                "python_missive.providers.vonage.VonageProvider",
                "python_missive.providers.smspartner.SMSPartnerProvider",
            ],
            "NOTIFICATION": [
                "python_missive.providers.notification.InAppNotificationProvider"
            ],
            "PUSH_NOTIFICATION": [
                "python_missive.providers.fcm.FCMProvider",
                "python_missive.providers.apn.APNProvider",
            ],
            "BRANDED": [
                "python_missive.providers.twilio.TwilioProvider",
                "python_missive.providers.slack.SlackProvider",
                "python_missive.providers.teams.TeamsProvider",
                "python_missive.providers.telegram.TelegramProvider",
                "python_missive.providers.signal.SignalProvider",
                "python_missive.providers.messenger.MessengerProvider",
            ],
        }

    return providers_by_type


def discover_providers():
    """
    Découvre automatiquement tous les providers depuis missive/providers/
    et retourne un dictionnaire {nom_court: display_name}.
    """
    providers_dict = {}

    # Add special "custom" provider
    providers_dict["custom"] = _("Custom Provider")

    # Chemin vers le dossier providers
    providers_dir = Path(__file__).parent / "providers"

    if not providers_dir.exists():
        return providers_dict

    # Parcourir tous les fichiers Python du dossier providers
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
                # Check that it's a Provider class defined in THIS module (not imported)
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

    # Collecter tous les providers uniques
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
