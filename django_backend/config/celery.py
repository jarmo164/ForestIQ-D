"""Celery application and correlation propagation for auditable ForestIQ background work."""

from __future__ import annotations

import logging
import os

from celery import Celery
from celery.signals import before_task_publish, task_postrun, task_prerun

from config.observability import (
    current_correlation_id,
    reset_correlation_id,
    safe_correlation_id,
    set_correlation_id,
)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

logger = logging.getLogger(__name__)

app = Celery("forestiq")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@before_task_publish.connect
def attach_correlation_id_to_task(headers=None, **_kwargs) -> None:
    """Propagate the active request trace to every task published from it."""

    if headers is not None:
        headers.setdefault("correlation_id", current_correlation_id() or safe_correlation_id(None))


@task_prerun.connect
def bind_task_correlation_id(task_id=None, task=None, **_kwargs) -> None:
    """Bind the task header to worker-local context before task code and logs run."""

    headers = getattr(task.request, "headers", None) or {}
    correlation_id = headers.get("correlation_id") or current_correlation_id() or safe_correlation_id(None)
    correlation_token = set_correlation_id(safe_correlation_id(correlation_id))
    task.request._forestiq_correlation_token = correlation_token
    logger.info("celery.task.started", extra={"task_name": task.name, "celery_task_id": task_id})


@task_postrun.connect
def clear_task_correlation_id(task_id=None, task=None, state=None, **_kwargs) -> None:
    """Log completion and always clear worker-local trace state for the next task."""

    logger.info(
        "celery.task.finished",
        extra={"task_name": task.name, "celery_task_id": task_id, "task_state": state},
    )
    correlation_token = getattr(task.request, "_forestiq_correlation_token", None)
    if correlation_token is not None:
        reset_correlation_id(correlation_token)
        delattr(task.request, "_forestiq_correlation_token")
