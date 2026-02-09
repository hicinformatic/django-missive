from typing import List
from django.urls import URLPattern, path

from .views.missive import missive_preview, missive_preview_form
from .views.webhook import WebhookView

app_name = "djpymissive"

urlpatterns: List[URLPattern] = [
    path("missive/<uuid:pk>/preview/", missive_preview, name="missive_preview"),
    path("missive/preview/", missive_preview_form, name="missive_preview_form"),
    path("webhook/<str:provider>/", WebhookView.as_view(), name="webhook"),
]
