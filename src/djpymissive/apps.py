from django.apps import AppConfig


class DjpymissiveConfig(AppConfig):
    """Djpymissive app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "djpymissive"
    verbose_name = "Django Missive"

    def ready(self):
        """Imports signal handlers when app is ready."""
        pass
