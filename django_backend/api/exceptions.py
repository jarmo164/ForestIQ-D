"""Consistent REST error responses with trace-safe structured logging."""

from __future__ import annotations

import logging

from rest_framework.views import exception_handler

from config.observability import current_correlation_id

logger = logging.getLogger(__name__)


def api_exception_handler(exc, context):
    """Normalize expected API errors and expose their opaque trace identifier."""

    response = exception_handler(exc, context)
    if response is not None:
        detail = response.data.get("detail", response.data)
        correlation_id = current_correlation_id()
        logger.warning(
            "api.request.error",
            extra={
                "http_status": response.status_code,
                "exception_type": type(exc).__name__,
            },
        )
        response.data = {
            "detail": detail,
            "status": response.status_code,
            "correlationId": correlation_id or None,
        }
    return response
