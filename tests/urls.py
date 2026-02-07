"""URL configuration for tests."""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(url="/admin/", permanent=False)),
    path("admin/", admin.site.urls),
    #path("geoaddress/", include("djgeoaddress.urls")),
    path("missive/", include("djpymissive.urls")),
]

admin.site.site_header = "Django CompanyAtlas - Administration"
admin.site.site_title = "Django CompanyAtlas Admin"
admin.site.index_title = "Welcome to Django CompanyAtlas"
