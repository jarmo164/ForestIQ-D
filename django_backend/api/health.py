"""Operational health endpoints with explicitly separated dependency scopes."""

from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

import redis
from django.conf import settings
from django.db import connection
from django.db.utils import DatabaseError
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.permissions import IsAdmin
from forestry.models import DataSyncRun
from config.prometheus import stable_source_name


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def liveness(_request):
    """Report only whether this Django process can answer a request."""

    return Response({"status": "OK", "check": "liveness"})


def _database_ready() -> tuple[bool, str | None]:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        return False, "unavailable"
    return True, None


def _redis_ready() -> tuple[bool, str | None]:
    try:
        redis.from_url(settings.CELERY_BROKER_URL, socket_connect_timeout=1, socket_timeout=1).ping()
    except redis.RedisError:
        return False, "unavailable"
    return True, None


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def readiness(_request):
    """Report whether local serving dependencies (database and broker) are usable."""

    database_ok, database_error = _database_ready()
    redis_ok, redis_error = _redis_ready()
    dependencies = {
        "database": {"status": "OK" if database_ok else "ERROR"},
        "redis": {"status": "OK" if redis_ok else "ERROR"},
    }
    if database_error:
        dependencies["database"]["reason"] = database_error
    if redis_error:
        dependencies["redis"]["reason"] = redis_error
    healthy = database_ok and redis_ok
    return Response(
        {"status": "OK" if healthy else "ERROR", "check": "readiness", "dependencies": dependencies},
        status=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
    )


def _integration_payload(records: list[dict]) -> dict:
    """Build a bounded per-source state from durable audit rows without external calls."""

    latest = records[0]
    latest_success = next(
        (record for record in records if record["status"] == DataSyncRun.Status.SUCCESS and record["finished_at"]),
        None,
    )
    failure_streak = 0
    for record in records:
        if record["status"] == DataSyncRun.Status.SUCCESS:
            break
        if record["status"] in {DataSyncRun.Status.FAILED, DataSyncRun.Status.PARTIAL}:
            failure_streak += 1
    stale_after = timedelta(seconds=settings.FORESTIQ_INTEGRATION_STALE_AFTER_SECONDS)
    stale = not latest_success or latest_success["finished_at"] < timezone.now() - stale_after
    health = "OK" if not stale and failure_streak == 0 else "DEGRADED"
    return {
        "source": stable_source_name(latest["source"]),
        "health": health,
        "lastStatus": latest["status"],
        "lastSuccessAt": latest_success["finished_at"].isoformat() if latest_success else None,
        "failureStreak": failure_streak,
        "backlogSize": sum(1 for record in records if record["status"] in {DataSyncRun.Status.QUEUED, DataSyncRun.Status.RUNNING}),
        "lagSeconds": next((record["lag_seconds"] for record in records if record["lag_seconds"] is not None), None),
    }


@api_view(["GET"])
@permission_classes([IsAdmin])
def integrations_health(_request):
    """Report data freshness and sync health from the audit trail, never by probing providers."""

    grouped: dict[str, list[dict]] = defaultdict(list)
    for record in DataSyncRun.objects.order_by("source", "-id").values("source", "status", "finished_at", "lag_seconds").iterator():
        grouped[stable_source_name(record["source"])].append(record)
    integrations = [_integration_payload(records) for _, records in sorted(grouped.items())]
    degraded = [item["source"] for item in integrations if item["health"] != "OK"]
    return Response(
        {
            "status": "DEGRADED" if degraded else "OK",
            "check": "integrations",
            "integrations": integrations,
            "degradedSources": degraded,
        }
    )
