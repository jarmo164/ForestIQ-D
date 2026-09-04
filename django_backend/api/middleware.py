"""Request-bound organization, validation and observability context middleware."""

from __future__ import annotations

import json
import logging
import re
from time import monotonic

from django.http import JsonResponse

from api.mutation_serializers import MUTATION_RULES, MarkCadastresSerializer, validation_error_payload
from config.observability import current_correlation_id, reset_correlation_id, safe_correlation_id, set_correlation_id
from config.prometheus import observe_http_request

logger = logging.getLogger(__name__)

from accounts.organization_context import (
    require_organization_scope,
    reset_organization,
    reset_organization_scope_requirement,
)


def _normalized_api_path(path: str) -> str:
    if path.startswith("/api/v1/"):
        return "/" + path[len("/api/v1/") :].lstrip("/")
    if path.startswith("/api/"):
        return "/" + path[len("/api/") :].lstrip("/")
    return path


def _request_payload(request):
    content_type = (request.content_type or "").lower()
    if "application/json" in content_type:
        if not request.body:
            return {}
        return json.loads(request.body.decode(request.encoding or "utf-8"))
    if "multipart/form-data" in content_type:
        data = request.POST.dict()
        # MultiValueDict tuleb kopeerida võtmehaaval: dict.update ei säilita
        # kõigis Django request-kontekstides failiobjekti usaldusväärselt.
        for field_name, uploaded_file in request.FILES.items():
            data[field_name] = uploaded_file
        return data
    return None


def _validate_registered_mutation(request):
    path = _normalized_api_path(request.path)
    for method, pattern, serializer_class in MUTATION_RULES:
        if request.method != method or re.fullmatch(pattern, path) is None:
            continue
        try:
            payload = _request_payload(request)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return JsonResponse(
                validation_error_payload(
                    {"body": [f"Malformed JSON: {exc.msg if hasattr(exc, 'msg') else str(exc)}"]},
                    status_code=400,
                    correlation_id=current_correlation_id(),
                ),
                status=400,
            )
        if payload is None:
            return None
        validation_payload = {"cadastres": payload} if serializer_class is MarkCadastresSerializer and isinstance(payload, list) else payload
        serializer = serializer_class(data=validation_payload)
        if not serializer.is_valid():
            return JsonResponse(
                validation_error_payload(
                    serializer.errors,
                    status_code=400,
                    correlation_id=current_correlation_id(),
                ),
                status=400,
            )
        return None
    return None


def _normalize_error_response(response):
    if getattr(response, "status_code", 200) not in {400, 403, 404, 409} or not hasattr(response, "data"):
        return response
    raw = response.data
    payload = dict(raw) if isinstance(raw, dict) else {"detail": raw}
    payload.setdefault("detail", "Request failed.")
    payload.setdefault("code", {
        400: "bad_request",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
    }[response.status_code])
    payload["status"] = response.status_code
    payload.setdefault("correlationId", current_correlation_id() or None)
    response.data = payload
    return response


class TraceContextMiddleware:
    """Attach one safe correlation ID and a consistent API error envelope to each request."""

    header_name = "X-Correlation-ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started_at = monotonic()
        correlation_id = safe_correlation_id(request.headers.get(self.header_name))
        correlation_token = set_correlation_id(correlation_id)
        request.correlation_id = correlation_id
        try:
            response = _validate_registered_mutation(request)
            if response is None:
                response = self.get_response(request)
            response = _normalize_error_response(response)
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
