"""URL configuration for tests."""

from django import get_version
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from djpymissive import __version__
from django.conf import settings


urlpatterns = [
    path("", RedirectView.as_view(url="/admin/", permanent=False)),
    path("admin/", admin.site.urls),
    path("geoaddress/", include("djgeoaddress.urls")),
    path("missive/", include("djpymissive.urls")),
]

admin.site.site_header = (
    f"Django ({get_version()}) Admin Missive ({__version__}) - Administration"
)
admin.site.site_title = f"Django ({get_version()}) Admin Missive ({__version__})"
admin.site.index_title = "Welcome to Django Missive"

if settings.NGROK_PUBLIC_URL:
    admin.site.site_header += f" - {settings.NGROK_PUBLIC_URL}"
