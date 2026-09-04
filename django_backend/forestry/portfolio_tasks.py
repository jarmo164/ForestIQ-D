"""Audited Metsis portfolio synchronization, independent from one-time Forestek imports."""

from __future__ import annotations

from dataclasses import dataclass

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from accounts.organization_context import organization_scope
from config.observability import current_correlation_id
from forestry.models import Cadastre, DataSyncRun
from forestry.services.single_flight import SingleFlightLock
from forestry.tasks import enqueue_cadastre_sync


SOURCE = "metsis:portfolio"


@dataclass(frozen=True)
class PortfolioSyncDispatch:
    run: DataSyncRun
    already_running: bool = False


def _active_run() -> DataSyncRun | None:
    return (
        DataSyncRun.objects.filter(
            source=SOURCE,
            status__in=(DataSyncRun.Status.QUEUED, DataSyncRun.Status.RUNNING),
        )
        .order_by("-id")
        .first()
    )


@shared_task(bind=True)
def run_metsis_portfolio_sync(self, run_id: int, organization_id: str, lock_token: str = "") -> dict[str, object]:
    """Refresh every cadastre in one organization and persist parent-level progress."""

    with organization_scope(organization_id):
        run = DataSyncRun.objects.get(id=run_id)
        if run.status == DataSyncRun.Status.SUCCESS:
            return run.result

        lock = SingleFlightLock.for_sync("metsis-portfolio", organization_id)
        if lock_token:
            lock.token = lock_token
            acquired = lock.claim_queued_or_recover()
        else:
            acquired = lock.acquire()
        if not acquired:
            return {"status": "already_running", "runId": run.id}

        try:
            run.status = DataSyncRun.Status.RUNNING
            run.started_at = run.started_at or timezone.now()
            run.task_id = self.request.id or run.task_id
            run.error_message = ""
            run.save(update_fields=("status", "started_at", "task_id", "error_message"))

            cadastre_ids = list(Cadastre.objects.order_by("id").values_list("id", flat=True))
            total = len(cadastre_ids)
            succeeded = 0
            failed = 0
            already_running = 0
            failures: list[dict[str, str]] = []

            for index, cadastre_id in enumerate(cadastre_ids, start=1):
                try:
                    dispatch = enqueue_cadastre_sync(
                        cadastre_id,
                        organization_id=organization_id,
                        requested_by_id=run.requested_by_id,
                        source=SOURCE,
                        inline=True,
                    )
                    child = dispatch.run
                    if dispatch.already_running:
                        already_running += 1
                    elif child and child.status == DataSyncRun.Status.SUCCESS:
                        succeeded += 1
                    else:
                        failed += 1
                        failures.append({
                            "cadastreId": cadastre_id,
                            "error": (child.error_message if child else "No child sync run was created")[:1000],
                        })
                except Exception as exc:
                    failed += 1
                    failures.append({"cadastreId": cadastre_id, "error": str(exc)[:1000]})

                run.pages_processed = index
                run.rows_processed = succeeded
                run.cursor = {"index": index, "total": total, "cadastreId": cadastre_id}
                run.backlog_size = max(total - index, 0)
                run.save(update_fields=("pages_processed", "rows_processed", "cursor", "backlog_size"))

            result: dict[str, object] = {
                "total": total,
                "succeeded": succeeded,
                "failed": failed,
                "alreadyRunning": already_running,
                "failures": failures[:100],
            }
            if failed and succeeded:
                final_status = DataSyncRun.Status.PARTIAL
            elif failed:
                final_status = DataSyncRun.Status.FAILED
            else:
                final_status = DataSyncRun.Status.SUCCESS

            run.status = final_status
            run.result = result
            run.error_message = "; ".join(item["error"] for item in failures[:10])[:4000]
            run.finished_at = timezone.now()
            run.backlog_size = 0
            run.cursor = {"index": total, "total": total, "complete": True}
            run.save(
                update_fields=(
                    "status",
                    "result",
                    "error_message",
                    "finished_at",
                    "backlog_size",
                    "cursor",
                )
            )
            return result
        finally:
            lock.release()


def dispatch_metsis_portfolio_sync(*, organization_id: str, requested_by_id: str | None = None, inline: bool | None = None) -> PortfolioSyncDispatch:
    """Create one auditable portfolio run, or return the existing active run."""

    with organization_scope(organization_id):
        active = _active_run()
        if active:
            return PortfolioSyncDispatch(run=active, already_running=True)

        lock = SingleFlightLock.for_sync("metsis-portfolio", organization_id)
        if not lock.acquire():
            active = _active_run()
            if active:
                return PortfolioSyncDispatch(run=active, already_running=True)
            raise RuntimeError("Metsis portfolio synchronization is already locked")

        try:
            total = Cadastre.objects.count()
            run = DataSyncRun.objects.create(
                source=SOURCE,
                requested_by_id=requested_by_id,
                correlation_id=current_correlation_id(),
                cursor={"index": 0, "total": total},
                backlog_size=total,
            )
            run_inline = settings.FORESTIQ_TASKS_INLINE if inline is None else inline
            if run_inline:
                run_metsis_portfolio_sync(run.id, str(organization_id), lock.token)
                return PortfolioSyncDispatch(run=DataSyncRun.objects.get(id=run.id))

            result = run_metsis_portfolio_sync.delay(run.id, str(organization_id), lock.token)
            run.task_id = result.id
            run.save(update_fields=("task_id",))
            return PortfolioSyncDispatch(run=run)
        except Exception:
            lock.release()
            raise
