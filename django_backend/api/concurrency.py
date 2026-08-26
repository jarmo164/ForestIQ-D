"""Optimistic locking helpers for versioned ForestIQ aggregates."""
from __future__ import annotations

from django.db.models import F
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response


def requested_version(request) -> int | None:
    """Read the aggregate version from a JSON body or standard If-Match header."""
    raw_value = request.data.get("version") if hasattr(request, "data") else None
    if raw_value is None:
        raw_value = request.headers.get("If-Match", "").strip().strip('"')
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def missing_version_response() -> Response:
    return Response(
        {
            "detail": "A positive aggregate version is required for this change.",
            "code": "version_required",
        },
        status=428,
    )


def version_conflict_response(instance, expected_version: int) -> Response:
    return Response(
        {
            "detail": "This record was changed by another user. Refresh it and try again.",
            "code": "version_conflict",
            "expectedVersion": expected_version,
            "currentVersion": instance.version,
        },
        status=status.HTTP_409_CONFLICT,
    )


def update_if_current(instance, expected_version: int, **changes):
    """Atomically apply changes only when the stored version remains current.

    The returned instance is reloaded with the incremented version. ``None``
    signals that another request committed first.
    """
    model = type(instance)
    if hasattr(instance, "updated_at") and "updated_at" not in changes:
        changes["updated_at"] = timezone.now()
    updated = model.objects.filter(pk=instance.pk, version=expected_version).update(
        **changes,
        version=F("version") + 1,
    )
    if not updated:
        return None
    return model.objects.get(pk=instance.pk)


def delete_if_current(instance, expected_version: int) -> bool:
    """Delete an aggregate only if its stored version is still current."""
    model = type(instance)
    deleted, _ = model.objects.filter(pk=instance.pk, version=expected_version).delete()
    return bool(deleted)
