"""Declarative adapters for administrator-managed external integration work."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from django.conf import settings

from forestry.models import DataSyncRun
from forestry.tasks import enqueue_cadastre_sync, enqueue_portfolio_sync, run_parimus_official_notice_import

from .organization import request_organization_id
from .serializers import json_value


@dataclass(frozen=True)
class IntegrationDispatch:
    payload: dict[str, Any]
    status_code: int


@dataclass(frozen=True)
class IntegrationAdapter:
    """One registered integration and its complete operational declaration."""

    key: str
    label: str
    mode: str
    source_token: str
    configured: Callable[[], bool]
    dispatch: Callable[[Any], IntegrationDispatch] | None = None

    def records(self, organization_id: str):
        return DataSyncRun.objects.filter(organization_id=organization_id, source__icontains=self.source_token).order_by("-id")

    def latest(self, organization_id: str) -> DataSyncRun | None:
        return self.records(organization_id).first()

    def health(self, latest: DataSyncRun | None) -> str:
        if not self.configured():
            return "UNCONFIGURED"
        if latest is None:
            return "UNKNOWN"
        if latest.status in {DataSyncRun.Status.FAILED, DataSyncRun.Status.PARTIAL}:
            return "DEGRADED"
        if latest.status in {DataSyncRun.Status.QUEUED, DataSyncRun.Status.RUNNING}:
            return "PENDING"
        return "OK"

    def row(self, organization_id: str) -> dict[str, Any]:
        latest = self.latest(organization_id)
        return {
            "key": self.key,
            "label": self.label,
            "configured": self.configured(),
            "mode": self.mode,
            "status": latest.status if latest else "NOT_RUN",
            "checkpoint": latest.cursor if latest else None,
            "health": self.health(latest),
            "lastRun": serialize_run(latest) if latest else None,
        }


def serialize_run(item: DataSyncRun) -> dict[str, Any]:
    """Serialize durable run evidence consistently for every registered adapter."""

    return {
        "id": item.id,
        "cadastreId": item.cadastre_id,
        "source": item.source,
        "status": item.status,
        "taskId": item.task_id,
        "correlationId": item.correlation_id or None,
        "pagesProcessed": item.pages_processed,
        "rowsProcessed": item.rows_processed,
        "retryCount": item.retry_count,
        "backlogSize": item.backlog_size,
        "cursor": item.cursor,
        "lagSeconds": item.lag_seconds,
        "retryOf": item.retry_of_id,
        "startedAt": json_value(item.started_at),
        "finishedAt": json_value(item.finished_at),
        "result": item.result,
        "error": item.error_message or None,
    }


def _cadastre_dispatch(request) -> IntegrationDispatch:
    organization_id = str(request_organization_id(request))
    parameters = request.data.get("parameters", {})
    parameters = parameters if isinstance(parameters, dict) else {}
    cadastre_id = str(request.data.get("cadastreId") or parameters.get("cadastreId") or "").strip()
    if cadastre_id:
        dispatch = enqueue_cadastre_sync(
            cadastre_id,
            organization_id=organization_id,
            requested_by_id=request.user.id,
            source="cadastre",
        )
        if dispatch.already_running:
            run = dispatch.run
            return IntegrationDispatch(
                {"key": "CADASTRE", "status": "already_running", "code": "already_running", "runId": run.id if run else None, "taskId": run.task_id if run else "", "correlationId": run.correlation_id if run else None},
                409,
            )
        run = dispatch.run
        return IntegrationDispatch(
            {"key": "CADASTRE", "status": run.status, "runId": run.id, "taskId": run.task_id, "correlationId": run.correlation_id or None},
            202,
        )
    if settings.FORESTIQ_TASKS_INLINE:
        result = enqueue_portfolio_sync(organization_id)
        return IntegrationDispatch({"key": "CADASTRE", "status": "SUCCESS", "result": result}, 202)
    task = enqueue_portfolio_sync.delay(organization_id)
    return IntegrationDispatch({"key": "CADASTRE", "status": "QUEUED", "taskId": task.id}, 202)


def _parimus_dispatch(request) -> IntegrationDispatch:
    organization_id = str(request_organization_id(request))
    if settings.FORESTIQ_TASKS_INLINE:
        result = run_parimus_official_notice_import.run(organization_id)
        return IntegrationDispatch({"key": "PARIMUS", "status": result.get("status", "SUCCESS"), "result": result}, 202)
    task = run_parimus_official_notice_import.delay(organization_id)
    return IntegrationDispatch({"key": "PARIMUS", "status": "QUEUED", "taskId": task.id}, 202)


def _forestek_dispatch(_request) -> IntegrationDispatch:
    return IntegrationDispatch(
        {"detail": "Forestek is a one-time initial import. Run the controlled management command only before its first successful import."},
        409,
    )


class IntegrationRegistry:
    def __init__(self, adapters: tuple[IntegrationAdapter, ...]):
        self._adapters = adapters
        self._by_key = {adapter.key: adapter for adapter in adapters}

    def all(self) -> tuple[IntegrationAdapter, ...]:
        return self._adapters

    def get(self, key: str) -> IntegrationAdapter | None:
        return self._by_key.get(key.upper())

    def rows(self, organization_id: str) -> list[dict[str, Any]]:
        return [adapter.row(organization_id) for adapter in self._adapters]


integration_registry = IntegrationRegistry(
    (
        IntegrationAdapter("CADASTRE", "Cadastre and forest registry", "RECURRING", "cadastre", lambda: True, _cadastre_dispatch),
        IntegrationAdapter("FORESTEK", "Forestek ownership relations", "ONE_TIME", "forestek", lambda: bool(settings.FORESTEK_API_URL and settings.FORESTEK_API_TOKEN), _forestek_dispatch),
        IntegrationAdapter("PARIMUS", "Pärimus official notices", "RECURRING", "parimus", lambda: bool(settings.PARIMUS_API_URL and settings.PARIMUS_API_TOKEN), _parimus_dispatch),
    )
)
