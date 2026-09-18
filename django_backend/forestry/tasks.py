"""Celery task entry points for auditable recurring ForestIQ registry refreshes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from config.observability import current_correlation_id

from accounts.models import Organization
from accounts.organization_context import organization_scope
from forestry.models import Cadastre, DataSyncRun
from forestry.p3_models import WfsLayerManifest
from forestry.services.external_sync import (
    sync_cadastre_wfs,
    sync_metsaregister_wfs,
    sync_optional_soos_wfs,
    sync_parimus_inheritance,
)
from forestry.services.metsaregister_full_import import import_metsaregister_chunk, import_metsaregister_delta
from forestry.services.wfs_generations import ensure_default_manifests, refresh_manifest
from forestry.services.single_flight import SingleFlightLock
from forestry.services.weasel_client import WeaselClientError
from forestry.services.weasel_ownership_sync import import_weasel_ownership_deltas


@dataclass(frozen=True)
class CadastreSyncDispatch:
    """Outcome of scheduling a tenant-scoped cadastre synchronization."""

    run: DataSyncRun | None
    already_running: bool = False


def _start(run: DataSyncRun) -> None:
    now = timezone.now()
    run.status = DataSyncRun.Status.RUNNING
    run.started_at = run.started_at or now
    run.error_message = ""
    run.cursor = {**(run.cursor or {}), "heartbeatAt": now.isoformat()}
    run.save(update_fields=("status", "started_at", "error_message", "cursor"))


def _heartbeat(run: DataSyncRun, *, cursor: dict[str, object] | None = None) -> None:
    """Persist liveness without requiring a schema migration for heartbeat state."""

    payload = dict(run.cursor or {})
    if cursor:
        payload.update(cursor)
    payload["heartbeatAt"] = timezone.now().isoformat()
    run.cursor = payload
    run.save(update_fields=("cursor",))


def _heartbeat_time(run: DataSyncRun):
    value = (run.cursor or {}).get("heartbeatAt")
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if timezone.is_naive(parsed):
                parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
            return parsed
        except ValueError:
            pass
    return run.started_at


def _is_stale_run(run: DataSyncRun, *, now=None) -> bool:
    if run.status != DataSyncRun.Status.RUNNING:
        return False
    heartbeat = _heartbeat_time(run)
    if heartbeat is None:
        return True
    cutoff = (now or timezone.now()) - timedelta(seconds=settings.FORESTIQ_SYNC_RUN_STALE_SECONDS)
    return heartbeat < cutoff


def _fail_stale_run(run: DataSyncRun) -> None:
    _complete(
        run,
        run.result or {},
        status=DataSyncRun.Status.FAILED,
        error_message="Synchronization heartbeat expired; the worker is presumed lost and the run may be retried.",
        pages_processed=run.pages_processed,
        rows_processed=run.rows_processed,
        cursor=run.cursor or {},
        retry_count=run.retry_count,
    )


@shared_task(name="forestry.tasks.reconcile_stale_sync_runs")
def reconcile_stale_sync_runs() -> dict[str, int]:
    """Fail orphaned RUNNING audit rows so expired Redis locks cannot block dispatch forever."""

    now = timezone.now()
    checked = 0
    recovered = 0
    for organization_id in Organization.objects.filter(is_active=True).values_list("id", flat=True):
        with organization_scope(str(organization_id)):
            for run in DataSyncRun.objects.filter(status=DataSyncRun.Status.RUNNING).iterator():
                checked += 1
                if _is_stale_run(run, now=now):
                    _fail_stale_run(run)
                    recovered += 1
    return {"checked": checked, "recovered": recovered}


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
    """Find a live audit row and retire an orphaned RUNNING row on sight."""

    for run in DataSyncRun.objects.filter(
        cadastre_id=cadastre_id,
        status__in=(DataSyncRun.Status.QUEUED, DataSyncRun.Status.RUNNING),
    ).order_by("-id"):
        if _is_stale_run(run):
            _fail_stale_run(run)
            continue
        return run
    return None


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
def run_metsaregister_full_import(self, organization_id: str, run_id: int | None = None) -> dict[str, object]:
    """Drain one bounded full-import chunk and chain another task until WFS EOF."""

    lock = SingleFlightLock.for_sync("metsaregister-full", organization_id)
    if not lock.acquire():
        return {"status": "already_running", "runId": run_id}
    try:
        with organization_scope(organization_id):
            if run_id is None:
                existing = DataSyncRun.objects.filter(
                    source="celery:metsaregister-full",
                    status__in=(DataSyncRun.Status.QUEUED, DataSyncRun.Status.RUNNING),
                ).order_by("-id").first()
                if existing and not _is_stale_run(existing):
                    return {"status": "already_running", "runId": existing.id}
                if existing and _is_stale_run(existing):
                    _fail_stale_run(existing)
                run = DataSyncRun.objects.create(
                    source="celery:metsaregister-full",
                    status=DataSyncRun.Status.QUEUED,
                    task_id=self.request.id or "",
                    correlation_id=current_correlation_id(),
                )
            else:
                run = DataSyncRun.objects.get(id=run_id, source="celery:metsaregister-full")
                if run.status in (DataSyncRun.Status.SUCCESS, DataSyncRun.Status.FAILED):
                    return {"status": run.status, "runId": run.id, **(run.result or {})}
            if run.status == DataSyncRun.Status.QUEUED:
                _start(run)
            else:
                _heartbeat(run)

            try:
                chunk, completed = import_metsaregister_chunk(
                    organization_id=organization_id,
                    run=run,
                    max_features=settings.FORESTIQ_WFS_MAX_FEATURES,
                )
            except Exception as exc:
                _fail(run, exc, retry_count=self.request.retries)
                raise

            aggregate = dict(run.result or {})
            data = chunk.data()
            for key in ("features", "cadastres", "new_subparts", "updated_subparts", "notifications", "skipped_features"):
                aggregate[key] = int(aggregate.get(key, 0)) + int(data.get(key, 0))
            aggregate["resumed_from"] = aggregate.get("resumed_from", data["resumed_from"])
            aggregate["checkpoint_cursor"] = data["checkpoint_cursor"]
            aggregate["checkpoint_pages"] = data["checkpoint_pages"]
            aggregate["completed"] = completed
            run.result = aggregate
            run.pages_processed = data["checkpoint_pages"]
            run.rows_processed = int(aggregate.get("features", 0))
            _heartbeat(run, cursor={"startIndex": data["checkpoint_cursor"]})
            run.result = aggregate
            run.pages_processed = data["checkpoint_pages"]
            run.rows_processed = int(aggregate.get("features", 0))
            run.save(update_fields=("result", "pages_processed", "rows_processed"))

            if completed:
                result = _succeed(
                    run,
                    aggregate,
                    pages_processed=run.pages_processed,
                    rows_processed=run.rows_processed,
                    cursor=run.cursor,
                    retry_count=self.request.retries,
                )
                return {"status": DataSyncRun.Status.SUCCESS, "runId": run.id, **result}

            continuation = run_metsaregister_full_import.apply_async(
                args=[organization_id, run.id],
                countdown=0,
            )
            run.task_id = continuation.id
            run.save(update_fields=("task_id",))
            return {
                "status": "CONTINUE",
                "runId": run.id,
                "nextTaskId": continuation.id,
                "startIndex": data["checkpoint_cursor"],
            }
    finally:
        lock.release()


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
            if not settings.PARIMUS_API_URL or not settings.PARIMUS_API_TOKEN:
                run = DataSyncRun.objects.create(
                    source="celery:parimus-official-notices",
                    status=DataSyncRun.Status.RUNNING,
                    started_at=now,
                    task_id=self.request.id or "",
                    correlation_id=current_correlation_id(),
                )
                return _complete(
                    run,
                    {"status": "not_configured"},
                    status=DataSyncRun.Status.SKIPPED,
                    error_message="Pärimus adapter is not configured.",
                )
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
def enqueue_all_organizations_parimus_official_notice_import() -> dict[str, int | str]:
    """Beat entry point for auditable Pärimus official-notice refreshes."""
    if not settings.PARIMUS_API_URL or not settings.PARIMUS_API_TOKEN:
        return {"organizations": 0, "status": "not_configured"}
    queued = 0
    for organization_id in Organization.objects.filter(is_active=True).values_list("id", flat=True):
        result = run_parimus_official_notice_import.delay(str(organization_id))
        queued += 1 if result else 0
    return {"organizations": queued, "status": "queued"}


@shared_task(bind=True, autoretry_for=(ConnectionError, WeaselClientError), retry_backoff=True, max_retries=settings.FORESTIQ_SYNC_RUN_MAX_RETRIES)
def run_weasel_ownership_delta(self, organization_id: str, cursor: str | None = None) -> dict[str, object]:
    """Drain a bounded Weasel backlog and persist only confirmed cursors."""

    lock = SingleFlightLock.for_sync("weasel-ownership-delta", organization_id)
    if not lock.acquire():
        return {"status": "already_running"}
    try:
        with organization_scope(organization_id):
            if not settings.WEASEL_API_URL or not settings.WEASEL_API_TOKEN:
                run = DataSyncRun.objects.create(
                    source="weasel:ownership-delta",
                    status=DataSyncRun.Status.RUNNING,
                    started_at=timezone.now(),
                    task_id=self.request.id or "",
                    correlation_id=current_correlation_id(),
                )
                return _complete(
                    run,
                    {"status": "not_configured"},
                    status=DataSyncRun.Status.SKIPPED,
                    error_message="Weasel adapter is not configured.",
                )
            previous = DataSyncRun.objects.filter(
                source="weasel:ownership-delta",
                status=DataSyncRun.Status.SUCCESS,
                finished_at__isnull=False,
            ).order_by("-finished_at", "-id").first()
            resume_cursor = cursor if cursor is not None else (str(previous.cursor.get("cursor")) if previous and previous.cursor.get("cursor") else None)
            run = DataSyncRun.objects.create(
                source="weasel:ownership-delta",
                status=DataSyncRun.Status.RUNNING,
                started_at=timezone.now(),
                task_id=self.request.id or "",
                correlation_id=current_correlation_id(),
                cursor={"cursor": resume_cursor} if resume_cursor else {},
            )
            try:
                aggregate: dict[str, object] = {"events": 0, "duplicates": 0, "ignored": 0, "nextCursor": resume_cursor}
                max_pages = max(1, (settings.FORESTIQ_WEASEL_MAX_EVENTS + settings.FORESTIQ_WEASEL_PAGE_SIZE - 1) // settings.FORESTIQ_WEASEL_PAGE_SIZE)
                pages = 0
                current_cursor = resume_cursor
                while pages < max_pages:
                    page_report = import_weasel_ownership_deltas(organization_id=organization_id, cursor=current_cursor)
                    pages += 1
                    for key in ("events", "duplicates", "ignored"):
                        aggregate[key] = int(aggregate[key]) + int(page_report[key])
                    next_cursor = page_report.get("nextCursor")
                    aggregate["nextCursor"] = next_cursor
                    if not next_cursor or next_cursor == current_cursor:
                        break
                    current_cursor = str(next_cursor)
            except Exception as exc:
                _fail(run, exc, retry_count=self.request.retries)
                raise
            next_cursor = aggregate.get("nextCursor")
            return _succeed(
                run,
                aggregate,
                pages_processed=pages,
                rows_processed=int(aggregate["events"]),
                lag_seconds=0,
                cursor={"cursor": next_cursor} if next_cursor else {},
                retry_count=self.request.retries,
            )
    finally:
        lock.release()


@shared_task
def enqueue_all_organizations_weasel_ownership_delta() -> dict[str, int | str]:
    """Beat entry point for separately auditable, opt-in Weasel delta imports."""

    if not settings.WEASEL_API_URL or not settings.WEASEL_API_TOKEN:
        return {"organizations": 0, "status": "not_configured"}
    queued = 0
    for organization_id in Organization.objects.filter(is_active=True).values_list("id", flat=True):
        result = run_weasel_ownership_delta.delay(str(organization_id))
        queued += 1 if result else 0
    return {"organizations": queued, "status": "queued"}


@shared_task(name="forestry.refresh_wfs_generation")
def refresh_wfs_generation(organization_id: str, manifest_id: str, requested_by_id: str | None = None):
    """Stage and publish one WFS layer without mutating the active projection until validation passes."""
    from accounts.models import User

    with organization_scope(organization_id):
        manifest = WfsLayerManifest.objects.get(id=manifest_id, enabled=True)
        actor = User.objects.filter(id=requested_by_id, is_active=True).first() if requested_by_id else None
        generation = refresh_manifest(manifest, created_by=actor)
        return {
            "manifestId": str(manifest.id),
            "generationId": str(generation.id),
            "status": generation.status,
            "featureCount": generation.feature_count,
            "validation": generation.validation,
        }


@shared_task(name="forestry.refresh_all_wfs_generations")
def refresh_all_wfs_generations(organization_id: str, requested_by_id: str | None = None):
    """Refresh configured manifests sequentially so one bad layer cannot invalidate another layer."""
    from accounts.models import User

    result = []
    with organization_scope(organization_id):
        actor = User.objects.filter(id=requested_by_id, is_active=True).first() if requested_by_id else None
        for manifest in ensure_default_manifests(organization_id=organization_id):
            if not manifest.enabled:
                continue
            generation = refresh_manifest(manifest, created_by=actor)
            result.append({
                "manifestId": str(manifest.id),
                "generationId": str(generation.id),
                "status": generation.status,
                "featureCount": generation.feature_count,
                "validation": generation.validation,
            })
    return {"layers": result}
