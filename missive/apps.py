from django.apps import AppConfig


class MissiveConfig(AppConfig):
    """Configuration for the Missive app"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "missive"
    verbose_name = "Django Missive"

    def ready(self):
        """
        Import signal handlers when the app is ready
        """
        # Import signals here if needed
        # from . import signals
        pass
