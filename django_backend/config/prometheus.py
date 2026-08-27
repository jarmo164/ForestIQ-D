"""Low-cardinality Prometheus instrumentation for ForestIQ operations."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from time import monotonic

from django.db import DatabaseError
from prometheus_client import Counter, Histogram, REGISTRY
from prometheus_client.core import GaugeMetricFamily


HTTP_REQUESTS = Counter(
    "forestiq_http_requests_total",
    "Completed HTTP requests by stable route, method and status class.",
    ("method", "route", "status_class"),
)
HTTP_REQUEST_DURATION = Histogram(
    "forestiq_http_request_duration_seconds",
    "Completed HTTP request duration by stable route and method.",
    ("method", "route"),
)
HTTP_ERRORS = Counter(
    "forestiq_http_errors_total",
    "Completed HTTP requests with an error status by stable route and status class.",
    ("route", "status_class"),
)
CELERY_TASKS = Counter(
    "forestiq_celery_tasks_total",
    "Completed Celery tasks by stable task group and result state.",
    ("task", "state"),
)
CELERY_TASK_DURATION = Histogram(
    "forestiq_celery_task_duration_seconds",
    "Completed Celery task duration by stable task group.",
    ("task",),
)


def stable_route(request) -> str:
    """Return Django's route template, never a request path containing object IDs."""

    resolver_match = getattr(request, "resolver_match", None)
    route = getattr(resolver_match, "route", "") if resolver_match else ""
    return route or "unmatched"


def stable_task_name(task_name: str | None) -> str:
    """Collapse implementation names into a bounded set of task labels."""

    name = task_name or ""
    if name.endswith("run_cadastre_sync"):
        return "cadastre_sync"
    if name.endswith("run_metsaregister_delta_check"):
        return "metsaregister_delta"
    if name.endswith("run_parimus_official_notice_import"):
        return "parimus_notices"
    if name.endswith("enqueue_portfolio_sync"):
        return "portfolio_dispatch"
    if name.endswith("enqueue_all_organizations_portfolio_sync"):
        return "portfolio_beat"
    if name.endswith("enqueue_all_organizations_metsaregister_delta_check"):
        return "metsaregister_delta_beat"
    if name.endswith("enqueue_all_organizations_parimus_official_notice_import"):
        return "parimus_notices_beat"
    return "other"


def stable_source_name(source: str | None) -> str:
    """Map audit sources to bounded labels and explicitly reject dynamic identifiers."""

    value = (source or "").lower()
    if "metsaregister" in value:
        return "metsaregister"
    if "parimus" in value:
        return "parimus"
    if "forestek" in value:
        return "forestek"
    if "cadastre" in value or value in {"api", "daily", "recovery", "all"}:
        return "cadastre"
    if value.startswith("retry:"):
        return "retry"
    if value.startswith("cli:"):
        return "cli"
    return "other"


def observe_http_request(request, *, status_code: int, duration_seconds: float) -> None:
    """Record an HTTP outcome without request-specific labels."""

    route = stable_route(request)
    method = request.method.upper()
    status_class = f"{status_code // 100}xx"
    HTTP_REQUESTS.labels(method=method, route=route, status_class=status_class).inc()
    HTTP_REQUEST_DURATION.labels(method=method, route=route).observe(duration_seconds)
    if status_code >= 400:
        HTTP_ERRORS.labels(route=route, status_class=status_class).inc()


def begin_task_observation(task) -> float:
    """Capture a monotonic start time on the worker-local task request."""

    started_at = monotonic()
    task.request._forestiq_metrics_started_at = started_at
    return started_at


def observe_task_completion(task, *, state: str | None) -> None:
    """Record task duration and result using a bounded task-name label."""

    task_name = stable_task_name(getattr(task, "name", ""))
    task_state = (state or "UNKNOWN").upper()
    started_at = getattr(task.request, "_forestiq_metrics_started_at", None)
    if started_at is not None:
        CELERY_TASK_DURATION.labels(task=task_name).observe(max(0.0, monotonic() - started_at))
        delattr(task.request, "_forestiq_metrics_started_at")
    CELERY_TASKS.labels(task=task_name, state=task_state).inc()


class IntegrationRunCollector:
    """Expose durable sync audit health as scrape-time Prometheus gauges."""

    def describe(self) -> Iterable[GaugeMetricFamily]:
        """Avoid querying Django models while the process registry is still starting."""

        return []

    def collect(self) -> Iterable[GaugeMetricFamily]:
        latest_success = GaugeMetricFamily(
            "forestiq_sync_last_success_timestamp_seconds",
            "Unix timestamp of the latest successful synchronization by source group.",
            labels=("source",),
        )
        failure_streak = GaugeMetricFamily(
            "forestiq_sync_failure_streak",
            "Consecutive terminal non-success synchronization runs by source group.",
            labels=("source",),
        )
        backlog = GaugeMetricFamily(
            "forestiq_sync_backlog_runs",
            "Queued or running synchronization audit rows by source group.",
            labels=("source",),
        )
        cursor_lag = GaugeMetricFamily(
            "forestiq_sync_cursor_lag_seconds",
            "Latest recorded synchronization cursor lag by source group.",
            labels=("source",),
        )
        try:
            from forestry.models import DataSyncRun

            records = DataSyncRun.objects.order_by("source", "-id").values(
                "source", "status", "finished_at", "lag_seconds"
            )
            grouped: dict[str, list[dict]] = defaultdict(list)
            for record in records.iterator():
                grouped[stable_source_name(record["source"])].append(record)
        except DatabaseError:
            grouped = {}

        for source, records_for_source in grouped.items():
            successful = next(
                (record for record in records_for_source if record["status"] == "SUCCESS" and record["finished_at"]),
                None,
            )
            if successful:
                latest_success.add_metric([source], successful["finished_at"].timestamp())

            streak = 0
            for record in records_for_source:
                if record["status"] == "SUCCESS":
                    break
                if record["status"] in {"FAILED", "PARTIAL"}:
                    streak += 1
            failure_streak.add_metric([source], streak)

            queued_or_running = sum(1 for record in records_for_source if record["status"] in {"QUEUED", "RUNNING"})
            backlog.add_metric([source], queued_or_running)

            latest_with_lag = next((record for record in records_for_source if record["lag_seconds"] is not None), None)
            if latest_with_lag:
                cursor_lag.add_metric([source], latest_with_lag["lag_seconds"])

        yield latest_success
        yield failure_streak
        yield backlog
        yield cursor_lag


try:
    REGISTRY.register(IntegrationRunCollector())
except ValueError:
    # Django autoreload can import this module twice in development; retain one collector.
    pass
