"""Versioned public API URL configuration used by the OpenAPI compatibility contract."""

from django.urls import include, path

urlpatterns = [
    path("api/v1/", include("api.overrides_urls")),
    path("api/v1/", include("api.urls")),
]
