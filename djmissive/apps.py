from django.apps import AppConfig


class MissiveConfig(AppConfig):
    """Missive app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "djmissive"
    verbose_name = "Django Missive"

    def ready(self):
        """Imports signal handlers when app is ready."""
        pass
