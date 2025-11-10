"""
Modèle virtuel (non persisté) pour afficher les providers dans l'admin.
"""

from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db import models
from django.db.models.query import QuerySet
from django.db.models.sql import Query
from django.utils.translation import gettext_lazy as _


class ProviderInfoQuerySet(QuerySet):
    """QuerySet en mémoire qui lit depuis MISSIVE_PROVIDERS au lieu de la base"""

    def __init__(self, model=None, data=None, query=None, using=None, hints=None):
        if query is None and model is not None:
            query = Query(model)
        super().__init__(model=model, query=query, using=using, hints=hints)
        self._result_cache = list(data or [])
        self._prefetch_done = True

    def __len__(self):
        return len(self._result_cache)

    def __getitem__(self, k):
        if isinstance(k, slice):
            return self.__class__(
                self.model,
                self._result_cache[k],
                self.query.clone(),
                using=self._db,
                hints=self._hints,
            )
        return self._result_cache[k]

    def _clone(self):
        return self.__class__(
            self.model,
            list(self._result_cache),
            self.query.clone(),
            using=self._db,
            hints=self._hints,
        )

    def all(self):
        return self._clone()

    def count(self):
        return len(self._result_cache)

    def filter(self, *args, **kwargs):
        """Filtre les providers selon les kwargs avec support des lookups Django"""
        rslt = self._result_cache

        for lookup, value in kwargs.items():
            # Gérer les lookups Django (__icontains, __contains, etc.)
            if "__" in lookup:
                field_name, lookup_type = lookup.rsplit("__", 1)

                if lookup_type == "icontains":
                    # Recherche insensible à la casse
                    rslt = [
                        obj
                        for obj in rslt
                        if value.lower() in str(getattr(obj, field_name, "")).lower()
                    ]
                elif lookup_type == "contains":
                    # Recherche sensible à la casse
                    rslt = [
                        obj
                        for obj in rslt
                        if value in str(getattr(obj, field_name, ""))
                    ]
                elif lookup_type == "exact":
                    # Égalité exacte
                    rslt = [obj for obj in rslt if getattr(obj, field_name) == value]
                elif lookup_type == "in":
                    # Valeur dans une liste
                    rslt = [obj for obj in rslt if getattr(obj, field_name) in value]
                else:
                    # Autres lookups non supportés, ignorer
                    pass
            else:
                # Filtre simple (égalité)
                rslt = [obj for obj in rslt if getattr(obj, lookup, None) == value]

        return self.__class__(
            self.model,
            rslt,
            self.query.clone(),
            using=self._db,
            hints=self._hints,
        )

    def order_by(self, *fields):
        """Trie les providers"""
        rslt = self._result_cache
        for field in reversed(fields):
            reverse = False
            if field.startswith("-"):
                reverse = True
                field = field[1:]
            rslt = sorted(
                rslt, key=lambda x: getattr(x, field, None) or "", reverse=reverse
            )
        return self.__class__(
            self.model,
            rslt,
            self.query.clone(),
            using=self._db,
            hints=self._hints,
        )

    def get(self, **kwargs):
        """Récupère un provider unique"""
        rslt = self._result_cache
        for attr, value in kwargs.items():
            rslt = [obj for obj in rslt if getattr(obj, attr) == value]

        if len(rslt) == 1:
            return rslt[0]
        if not rslt:
            raise ObjectDoesNotExist(
                f"{self.model.__name__} matching query does not exist."
            )
        raise MultipleObjectsReturned(
            f"Multiple {self.model.__name__} objects returned."
        )


class ProviderInfoManager(models.Manager):
    """Manager personnalisé qui retourne notre QuerySet en mémoire"""

    def get_queryset(self):
        # Charger les providers depuis la config
        from ..helpers import get_providers_from_config

        providers_by_type = get_providers_from_config()

        # Regrouper les providers par nom (un provider peut supporter plusieurs types)
        providers_dict = {}
        for missive_type, provider_names in sorted(providers_by_type.items()):
            for provider_name in provider_names:
                if provider_name not in providers_dict:
                    providers_dict[provider_name] = []
                providers_dict[provider_name].append(missive_type)

        # Créer la liste des providers avec leurs types multiples
        providers_list = []
        pk = 1
        for provider_name, missive_types in sorted(providers_dict.items()):
            provider = ProviderInfo(
                pk=pk,
                name=provider_name,
                missive_type=",".join(
                    missive_types
                ),  # Stocker tous les types séparés par virgule
            )
            providers_list.append(provider)
            pk += 1

        # Retourner un QuerySet en mémoire
        return ProviderInfoQuerySet(model=self.model, data=providers_list)


