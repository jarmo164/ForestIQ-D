"""Django Q task entry points for external ForestIQ data refreshes."""

from __future__ import annotations

from django.conf import settings
from django.utils import timezone
from django_q.tasks import async_task

from forestry.models import Cadastre, DataSyncRun
from forestry.services.external_sync import (
    sync_cadastre_wfs,
    sync_forestek_owner_relations,
    sync_metsaregister_wfs,
    sync_optional_soos_wfs,
    sync_parimus_inheritance,
)


def run_cadastre_sync(run_id: int) -> dict[str, object]:
    run = DataSyncRun.objects.select_related("cadastre").get(id=run_id)
    if run.cadastre is None:
        raise ValueError("The requested cadastre no longer exists")
    run.status = DataSyncRun.Status.RUNNING
    run.started_at = timezone.now()
    run.error_message = ""
    run.save(update_fields=("status", "started_at", "error_message"))
    try:
        result = {
            "cadastre_wfs": sync_cadastre_wfs(run.cadastre_id),
            "metsaregister_wfs": sync_metsaregister_wfs(run.cadastre_id),
            "soos_wfs": sync_optional_soos_wfs(run.cadastre_id),
            "forestek_owner_relations": sync_forestek_owner_relations(run.cadastre_id),
            "parimus_inheritance": sync_parimus_inheritance(run.cadastre_id),
        }
    except Exception as exc:
        run.status = DataSyncRun.Status.FAILED
        run.error_message = str(exc)[:4000]
        run.finished_at = timezone.now()
        run.save(update_fields=("status", "error_message", "finished_at"))
        raise
    run.status = DataSyncRun.Status.SUCCEEDED
    run.result = result
    run.finished_at = timezone.now()
    run.save(update_fields=("status", "result", "finished_at"))
    return result


def enqueue_cadastre_sync(cadastre_id: str, *, requested_by_id: str | None = None, source: str = "all") -> DataSyncRun:
    run = DataSyncRun.objects.create(cadastre_id=cadastre_id, requested_by_id=requested_by_id, source=source)
    if settings.FORESTIQ_Q_SYNC_INLINE:
        run_cadastre_sync(run.id)
        return DataSyncRun.objects.get(id=run.id)
    task_id = async_task("forestry.tasks.run_cadastre_sync", run.id, group=f"cadastre:{cadastre_id}")
    run.task_id = str(task_id or "")
    run.save(update_fields=("task_id",))
    return run


def enqueue_portfolio_sync() -> dict[str, int]:
    queued = 0
    for cadastre_id in Cadastre.objects.order_by("id").values_list("id", flat=True):
        enqueue_cadastre_sync(cadastre_id, source="daily")
        queued += 1
    return {"queued": queued}


def run_forestek_owner_relations_sync(run_id: int) -> dict[str, object]:
    """Refresh only Forestek owner–cadastre links for one DataSyncRun."""
    run = DataSyncRun.objects.select_related("cadastre").get(id=run_id)
    if run.cadastre is None:
        raise ValueError("The requested cadastre no longer exists")
    run.status = DataSyncRun.Status.RUNNING
    run.started_at = timezone.now()
    run.error_message = ""
    run.save(update_fields=("status", "started_at", "error_message"))
    try:
        if not settings.FORESTEK_API_URL or not settings.FORESTEK_API_TOKEN:
            result = {"forestek_owner_relations": 0, "skipped": "FORESTEK_API_URL/TOKEN not configured"}
        else:
            result = {"forestek_owner_relations": sync_forestek_owner_relations(run.cadastre_id)}
    except Exception as exc:
        run.status = DataSyncRun.Status.FAILED
        run.error_message = str(exc)[:4000]
        run.finished_at = timezone.now()
        run.save(update_fields=("status", "error_message", "finished_at"))
        raise
    run.status = DataSyncRun.Status.SUCCEEDED
    run.result = result
    run.finished_at = timezone.now()
    run.save(update_fields=("status", "result", "finished_at"))
    return result


def enqueue_forestek_owner_relations_sync(
    cadastre_id: str, *, requested_by_id: str | None = None
) -> DataSyncRun:
    run = DataSyncRun.objects.create(
        cadastre_id=cadastre_id,
        requested_by_id=requested_by_id,
        source="forestek_owner_relations",
    )
    if settings.FORESTIQ_Q_SYNC_INLINE:
        run_forestek_owner_relations_sync(run.id)
        return DataSyncRun.objects.get(id=run.id)
    task_id = async_task(
        "forestry.tasks.run_forestek_owner_relations_sync",
        run.id,
        group=f"forestek:{cadastre_id}",
    )
    run.task_id = str(task_id or "")
    run.save(update_fields=("task_id",))
    return run


def enqueue_forestek_portfolio_sync() -> dict[str, int | str]:
    """Queue Forestek owner–cadastre refreshes for every known cadastre."""
    if not settings.FORESTEK_API_URL or not settings.FORESTEK_API_TOKEN:
        return {"queued": 0, "skipped": "FORESTEK_API_URL/TOKEN not configured"}
    queued = 0
    for cadastre_id in Cadastre.objects.order_by("id").values_list("id", flat=True):
        enqueue_forestek_owner_relations_sync(cadastre_id)
        queued += 1
    return {"queued": queued}
