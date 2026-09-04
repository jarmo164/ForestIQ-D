"""Root URL configuration for the ForestIQ Django service."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView

from .metrics_views import prometheus_metrics

urlpatterns = [
    path("metrics", prometheus_metrics, name="prometheus-metrics"),
    path("django-admin/", admin.site.urls),
    path(
        "api/v1/schema/",
        SpectacularAPIView.as_view(urlconf="config.api_v1_urls"),
        name="openapi-v1-schema",
    ),
    path("api/v1/", include("api.overrides_urls")),
    path("api/v1/", include("api.urls")),
    path("api/", include("api.overrides_urls")),
    path("api/", include("api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