class ProviderInfo(models.Model):
    """
    Modèle virtuel (non persisté) représentant un provider configuré.
    Les données viennent de MISSIVE_PROVIDERS, pas de la base de données.
    """

    name = models.CharField(
        max_length=100,
        verbose_name=_("Nom du provider"),
    )
    missive_type = models.CharField(
        max_length=50,
        verbose_name=_("Type de missive"),
    )

    objects = ProviderInfoManager()

    class Meta:
        managed = False  # Pas de table en base de données
        verbose_name = _("Provider")
        verbose_name_plural = _("Providers")
        default_permissions = ()  # Pas de permissions add/change/delete
        ordering = ["name"]  # Tri alphabétique par nom

    def __str__(self):
        return f"{self.name} ({self.missive_type})"

    @property
    def missive_types_list(self):
        """Retourne la liste des types de missive supportés"""
        if not self.missive_type:
            return []
        return [t.strip() for t in self.missive_type.split(",")]

    def _get_provider_class(self):
        """
        Helper pour récupérer la classe du provider dynamiquement.
        Retourne None si le provider ne peut pas être chargé.

        Cherche dans MISSIVE_PROVIDERS (format liste), sinon utilise un fallback.
        """
        try:
            from django.conf import settings
            from django.utils.module_loading import import_string

            # Normaliser le nom (minuscules, sans espaces ni tirets)
            normalized_name = (
                self.name.lower().replace(" ", "").replace("-", "").replace("_", "")
            )

            # Récupérer MISSIVE_PROVIDERS (doit être une liste)
            providers_config = getattr(settings, "MISSIVE_PROVIDERS", None)

            # Chercher le provider dans la config
            provider_path = None

            if isinstance(providers_config, list):
                for path in providers_config:
                    # Extraire le nom du provider depuis le path
                    path_lower = path.lower()
                    if normalized_name in path_lower:
                        provider_path = path
                        break

            # Si trouvé dans la config, importer directement
            if provider_path:
                return import_string(provider_path)

            # Fallback : Essayer de construire le chemin automatiquement
            # Cas spéciaux pour les noms de classe non standards
            class_name_map = {
                "djangoemail": "DjangoEmailProvider",
                "smspartner": "SMSPartnerProvider",
                "laposte": "LaPosteProvider",
                "sendgrid": "SendGridProvider",
                "ses": "SESProvider",
                "ar24": "AR24Provider",
                "fcm": "FCMProvider",
                "apn": "APNProvider",
                "notification": "InAppNotificationProvider",
            }

            class_name = class_name_map.get(normalized_name)
            if not class_name:
                # Fallback: capitaliser le nom
                class_name = f"{normalized_name.capitalize()}Provider"

            # Construire le chemin du provider
            provider_path = f"missive.providers.{normalized_name}.{class_name}"

            # Importer la classe
            return import_string(provider_path)

        except Exception:
            return None

    @property
    def required_packages(self):
        """
        Retourne la liste des packages Python requis pour ce provider.
        Récupère required_packages directement depuis la classe du provider.
        """
        provider_class = self._get_provider_class()
        if provider_class is None:
            return []
        return getattr(provider_class, "required_packages", [])

    @property
    def required_package(self):
        """
        DEPRECATED: Utilisez required_packages à la place.
        Retourne le premier package requis pour compatibilité rétroactive.
        """
        packages = self.required_packages
        return packages[0] if packages else None

    @property
    def is_installed(self):
        """Vérifie si tous les packages Python requis sont installés"""
        packages = self.required_packages
        if not packages:
            return True  # Pas de dépendance ou toujours dispo

        for package in packages:
            try:
                __import__(package)
            except ImportError:
                return False
        return True

    @property
    def required_config_keys(self):
        """
        Retourne la liste des variables d'environnement nécessaires.
        Récupère les config_keys directement depuis la classe du provider.
        """
        provider_class = self._get_provider_class()
        if provider_class is None:
            return []
        return getattr(provider_class, "config_keys", [])

    @property
    def brands(self):
        """
        Retourne la liste des marques de messagerie supportées (pour type BRANDED).
        Récupère brands directement depuis la classe du provider.
        """
        provider_class = self._get_provider_class()
        if provider_class is None:
            return []
        return getattr(provider_class, "brands", [])

    @property
    def status_url(self):
        """
        Retourne l'URL de la page de statut/SLA du provider.
        Récupère status_url directement depuis la classe du provider.
        """
        provider_class = self._get_provider_class()
        if provider_class is None:
            return None
        return getattr(provider_class, "status_url", None)

    @property
    def documentation_url(self):
        """
        Retourne l'URL de la documentation API du provider.
        Récupère documentation_url directement depuis la classe du provider.
        """
        provider_class = self._get_provider_class()
        if provider_class is None:
            return None
        return getattr(provider_class, "documentation_url", None)

    @property
    def site_url(self):
        """
        Retourne l'URL du site web officiel du provider.
        Récupère site_url directement depuis la classe du provider.
        """
        provider_class = self._get_provider_class()
        if provider_class is None:
            return None
        return getattr(provider_class, "site_url", None)

    @property
    def description_text(self):
        """
        Retourne la description textuelle du provider.
        Récupère description_text directement depuis la classe du provider.
        """
        provider_class = self._get_provider_class()
        if provider_class is None:
            return None
        return getattr(provider_class, "description_text", None)

    @property
    def config_status(self):
        """Retourne le statut de configuration pour chaque variable"""
        config_vars = {}
        for key in self.required_config_keys:
            value = getattr(settings, key, None)
            config_vars[key] = {
                "configured": bool(value),
                "value": value,  # Afficher la vraie valeur
            }
        return config_vars

    @property
    def is_configured(self):
        """Vérifie si les credentials principaux sont configurés"""
        config_keys = {
            "sendgrid": "SENDGRID_API_KEY",
            "mailgun": "MAILGUN_API_KEY",
            "ses": "AWS_ACCESS_KEY_ID",
            "twilio": "TWILIO_ACCOUNT_SID",
            "vonage": "VONAGE_API_KEY",
            "telegram": "TELEGRAM_BOT_TOKEN",
            "slack": "SLACK_BOT_TOKEN",
            "teams": "TEAMS_CLIENT_ID",
            "fcm": "FCM_SERVER_KEY",
            "apn": "APN_CERTIFICATE_PATH",
            "laposte": "LAPOSTE_API_KEY",
            "ar24": "AR24_API_TOKEN",
            "certeurope": "CERTEUROPE_API_KEY",
            "messenger": "MESSENGER_PAGE_ACCESS_TOKEN",
            "smspartner": "SMSPARTNER_API_KEY",
            "django_email": None,
            "custom": None,
        }

        key = config_keys.get(self.name)
        if key is None:
            return True

        return hasattr(settings, key) and bool(getattr(settings, key, None))

    @property
    def status(self):
        """Retourne le statut : ready, needs_config, not_installed"""
        if self.is_installed and self.is_configured:
            return "ready"
        elif self.is_installed and not self.is_configured:
            return "needs_config"
        else:
            return "not_installed"

    @property
    def status_display(self):
        """Label du statut"""
        labels = {
            "ready": _("✅ Prêt"),
            "needs_config": _("⚠️ Configuration requise"),
            "not_installed": _("❌ Non installé"),
        }
        return labels.get(self.status, _("❓ Inconnu"))

    @property
    def usage_count(self):
        """Nombre d'utilisations de ce provider"""
        from .event import MissiveEvent

        return MissiveEvent.objects.filter(provider=self.name).count()

    @property
    def requirements_file(self):
        """Fichier requirements correspondant"""
        # Mapping provider → fichier requirements individuel
        mapping = {
            # Providers Email (fichiers individuels)
            "sendgrid": "requirements-sendgrid.txt",
            "mailgun": "requirements-mailgun.txt",
            "brevo": "requirements-brevo.txt",
            "ses": "requirements-ses.txt",
            "django_email": "requirements.txt",  # Toujours disponible
            # Providers SMS (fichiers individuels)
            "twilio": "requirements-twilio.txt",
            "vonage": "requirements-vonage.txt",
            "smspartner": "requirements.txt",  # Utilise requests (déjà dans core)
            # Messageries de marque (fichiers individuels)
            "slack": "requirements-slack.txt",
            "teams": "requirements-teams.txt",
            "telegram": "requirements-telegram.txt",
            "signal": "requirements.txt",  # Utilise requests (déjà dans core)
            "messenger": "requirements.txt",  # Utilise requests (déjà dans core)
            # Push (fichiers individuels)
            "fcm": "requirements-fcm.txt",
            "apn": "requirements-apn.txt",
            # Postal (utilisent requests + reportlab/Pillow déjà dans core)
            "laposte": "requirements.txt",
            "ar24": "requirements.txt",
            "certeurope": "requirements.txt",
        }
        return mapping.get(self.name, "requirements.txt")

    @property
    def credits_info(self):
        """
        Récupère les informations de crédits depuis le provider.

        Retourne un dict avec les infos de crédits ou None si erreur.
        """
        if not self.is_installed or not self.is_configured:
            return None

        try:
            from django.utils.module_loading import import_string

            # Construire le chemin du provider
            provider_path = (
                f"missive.providers.{self.name}.{self.name.capitalize()}Provider"
            )

            # Cas spéciaux pour les noms avec underscore ou espaces
            if self.name == "django_email":
                provider_path = "missive.providers.django_email.DjangoEmailProvider"
            elif self.name == "smspartner":
                provider_path = "missive.providers.smspartner.SMSPartnerProvider"

            # Importer et instancier le provider
            provider_class = import_string(provider_path)
            provider_instance = provider_class()

            # Récupérer le statut du service
            status_info = provider_instance.get_service_status()

            return status_info.get("credits")

        except Exception:
            return None
