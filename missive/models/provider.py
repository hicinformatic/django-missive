"""Virtual provider model for admin display (not persisted)."""

import importlib

from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db import models
from django.db.models.query import QuerySet
from django.db.models.sql import Query
from django.utils.translation import gettext_lazy as _

from ..providers import normalize_provider_path


class ProviderInfoQuerySet(QuerySet):
    """In-memory QuerySet for provider info."""

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
        """Filters providers with Django lookup support."""
        rslt = self._result_cache

        for lookup, value in kwargs.items():
            if "__" in lookup:
                field_name, lookup_type = lookup.rsplit("__", 1)

                if lookup_type == "icontains":
                    rslt = [
                        obj
                        for obj in rslt
                        if value.lower() in str(getattr(obj, field_name, "")).lower()
                    ]
                elif lookup_type == "contains":
                    rslt = [
                        obj
                        for obj in rslt
                        if value in str(getattr(obj, field_name, ""))
                    ]
                elif lookup_type == "exact":
                    rslt = [obj for obj in rslt if getattr(obj, field_name) == value]
                elif lookup_type == "in":
                    rslt = [obj for obj in rslt if getattr(obj, field_name) in value]
                else:
                    pass
            else:
                rslt = [obj for obj in rslt if getattr(obj, lookup, None) == value]

        return self.__class__(
            self.model,
            rslt,
            self.query.clone(),
            using=self._db,
            hints=self._hints,
        )

    def order_by(self, *fields):
        """Sorts providers."""
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
        """Get a unique provider"""
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
    """Custom manager that returns our in-memory QuerySet"""

    def get_queryset(self):
        # Load providers from settings using python-missive helper
        try:
            from python_missive.helpers import get_provider_paths_from_config
            from python_missive.providers import get_provider_name_from_path
            from django.conf import settings as dj_settings
            configured = getattr(dj_settings, "MISSIVE_PROVIDERS", None) or []
            provider_paths = (
                list(configured.keys()) if isinstance(configured, dict) else configured
            )
            mapping = get_provider_paths_from_config(provider_paths)
            providers_by_type = {k: v for k, v in mapping.items()}
        except Exception:
            providers_by_type = {}
            # Fallback name extraction if python-missive is not available

            def get_provider_name_from_path(path):
                return path.split(".")[-2] if "." in path else path

        # Group providers by name (a provider can support multiple types)
        # Use get_provider_name_from_path for consistent name normalization
        providers_dict = {}
        for missive_type, provider_paths in sorted(providers_by_type.items()):
            for path in provider_paths:
                name = get_provider_name_from_path(path)
                if name not in providers_dict:
                    providers_dict[name] = []
                providers_dict[name].append(missive_type)

        # Build provider list with all their missive types
        # Use name as pk for URL generation
        providers_list = []
        for provider_name, missive_types in sorted(providers_dict.items()):
            provider = ProviderInfo(
                pk=provider_name,  # Use name as pk for URL generation
                name=provider_name,
                missive_type=",".join(
                    missive_types
                ),  # Store type list for display
            )
            providers_list.append(provider)

        # Return an in-memory QuerySet clone
        return ProviderInfoQuerySet(model=self.model, data=providers_list)


