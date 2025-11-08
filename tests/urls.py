"""
URL configuration for testing django-missive
"""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(url="/admin/", permanent=False)),
    path("admin/", admin.site.urls),
    path("missive/", include("missive.urls")),  # Inclut à la fois CRUD et webhooks
]

# Customize admin site
admin.site.site_header = "Django Missive - Administration"
admin.site.site_title = "Django Missive Admin"
admin.site.index_title = "Bienvenue dans Django Missive"
