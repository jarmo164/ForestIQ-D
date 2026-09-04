"""Metsis portfolio status and sync endpoints, independent from Forestek bootstrap import."""

from __future__ import annotations

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from forestry.models import Cadastre, DataSyncRun
from forestry.tasks import enqueue_portfolio_sync

from .organization import request_organization_id
from .permissions import IsAdmin
from .serializers import json_value


def _run_data(run: DataSyncRun | None) -> dict | None:
    if run is None:
        return None
    return {
        "id": run.id,
        "status": run.status,
        "source": run.source,
        "taskId": run.task_id or None,
        "rowsProcessed": run.rows_processed,
        "cursor": run.cursor or {},
        "startedAt": json_value(run.started_at),
        "finishedAt": json_value(run.finished_at),
        "error": run.error_message or None,
    }


@api_view(["GET"])
@permission_classes([IsAdmin])
def portfolio_status(request):
    latest = DataSyncRun.objects.filter(source="daily").order_by("-id").first()
    latest_success = DataSyncRun.objects.filter(
        source="daily", status=DataSyncRun.Status.SUCCESS
    ).order_by("-finished_at", "-id").first()
    latest_failure = DataSyncRun.objects.filter(
        source="daily", status__in=(DataSyncRun.Status.FAILED, DataSyncRun.Status.PARTIAL)
    ).order_by("-finished_at", "-id").first()
    latest_dispatch = DataSyncRun.objects.filter(source="metsis:portfolio-dispatch").order_by("-id").first()
    forestek_bootstrap = DataSyncRun.objects.filter(source__icontains="forestek").order_by("-id").first()

    return Response(
        {
            "configured": True,
            "mode": "RECURRING_PORTFOLIO_SYNC",
            "cadastreCount": Cadastre.objects.count(),
            "latestRun": _run_data(latest),
            "lastSuccessAt": json_value(latest_success.finished_at) if latest_success else None,
            "lastError": latest_failure.error_message if latest_failure else None,
            "rowsProcessed": latest.rows_processed if latest else 0,
            "cursor": latest.cursor if latest else {},
            "latestDispatch": _run_data(latest_dispatch),
            "forestekBootstrap": {
                "configured": bool(settings.FORESTEK_API_URL and settings.FORESTEK_API_TOKEN),
                "completed": bool(forestek_bootstrap and forestek_bootstrap.status == DataSyncRun.Status.SUCCESS),
                "latestRun": _run_data(forestek_bootstrap),
            },
        }
    )


@api_view(["POST"])
@permission_classes([IsAdmin])
def portfolio_sync(request):
    organization_id = str(request_organization_id(request))
    now = timezone.now()
    async_result = enqueue_portfolio_sync.delay(organization_id)
    audit = DataSyncRun.objects.create(
        source="metsis:portfolio-dispatch",
        status=DataSyncRun.Status.SUCCESS,
        task_id=async_result.id or "",
        requested_by=request.user,
        started_at=now,
        finished_at=timezone.now(),
        result={"dispatcherTaskId": async_result.id, "organizationId": organization_id},
        cursor={},
        rows_processed=0,
    )
    return Response(
        {
            "status": "QUEUED",
            "dispatcherTaskId": async_result.id,
            "auditRun": _run_data(audit),
        },
        status=status.HTTP_202_ACCEPTED,
    )
