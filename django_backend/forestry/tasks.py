"""Celery task entry points for auditable recurring ForestIQ registry refreshes."""

from __future__ import annotations

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from forestry.models import Cadastre, DataSyncRun
from forestry.services.external_sync import (
    sync_cadastre_wfs,
    sync_metsaregister_wfs,
    sync_optional_soos_wfs,
    sync_parimus_inheritance,
)


def _start(run: DataSyncRun) -> None:
    run.status = DataSyncRun.Status.RUNNING
    run.started_at = timezone.now()
    run.error_message = ""
    run.save(update_fields=("status", "started_at", "error_message"))


def _fail(run: DataSyncRun, error: Exception) -> None:
    run.status = DataSyncRun.Status.FAILED
    run.error_message = str(error)[:4000]
    run.finished_at = timezone.now()
    run.save(update_fields=("status", "error_message", "finished_at"))


def _succeed(run: DataSyncRun, result: dict[str, object]) -> dict[str, object]:
    run.status = DataSyncRun.Status.SUCCEEDED
    run.result = result
    run.finished_at = timezone.now()
    run.save(update_fields=("status", "result", "finished_at"))
    return result


@shared_task(bind=True, autoretry_for=(ConnectionError,), retry_backoff=True, max_retries=3)
def run_cadastre_sync(self, run_id: int) -> dict[str, object]:
    """Refresh recurring public registry data; Forestek is deliberately excluded."""

    run = DataSyncRun.objects.select_related("cadastre").get(id=run_id)
    if run.cadastre is None:
        raise ValueError("The requested cadastre no longer exists")
    _start(run)
    try:
        result = {
            "cadastre_wfs": sync_cadastre_wfs(run.cadastre_id),
            "metsaregister_wfs": sync_metsaregister_wfs(run.cadastre_id),
            "soos_wfs": sync_optional_soos_wfs(run.cadastre_id),
            "parimus_inheritance": sync_parimus_inheritance(run.cadastre_id),
        }
    except Exception as exc:
        _fail(run, exc)
        raise
    return _succeed(run, result)


def enqueue_cadastre_sync(cadastre_id: str, *, requested_by_id: str | None = None, source: str = "all") -> DataSyncRun:
    run = DataSyncRun.objects.create(cadastre_id=cadastre_id, requested_by_id=requested_by_id, source=source)
    if settings.FORESTIQ_TASKS_INLINE:
        run_cadastre_sync(run.id)
        return DataSyncRun.objects.get(id=run.id)
    result = run_cadastre_sync.delay(run.id)
    run.task_id = result.id
    run.save(update_fields=("task_id",))
    return run


@shared_task
def enqueue_portfolio_sync() -> dict[str, int]:
    queued = 0
    for cadastre_id in Cadastre.objects.order_by("id").values_list("id", flat=True):
        enqueue_cadastre_sync(cadastre_id, source="daily")
        queued += 1
    return {"queued": queued}
