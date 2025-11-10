"""
Module pour envoyer des missives via différents providers avec fallback automatique.
"""

import logging
from typing import List

from django.conf import settings
from django.utils.module_loading import import_string

from .helpers import get_provider_paths_from_config
from .models import Missive

logger = logging.getLogger(__name__)


# Mapping par défaut des providers (fallback si pas de config)
DEFAULT_PROVIDERS = {
    "EMAIL": ["missive.providers.django_email.DjangoEmailProvider"],
    "SMS": ["missive.providers.twilio.TwilioProvider"],
    "POSTAL": ["missive.providers.laposte.LaPosteProvider"],
    "NOTIFICATION": ["missive.providers.notification.InAppNotificationProvider"],
    "BRANDED": [
        "missive.providers.twilio.TwilioProvider"
    ],  # Pour WhatsApp, Slack, Teams, etc.
}


class MissiveSender:
    """
    Classe pour envoyer des missives avec fallback automatique.

    Usage:
        from missive.sender import MissiveSender
        from missive.models import Missive

        missive = Missive.objects.get(id=123)

        # Envoi avec fallback automatique
        success = MissiveSender.send(missive)

        # Envoi sans fallback
        success = MissiveSender.send(missive, enable_fallback=False)

        # Envoi sans health check
        success = MissiveSender.send(missive, skip_health_check=True)
    """

    @staticmethod
    def get_provider_classes(missive: Missive) -> List[str]:
        """
        Récupère la liste ordonnée des providers à essayer (par priorité).

        Ordre de priorité :
        1. missive.provider (provider explicitement défini) - UN SEUL
        2. get_provider_paths_from_config() (auto-catégorisation) - LISTE
        3. Ancienne config MISSIVE_CONFIG['PROVIDERS'] (deprecated) - STRING
        4. DEFAULT_PROVIDERS[missive_type] (providers par défaut) - LISTE

        Args:
            missive: La missive à envoyer

        Returns:
            Liste des chemins de classes de providers à essayer dans l'ordre

        Raises:
            ValueError: Si aucun provider n'est configuré pour ce type
        """
        # 1. Provider explicite sur la missive (priorité absolue, pas de fallback)
        if missive.provider:
            logger.info(
                f"Missive {missive.id}: Provider explicite '{missive.provider}'"
            )
            return [missive.provider]

        # 2. Configuration depuis get_provider_paths_from_config() (auto-catégorisation)
        providers_by_type = get_provider_paths_from_config()
        provider_paths = providers_by_type.get(missive.missive_type)

        if provider_paths:
            logger.info(
                f"Missive {missive.id}: Providers configurés pour {missive.missive_type}: {provider_paths}"
            )
            return provider_paths

        # 3. Fallback sur l'ancienne config MISSIVE_CONFIG['PROVIDERS']
        missive_config = getattr(settings, "MISSIVE_CONFIG", {})
        old_providers_config = missive_config.get("PROVIDERS", {})
        old_provider_path = old_providers_config.get(missive.missive_type)

        if old_provider_path:
            logger.warning(
                f"Missive {missive.id}: Utilisation de l'ancienne config MISSIVE_CONFIG['PROVIDERS']. "
                f"Migrez vers MISSIVE_PROVIDERS."
            )
            return [old_provider_path]

        # 4. Provider par défaut
        default_providers = DEFAULT_PROVIDERS.get(missive.missive_type, [])
        if default_providers:
            logger.info(
                f"Missive {missive.id}: Utilisation des providers par défaut: {default_providers}"
            )
            return default_providers

        raise ValueError(f"Aucun provider configuré pour {missive.missive_type}")

    @staticmethod
    def get_provider_class(missive: Missive):
        """
        DEPRECATED: Utilisez get_provider_classes() à la place.

        Récupère le premier provider de la liste pour compatibilité.
        """
        logger.warning(
            "get_provider_class() est deprecated, utilisez send() directement"
        )

        provider_paths = MissiveSender.get_provider_classes(missive)
        return import_string(provider_paths[0])

    @staticmethod
    def is_provider_healthy(provider_class) -> bool:
        """
        Vérifie si un provider est opérationnel via health check.

        Args:
            provider_class: Classe du provider à vérifier

        Returns:
            bool: True si le provider est sain, False sinon
        """
        try:
            provider_instance = provider_class()
            health = provider_instance.health_check()

            is_healthy = health.get("is_healthy", False)
            status = health.get("status", "unknown")

            if not is_healthy:
                logger.warning(
                    f"Provider {provider_class.__name__} n'est pas healthy: "
                    f"status={status}, summary={health.get('summary')}"
                )

            return is_healthy
        except Exception as e:
            logger.error(
                f"Erreur lors du health check de {provider_class.__name__}: {e}"
            )
            return False

    @staticmethod
    def send(
        missive: Missive, skip_health_check: bool = False, enable_fallback: bool = True
    ) -> bool:
        """
        Envoie une missive via le provider approprié avec fallback automatique.

        Processus :
        1. Récupère la liste des providers configurés par ordre de priorité
        2. Pour chaque provider :
           - Vérifie sa santé (health check) si skip_health_check=False
           - Tente l'envoi
           - Si succès, termine
           - Si échec et enable_fallback=True, essaie le suivant
        3. Si tous échouent, lève une exception

        Args:
            missive: La missive à envoyer
            skip_health_check: Si True, ne fait pas de health check avant envoi (défaut: False)
            enable_fallback: Si True, essaie les providers suivants en cas d'échec (défaut: True)

        Returns:
            bool: True si envoyé avec succès

        Raises:
            ValueError: Si aucun provider n'est configuré
            RuntimeError: Si tous les providers ont échoué

        Example:
            # Envoi standard avec fallback
            success = MissiveSender.send(missive)

            # Envoi sans fallback (utilise uniquement le premier provider)
            success = MissiveSender.send(missive, enable_fallback=False)

            # Envoi sans health check (plus rapide)
            success = MissiveSender.send(missive, skip_health_check=True)
        """
        # Vérifier que la missive peut être envoyée
        if not missive.can_send():
            logger.warning(
                f"Missive {missive.id}: Ne peut pas être envoyée (can_send()=False)"
            )
            return False

        # Récupérer la liste des providers
        provider_paths = MissiveSender.get_provider_classes(missive)

        if not provider_paths:
            raise ValueError(f"Aucun provider configuré pour {missive.missive_type}")

        logger.info(
            f"Missive {missive.id}: Tentative d'envoi avec {len(provider_paths)} provider(s) disponible(s)"
        )

        last_error = None
        attempts = []

        # Essayer chaque provider dans l'ordre
        for index, provider_path in enumerate(provider_paths, 1):
            try:
                # Importer le provider
                provider_class = import_string(provider_path)
                provider_name = provider_class.__name__

                logger.info(
                    f"Missive {missive.id}: Tentative {index}/{len(provider_paths)} avec {provider_name}"
                )

                # Health check (optionnel)
                if not skip_health_check:
                    if not MissiveSender.is_provider_healthy(provider_class):
                        logger.warning(
                            f"Missive {missive.id}: {provider_name} n'est pas healthy, skip"
                        )
                        attempts.append(
                            {
                                "provider": provider_name,
                                "status": "skipped",
                                "reason": "health_check_failed",
                            }
                        )

                        if not enable_fallback:
                            raise RuntimeError(f"{provider_name} n'est pas disponible")

                        continue  # Essayer le suivant

                # Instancier et envoyer
                provider = provider_class(missive)
                success = provider.send()

                if success:
                    logger.info(
                        f"Missive {missive.id}: ✅ Envoyé avec succès via {provider_name} "
                        f"(tentative {index}/{len(provider_paths)})"
                    )
                    attempts.append(
                        {
                            "provider": provider_name,
                            "status": "success",
                            "attempt": index,
                        }
                    )

                    # Mettre à jour le provider utilisé sur la missive
                    missive.provider = provider_path
                    missive.save(update_fields=["provider"])

                    return True
                else:
                    logger.warning(
                        f"Missive {missive.id}: ❌ Échec avec {provider_name}"
                    )
                    attempts.append(
                        {
                            "provider": provider_name,
                            "status": "failed",
                            "attempt": index,
                        }
                    )

                    if not enable_fallback:
                        raise RuntimeError(f"Échec d'envoi avec {provider_name}")

            except ImportError as e:
                error_msg = f"Provider '{provider_path}' introuvable: {e}"
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
                error_msg = f"Erreur lors de l'envoi avec {provider_path}: {e}"
                logger.error(f"Missive {missive.id}: {error_msg}")
                last_error = error_msg
                attempts.append(
                    {"provider": provider_path, "status": "exception", "error": str(e)}
                )

                if not enable_fallback:
                    raise

        # Si on arrive ici, tous les providers ont échoué
        error_summary = f"Tous les providers ont échoué pour la missive {missive.id}. "
        error_summary += f"Tentatives: {attempts}. "
        if last_error:
            error_summary += f"Dernière erreur: {last_error}"

        logger.error(error_summary)
        raise RuntimeError(error_summary)

    @classmethod
    def send_bulk(cls, missives: list, **kwargs) -> dict:
        """
        Envoie plusieurs missives en masse.

        Args:
            missives: Liste de missives à envoyer
            **kwargs: Arguments à passer à send() (skip_health_check, enable_fallback)

        Returns:
            dict: {'success': count, 'failed': count, 'errors': [...]}

        Example:
            missives = Missive.objects.filter(status='PENDING')
            results = MissiveSender.send_bulk(missives)
            print(f"Envoyés: {results['success']}, Échecs: {results['failed']}")
        """
        results = {"success": 0, "failed": 0, "errors": []}

        for missive in missives:
            try:
                if cls.send(missive, **kwargs):
                    results["success"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({"missive_id": missive.id, "error": str(e)})
                logger.error(
                    f"Erreur lors de l'envoi en masse de missive {missive.id}: {e}"
                )

        return results
