from django.urls import path

from .views import WebhookView, missive_views, webhook_status_view, webhook_test_view

app_name = "missive"

urlpatterns = [
    # Interface CRUD des missives
    path("", missive_views.MissiveListView.as_view(), name="missive-list"),
    path("<int:pk>/", missive_views.MissiveDetailView.as_view(), name="missive-detail"),
    path("create/", missive_views.MissiveCreateView.as_view(), name="missive-create"),
    path(
        "<int:pk>/update/",
        missive_views.MissiveUpdateView.as_view(),
        name="missive-update",
    ),
    path(
        "<int:pk>/delete/",
        missive_views.MissiveDeleteView.as_view(),
        name="missive-delete",
    ),
    # Webhooks
    path(
        "webhooks/status/", webhook_status_view, name="webhook-status"
    ),  # Status check
    path(
        "webhooks/<str:provider>/", WebhookView.as_view(), name="webhook"
    ),  # Endpoint unifié
    # Test (dev only)
    path("webhook/test/", webhook_test_view, name="webhook-test"),
]
