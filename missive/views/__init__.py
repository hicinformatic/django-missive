"""
Views pour Django Missive.

Seuls les webhooks sont nécessaires pour la bibliothèque.
Pour des vues CRUD, consultez examples/secure_views.py
"""

from .webhooks import WebhookView, webhook_status_view, webhook_test_view

__all__ = [
    "WebhookView",
    "webhook_status_view",
    "webhook_test_view",
]
