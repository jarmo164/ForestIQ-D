"""Celery task entry points for auditable recurring ForestIQ registry refreshes."""

from __future__ import annotations

from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from accounts.models import Organization
from accounts.organization_context import organization_scope
from forestry.models import Cadastre, DataSyncRun
from forestry.services.external_sync import (
    sync_cadastre_wfs,
    sync_metsaregister_wfs,
    sync_optional_soos_wfs,
    sync_parimus_inheritance,
)
from forestry.services.metsaregister_full_import import import_metsaregister_delta


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
def run_cadastre_sync(self, run_id: int, organization_id: str) -> dict[str, object]:
    """Refresh recurring public registry data; Forestek is deliberately excluded."""

    with organization_scope(organization_id):
        run = DataSyncRun.objects.select_related("cadastre").get(id=run_id)
        if run.cadastre is None:
            raise ValueError("The requested cadastre no longer exists")
        _start(run)
        try:
            result = {
                "cadastre_wfs": sync_cadastre_wfs(run.cadastre_id, organization_id=organization_id),
                "metsaregister_wfs": sync_metsaregister_wfs(run.cadastre_id, organization_id=organization_id),
                "soos_wfs": sync_optional_soos_wfs(run.cadastre_id, organization_id=organization_id),
                "parimus_inheritance": sync_parimus_inheritance(run.cadastre_id, organization_id=organization_id),
            }
        except Exception as exc:
            _fail(run, exc)
            raise
        return _succeed(run, result)


def enqueue_cadastre_sync(
    cadastre_id: str,
    *,
    organization_id: str,
    requested_by_id: str | None = None,
    source: str = "all",
) -> DataSyncRun:
    """Create and dispatch one audit row under an explicit organization context."""

    with organization_scope(organization_id):
        cadastre = Cadastre.objects.get(id=cadastre_id)
        run = DataSyncRun.objects.create(cadastre=cadastre, requested_by_id=requested_by_id, source=source)
        if settings.FORESTIQ_TASKS_INLINE:
            run_cadastre_sync(run.id, str(organization_id))
            return DataSyncRun.objects.get(id=run.id)
        result = run_cadastre_sync.delay(run.id, str(organization_id))
        run.task_id = result.id
        run.save(update_fields=("task_id",))
        return run


@shared_task
def enqueue_portfolio_sync(organization_id: str) -> dict[str, int]:
    """Queue the scoped portfolio refresh for one organization only."""

    with organization_scope(organization_id):
        queued = 0
        for cadastre_id in Cadastre.objects.order_by("id").values_list("id", flat=True):
            enqueue_cadastre_sync(cadastre_id, organization_id=organization_id, source="daily")
            queued += 1
        return {"queued": queued}


@shared_task
def enqueue_all_organizations_portfolio_sync() -> dict[str, int]:
    """Beat entry point: enumerate active tenants, then dispatch scoped tasks only."""

    queued = 0
    for organization_id in Organization.objects.filter(is_active=True).values_list("id", flat=True):
        result = enqueue_portfolio_sync.delay(str(organization_id))
        queued += 1 if result else 0
    return {"organizations": queued}


@shared_task(bind=True, autoretry_for=(ConnectionError,), retry_backoff=True, max_retries=3)
def run_metsaregister_delta_check(self, organization_id: str) -> dict[str, object]:
    """Periodically query the Metsaregister delta CQL filter and audit newly persisted allocations."""

    with organization_scope(organization_id):
        now = timezone.now()
        previous = DataSyncRun.objects.filter(source="celery:metsaregister-cql-delta", status=DataSyncRun.Status.SUCCEEDED, finished_at__isnull=False).order_by("-finished_at").first()
        since = (previous.finished_at - timedelta(minutes=settings.FORESTIQ_METSAREGISTER_DELTA_OVERLAP_MINUTES)) if previous else now - timedelta(hours=settings.FORESTIQ_METSAREGISTER_DELTA_LOOKBACK_HOURS)
        run = DataSyncRun.objects.create(source="celery:metsaregister-cql-delta", status=DataSyncRun.Status.RUNNING, started_at=now)
        try:
            report = import_metsaregister_delta(since=since, organization_id=organization_id)
            result = {**report.data(), "since": since.isoformat()}
        except Exception as exc:
            _fail(run, exc)
            raise
        return _succeed(run, result)


@shared_task
def enqueue_all_organizations_metsaregister_delta_check() -> dict[str, int]:
    """Beat entry point for separately auditable, organization-scoped delta checks."""

    queued = 0
    for organization_id in Organization.objects.filter(is_active=True).values_list("id", flat=True):
        result = run_metsaregister_delta_check.delay(str(organization_id))
        queued += 1 if result else 0
    return {"organizations": queued}
