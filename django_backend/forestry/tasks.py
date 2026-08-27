"""Celery task entry points for auditable recurring ForestIQ registry refreshes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from config.observability import current_correlation_id

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
from forestry.services.single_flight import SingleFlightLock


@dataclass(frozen=True)
class CadastreSyncDispatch:
    """Outcome of scheduling a tenant-scoped cadastre synchronization."""

    run: DataSyncRun | None
    already_running: bool = False


def _start(run: DataSyncRun) -> None:
    run.status = DataSyncRun.Status.RUNNING
    run.started_at = timezone.now()
    run.error_message = ""
    run.save(update_fields=("status", "started_at", "error_message"))


def _metric_total(result: dict[str, object]) -> int:
    """Return an auditable row count from the integer counters in a task result."""

    return sum(value for value in result.values() if isinstance(value, int) and not isinstance(value, bool))


def _complete(
    run: DataSyncRun,
    result: dict[str, object],
    *,
    status: str = DataSyncRun.Status.SUCCESS,
    error_message: str = "",
    pages_processed: int = 0,
    rows_processed: int | None = None,
    cursor: dict[str, object] | None = None,
    lag_seconds: int | None = None,
    retry_count: int = 0,
) -> dict[str, object]:
    """Finish an audit run with normalized outcome and progress metrics."""

    run.status = status
    run.result = result
    run.error_message = error_message[:4000]
    run.pages_processed = pages_processed
    run.rows_processed = _metric_total(result) if rows_processed is None else rows_processed
    run.cursor = cursor or {}
    run.lag_seconds = lag_seconds
    run.retry_count = max(run.retry_count, retry_count)
    run.finished_at = timezone.now()
    run.save(
        update_fields=(
            "status",
            "result",
            "error_message",
            "pages_processed",
            "rows_processed",
            "cursor",
            "lag_seconds",
            "retry_count",
            "finished_at",
        )
    )
    return result


def _fail(run: DataSyncRun, error: Exception, *, retry_count: int = 0) -> None:
    _complete(
        run,
        run.result,
        status=DataSyncRun.Status.FAILED,
        error_message=str(error),
        retry_count=retry_count,
    )


def _succeed(
    run: DataSyncRun,
    result: dict[str, object],
    *,
    pages_processed: int = 0,
    rows_processed: int | None = None,
    cursor: dict[str, object] | None = None,
    lag_seconds: int | None = None,
    retry_count: int = 0,
) -> dict[str, object]:
    return _complete(
        run,
        result,
        pages_processed=pages_processed,
        rows_processed=rows_processed,
        cursor=cursor,
        lag_seconds=lag_seconds,
        retry_count=retry_count,
    )


def _active_cadastre_run(cadastre_id: str) -> DataSyncRun | None:
    """Find the audit row owned by a queued or executing cadastre refresh."""

    return (
        DataSyncRun.objects.filter(
            cadastre_id=cadastre_id,
            status__in=(DataSyncRun.Status.QUEUED, DataSyncRun.Status.RUNNING),
        )
        .order_by("-id")
        .first()
    )


@shared_task(bind=True, autoretry_for=(ConnectionError,), retry_backoff=True, max_retries=3)
def run_cadastre_sync(
    self,
    run_id: int,
    organization_id: str,
    lock_token: str = "",
    source_names: tuple[str, ...] | None = None,
) -> dict[str, object]:
    """Refresh one cadastre while holding the dispatch-created single-flight lock."""

    with organization_scope(organization_id):
        run = DataSyncRun.objects.select_related("cadastre").get(id=run_id)
        if run.cadastre is None:
            raise ValueError("The requested cadastre no longer exists")
        if run.status == DataSyncRun.Status.RUNNING:
            return {"status": "already_running", "runId": run.id}
        if run.status == DataSyncRun.Status.SUCCESS:
            return {"status": "already_finished", "runId": run.id}
        lock = SingleFlightLock.for_sync("cadastre-sync", organization_id, run.cadastre_id)
        if lock_token:
            lock.token = lock_token
            acquired = lock.claim_queued_or_recover()
        else:
            acquired = lock.acquire()
        if not acquired:
            return {"status": "already_running", "runId": run.id}
        try:
            _start(run)
            result: dict[str, object] = {}
            errors: dict[str, str] = {}
            importers = (
                ("cadastre_wfs", sync_cadastre_wfs),
                ("metsaregister_wfs", sync_metsaregister_wfs),
                ("soos_wfs", sync_optional_soos_wfs),
                ("parimus_inheritance", sync_parimus_inheritance),
            )
            selected_importers = tuple(item for item in importers if source_names is None or item[0] in source_names)
            if not selected_importers:
                return _complete(
                    run,
                    {"skipped": "No eligible failed source parts were supplied."},
                    status=DataSyncRun.Status.SKIPPED,
                    cursor={"cadastreId": run.cadastre_id},
                    retry_count=self.request.retries,
                )
            for source, importer in selected_importers:
                try:
                    result[source] = importer(run.cadastre_id, organization_id=organization_id)
                except Exception as exc:  # Keep successful source parts auditable and retryable.
                    errors[source] = str(exc)[:4000]
            if errors:
                result["failed_sources"] = errors
                outcome = DataSyncRun.Status.PARTIAL if len(result) > 1 else DataSyncRun.Status.FAILED
                return _complete(
                    run,
                    result,
                    status=outcome,
                    error_message="; ".join(f"{source}: {message}" for source, message in errors.items()),
                    pages_processed=len(selected_importers),
                    rows_processed=_metric_total({key: value for key, value in result.items() if key != "failed_sources"}),
                    cursor={"cadastreId": run.cadastre_id},
                    retry_count=self.request.retries,
                )
            return _succeed(
                run,
                result,
                pages_processed=len(selected_importers),
                cursor={"cadastreId": run.cadastre_id},
                retry_count=self.request.retries,
            )
        finally:
            lock.release()


def enqueue_cadastre_sync(
    cadastre_id: str,
    *,
    organization_id: str,
    requested_by_id: str | None = None,
    source: str = "all",
    inline: bool | None = None,
    source_names: tuple[str, ...] | None = None,
) -> CadastreSyncDispatch:
    """Schedule a refresh once per tenant and cadastre, returning an existing run on conflict."""

    with organization_scope(organization_id):
        cadastre = Cadastre.objects.get(id=cadastre_id)
        lock = SingleFlightLock.for_sync("cadastre-sync", organization_id, cadastre.id)
        if not lock.acquire():
            return CadastreSyncDispatch(run=_active_cadastre_run(cadastre.id), already_running=True)
        try:
            run = _active_cadastre_run(cadastre.id)
            if run and run.status == DataSyncRun.Status.RUNNING:
                lock.release()
                return CadastreSyncDispatch(run=run, already_running=True)
            if run is None:
                run = DataSyncRun.objects.create(
                    cadastre=cadastre,
                    requested_by_id=requested_by_id,
                    source=source,
                    correlation_id=current_correlation_id(),
                )
            run.backlog_size = DataSyncRun.objects.filter(
                status__in=(DataSyncRun.Status.QUEUED, DataSyncRun.Status.RUNNING)
            ).count()
            run.save(update_fields=("backlog_size",))
            run_inline = settings.FORESTIQ_TASKS_INLINE if inline is None else inline
            if run_inline:
                run_cadastre_sync(run.id, str(organization_id), lock.token, source_names)
                return CadastreSyncDispatch(run=DataSyncRun.objects.get(id=run.id))
            result = run_cadastre_sync.delay(run.id, str(organization_id), lock.token, source_names)
            run.task_id = result.id
            run.save(update_fields=("task_id",))
            return CadastreSyncDispatch(run=run)
        except Exception:
            lock.release()
            raise


@shared_task
def enqueue_portfolio_sync(organization_id: str) -> dict[str, int]:
    """Queue the scoped portfolio refresh for one organization only."""

    with organization_scope(organization_id):
        queued = 0
        already_running = 0
        for cadastre_id in Cadastre.objects.order_by("id").values_list("id", flat=True):
            dispatch = enqueue_cadastre_sync(cadastre_id, organization_id=organization_id, source="daily")
            if dispatch.already_running:
                already_running += 1
            else:
                queued += 1
        return {"queued": queued, "already_running": already_running}


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
    """Run one tenant-scoped Metsaregister delta check, skipping a concurrent run."""

    lock = SingleFlightLock.for_sync("metsaregister-delta", organization_id)
    if not lock.acquire():
        return {"status": "already_running"}
    try:
        with organization_scope(organization_id):
            now = timezone.now()
            previous = DataSyncRun.objects.filter(source="celery:metsaregister-cql-delta", status=DataSyncRun.Status.SUCCESS, finished_at__isnull=False).order_by("-finished_at").first()
            since = (previous.finished_at - timedelta(minutes=settings.FORESTIQ_METSAREGISTER_DELTA_OVERLAP_MINUTES)) if previous else now - timedelta(hours=settings.FORESTIQ_METSAREGISTER_DELTA_LOOKBACK_HOURS)
            run = DataSyncRun.objects.create(
                source="celery:metsaregister-cql-delta",
                status=DataSyncRun.Status.RUNNING,
                started_at=now,
                correlation_id=current_correlation_id(),
            )
            try:
                report = import_metsaregister_delta(since=since, organization_id=organization_id)
                result = {**report.data(), "since": since.isoformat()}
            except Exception as exc:
                _fail(run, exc, retry_count=self.request.retries)
                raise
            return _succeed(
                run,
                result,
                pages_processed=report.checkpoint_pages,
                rows_processed=report.features,
                cursor={"startIndex": report.checkpoint_cursor},
                lag_seconds=max(0, int((now - since).total_seconds())),
                retry_count=self.request.retries,
            )
    finally:
        lock.release()


@shared_task
def enqueue_all_organizations_metsaregister_delta_check() -> dict[str, int]:
    """Beat entry point for separately auditable, organization-scoped delta checks."""

    queued = 0
    for organization_id in Organization.objects.filter(is_active=True).values_list("id", flat=True):
        result = run_metsaregister_delta_check.delay(str(organization_id))
        queued += 1 if result else 0
    return {"organizations": queued}


@shared_task(bind=True, autoretry_for=(ConnectionError,), retry_backoff=True, max_retries=3)
def run_parimus_official_notice_import(self, organization_id: str) -> dict[str, object]:
    """Refresh Pärimus notices for one organization, even without a cadastre delta.

    `InheritanceSignal` uses the provider's notice number together with the
    organization and cadastre as its source key, so repeated polls update the
    same projection instead of creating duplicate notices.
    """

    lock = SingleFlightLock.for_sync("parimus-official-notices", organization_id)
    if not lock.acquire():
        return {"status": "already_running"}
    try:
        with organization_scope(organization_id):
            now = timezone.now()
            run = DataSyncRun.objects.create(
                source="celery:parimus-official-notices",
                status=DataSyncRun.Status.RUNNING,
                started_at=now,
                task_id=self.request.id or "",
                correlation_id=current_correlation_id(),
            )
            try:
                cadastres = Cadastre.objects.order_by("id")
                notices = sum(
                    sync_parimus_inheritance(cadastre.id, organization_id=organization_id)
                    for cadastre in cadastres.iterator()
                )
                result = {"cadastres": cadastres.count(), "notices": notices}
            except Exception as exc:
                _fail(run, exc, retry_count=self.request.retries)
                raise
            return _succeed(
                run,
                result,
                pages_processed=cadastres.count(),
                rows_processed=notices,
                cursor={"cadastres": cadastres.count()},
                retry_count=self.request.retries,
            )
    finally:
        lock.release()


@shared_task
def enqueue_all_organizations_parimus_official_notice_import() -> dict[str, int]:
    """Beat entry point for auditable Pärimus official-notice refreshes."""

    queued = 0
    for organization_id in Organization.objects.filter(is_active=True).values_list("id", flat=True):
        result = run_parimus_official_notice_import.delay(str(organization_id))
        queued += 1 if result else 0
    return {"organizations": queued}