class ProviderInfo(models.Model):
    """
    Virtual model (not persisted) representing a configured provider.
    Data comes from MISSIVE_PROVIDERS, not from the database.
    """

    name = models.CharField(
        max_length=100,
        verbose_name=_("Provider Name"),
    )
    missive_type = models.CharField(
        max_length=50,
        verbose_name=_("Missive Type"),
    )

    objects = ProviderInfoManager()

    class Meta:
        managed = False  # No database table
        verbose_name = _("Provider")
        verbose_name_plural = _("Providers")
        default_permissions = ()  # No add/change/delete permissions
        ordering = ["name"]  # Alphabetical sorting by name

    def __str__(self):
        return f"{self.name} ({self.missive_type})"

    @property
    def missive_types_list(self):
        """Returns the list of supported missive types"""
        if not self.missive_type:
            return []
        return [t.strip() for t in self.missive_type.split(",")]

    def _get_provider_class(self):
        """
        Helper to retrieve the provider class dynamically.
        Returns None if the provider cannot be loaded.

        Searches in MISSIVE_PROVIDERS and loads through python-missive loader.
        """
        try:
            from django.conf import settings
            from python_missive.providers import load_provider_class

            providers_config = getattr(settings, "MISSIVE_PROVIDERS", None) or []
            candidate_paths = (
                list(providers_config.keys())
                if isinstance(providers_config, dict)
                else providers_config
            )
            name_token = self.name.lower().replace(" ", "")
            for path in candidate_paths:
                if name_token in path.lower():
                    return load_provider_class(path)
            return None

        except Exception:
            return None

    @property
    def required_packages(self):
        """
        Returns the list of required Python packages for this provider.
        Gets required_packages directly from the provider class.
        """
        provider_class = self._get_provider_class()
        if provider_class is None:
            return []
        return getattr(provider_class, "required_packages", [])

    @property
    def is_installed(self):
        """Checks if all required Python packages are installed."""
        packages = self.required_packages
        if not packages:
            return True  # No dependency or always available

        for package in packages:
            try:
                importlib.import_module(package)
            except ImportError:
                return False
        return True

    @property
    def required_config_keys(self):
        """
        Returns the list of required environment variables.
        Gets config_keys directly from the provider class.
        """
        provider_class = self._get_provider_class()
        if provider_class is None:
            return []
        return getattr(provider_class, "config_keys", [])

    @property
    def brands(self):
        """
        Returns the list of supported messaging brands (for BRANDED type).
        Gets brands directly from the provider class.
        """
        provider_class = self._get_provider_class()
        if provider_class is None:
            return []
        return getattr(provider_class, "brands", [])

    @property
    def status_url(self):
        """
        Returns the provider status/SLA page URL.
        Gets status_url directly from the provider class.
        """
        provider_class = self._get_provider_class()
        if provider_class is None:
            return None
        return getattr(provider_class, "status_url", None)

    @property
    def documentation_url(self):
        """
        Returns the provider API documentation URL.
        Gets documentation_url directly from the provider class.
        """
        provider_class = self._get_provider_class()
        if provider_class is None:
            return None
        return getattr(provider_class, "documentation_url", None)

    @property
    def site_url(self):
        """
        Returns the provider official website URL.
        Gets site_url directly from the provider class.
        """
        provider_class = self._get_provider_class()
        if provider_class is None:
            return None
        return getattr(provider_class, "site_url", None)

    @property
    def description_text(self):
        """
        Returns the provider textual description.
        Gets description_text directly from the provider class.
        """
        provider_class = self._get_provider_class()
        if provider_class is None:
            return None
        return getattr(provider_class, "description_text", None)

    @property
    def config_status(self):
        """Returns the configuration status for each variable"""
        # Sensitive keys that should not be displayed
        sensitive_keywords = ["password", "secret", "key", "token", "credential"]
        config_vars = {}
        for key in self.required_config_keys:
            # B105: getattr on settings is safe, settings are controlled
            value = getattr(settings, key, None)  # nosec B105
            is_sensitive = any(
                keyword in key.lower() for keyword in sensitive_keywords
            )
            config_vars[key] = {
                "configured": bool(value),
                "value": "***HIDDEN***" if is_sensitive and value else value,
            }
        return config_vars

    @property
    def is_configured(self):
        """Checks if the main credentials are configured"""
        # Dictionary of configuration key names (not passwords, just key names)
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

        # B105: getattr on settings is safe, settings are controlled
        return hasattr(settings, key) and bool(getattr(settings, key, None))  # nosec B105

    @property
    def status(self):
        """Returns the status: ready, needs_config, not_installed"""
        if self.is_installed and self.is_configured:
            return "ready"
        elif self.is_installed and not self.is_configured:
            return "needs_config"
        else:
            return "not_installed"

    @property
    def status_display(self):
        """Status label"""
        labels = {
            "ready": _("✅ Ready"),
            "needs_config": _("⚠️ Configuration Required"),
            "not_installed": _("❌ Not Installed"),
        }
        return labels.get(self.status, _("❓ Unknown"))

    @property
    def usage_count(self):
        """Number of uses of this provider"""
        from .event import MissiveEvent

        return MissiveEvent.objects.filter(provider=self.name).count()

    @property
    def requirements_file(self):
        """Corresponding requirements file"""
        # Mapping provider → individual requirements file
        mapping = {
            # Email Providers (individual files)
            "sendgrid": "requirements-sendgrid.txt",
            "mailgun": "requirements-mailgun.txt",
            "brevo": "requirements-brevo.txt",
            "ses": "requirements-ses.txt",
            "django_email": "requirements.txt",  # Always available
            # SMS Providers (individual files)
            "twilio": "requirements-twilio.txt",
            "vonage": "requirements-vonage.txt",
            "smspartner": "requirements.txt",  # Uses requests (already in core)
            # Branded messaging (individual files)
            "slack": "requirements-slack.txt",
            "teams": "requirements-teams.txt",
            "telegram": "requirements-telegram.txt",
            "signal": "requirements.txt",  # Uses requests (already in core)
            "messenger": "requirements.txt",  # Uses requests (already in core)
            # Push (individual files)
            "fcm": "requirements-fcm.txt",
            "apn": "requirements-apn.txt",
            # Postal (use requests + reportlab/Pillow already in core)
            "laposte": "requirements.txt",
            "ar24": "requirements.txt",
            "certeurope": "requirements.txt",
        }
        return mapping.get(self.name, "requirements.txt")

    @property
    def credits_info(self):
        """
        Get credit information from the provider.

        Returns a dict with credit info or None if error.
        """
        if not self.is_installed or not self.is_configured:
            return None

        try:
            from django.utils.module_loading import import_string

            # Construire le chemin du provider
            provider_path = (
                f"python_missive.providers.{self.name}.{self.name.capitalize()}Provider"
            )

            # Special cases for names using underscores or multiple words
            if self.name == "django_email":
                provider_path = "python_missive.providers.django_email.DjangoEmailProvider"
            elif self.name == "smspartner":
                provider_path = "python_missive.providers.smspartner.SMSPartnerProvider"

            provider_path = normalize_provider_path(provider_path)

            # Importer et instancier le provider
            provider_class = import_string(provider_path)
            provider_instance = provider_class()

            # Fetch service status to expose credits information
            status_info = provider_instance.get_service_status()

            return status_info.get("credits")

        except Exception:
            return None
