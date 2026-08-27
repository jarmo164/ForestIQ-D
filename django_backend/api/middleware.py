"""Request-bound organization and observability context lifecycle middleware."""

from __future__ import annotations

import logging
from time import monotonic

from config.observability import reset_correlation_id, safe_correlation_id, set_correlation_id
from config.prometheus import observe_http_request

logger = logging.getLogger(__name__)

from accounts.organization_context import (
    require_organization_scope,
    reset_organization,
    reset_organization_scope_requirement,
)


class TraceContextMiddleware:
    """Attach one safe correlation ID to each HTTP request and response."""

    header_name = "X-Correlation-ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started_at = monotonic()
        correlation_id = safe_correlation_id(request.headers.get(self.header_name))
        correlation_token = set_correlation_id(correlation_id)
        request.correlation_id = correlation_id
        try:
            response = self.get_response(request)
            response[self.header_name] = correlation_id
            observe_http_request(
                request,
                status_code=response.status_code,
                duration_seconds=monotonic() - started_at,
            )
            logger.info(
                "api.request.completed",
                extra={
                    "http_method": request.method,
                    "path": request.path,
                    "http_status": response.status_code,
                },
            )
            return response
        except Exception:
            observe_http_request(request, status_code=500, duration_seconds=monotonic() - started_at)
            logger.error(
                "api.request.unhandled_error",
                extra={"http_method": request.method, "path": request.path},
            )
            raise
        finally:
            reset_correlation_id(correlation_token)


class OrganizationContextMiddleware:
    """Ensure a JWT-authenticated request cannot leak its organization into another request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        required_token = require_organization_scope()
        try:
            return self.get_response(request)
        finally:
            context_token = getattr(request, "_forestiq_organization_context_token", None)
            if context_token is not None:
                reset_organization(context_token)
            reset_organization_scope_requirement(required_token)
