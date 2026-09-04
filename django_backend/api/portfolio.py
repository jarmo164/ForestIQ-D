"""Metsis portfolio status and synchronization endpoints."""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api.organization import request_organization_id
from api.permissions import IsAdmin
from forestry.models import DataSyncRun
from forestry.portfolio_tasks import SOURCE, dispatch_metsis_portfolio_sync


def _run_payload(run: DataSyncRun | None) -> dict | None:
    if run is None:
        return None
    return {
        "id": run.id,
        "status": run.status,
        "rowsProcessed": run.rows_processed,
        "pagesProcessed": run.pages_processed,
        "cursor": run.cursor,
        "error": run.error_message or None,
        "startedAt": run.started_at,
        "finishedAt": run.finished_at,
        "taskId": run.task_id or None,
        "correlationId": run.correlation_id or None,
    }


@api_view(["GET"])
@permission_classes([IsAdmin])
def portfolio_status(request):
    runs = DataSyncRun.objects.filter(source=SOURCE).order_by("-id")
    latest = runs.first()
    last_success = runs.filter(status=DataSyncRun.Status.SUCCESS).first()
    last_error = runs.filter(status__in=(DataSyncRun.Status.FAILED, DataSyncRun.Status.PARTIAL)).first()
    return Response(
        {
            "configured": True,
            "mode": "RECURRING_PORTFOLIO_SYNC",
            "latestRun": _run_payload(latest),
            "lastSuccess": _run_payload(last_success),
            "lastError": _run_payload(last_error),
            "rowCount": latest.rows_processed if latest else 0,
            "cursor": latest.cursor if latest else {},
        }
    )


@api_view(["POST"])
@permission_classes([IsAdmin])
def portfolio_sync(request):
    dispatch = dispatch_metsis_portfolio_sync(
        organization_id=str(request_organization_id(request)),
        requested_by_id=request.user.id,
    )
    payload = _run_payload(dispatch.run)
    if dispatch.already_running:
        return Response(
            {"detail": "Metsis portfolio synchronization is already running.", "run": payload},
            status=status.HTTP_409_CONFLICT,
        )
    return Response({"run": payload}, status=status.HTTP_202_ACCEPTED)
