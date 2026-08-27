"""Prometheus scrape endpoint for the ForestIQ Django process."""

from __future__ import annotations

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.http import require_GET
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest


@require_GET
def prometheus_metrics(request):
    """Expose the process registry, optionally protected by a fixed scrape token."""

    token = settings.FORESTIQ_METRICS_BEARER_TOKEN
    if token and request.headers.get("Authorization") != f"Bearer {token}":
        return HttpResponseForbidden("Metrics authentication required.")
    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)
