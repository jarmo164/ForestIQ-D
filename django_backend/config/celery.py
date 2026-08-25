"""Celery application for auditable ForestIQ background work."""

from __future__ import annotations

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("forestiq")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
