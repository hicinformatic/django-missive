from django.urls import path

from .views import WebhookView, webhook_status_view, webhook_test_view

app_name = "missive"

urlpatterns = [
    path("webhooks/status/", webhook_status_view, name="webhook-status"),
    path("webhooks/<str:provider>/", WebhookView.as_view(), name="webhook"),
    path("webhook/test/", webhook_test_view, name="webhook-test"),
]
