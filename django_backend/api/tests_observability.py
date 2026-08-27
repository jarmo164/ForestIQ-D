"""Regression tests for trace propagation and redaction-safe JSON logging."""

from __future__ import annotations

import json
import logging
from types import SimpleNamespace

from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase

from api.middleware import TraceContextMiddleware
from config.celery import (
    attach_correlation_id_to_task,
    bind_task_correlation_id,
    clear_task_correlation_id,
)
from config.observability import (
    JsonFormatter,
    current_correlation_id,
    reset_correlation_id,
    set_correlation_id,
)
from config.prometheus import CELERY_TASKS


class TraceContextMiddlewareTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_returns_and_clears_valid_client_correlation_id(self):
        seen = []
        middleware = TraceContextMiddleware(lambda _request: seen.append(current_correlation_id()) or HttpResponse())

        response = middleware(self.factory.get("/api/services/status", HTTP_X_CORRELATION_ID="support-trace-001"))

        self.assertEqual(response["X-Correlation-ID"], "support-trace-001")
        self.assertEqual(seen, ["support-trace-001"])
        self.assertEqual(current_correlation_id(), "")

    def test_replaces_unsafe_client_correlation_id(self):
        response = TraceContextMiddleware(lambda _request: HttpResponse())(
            self.factory.get("/api/services/status", HTTP_X_CORRELATION_ID="Bearer secret-token")
        )

        self.assertRegex(response["X-Correlation-ID"], r"^[a-f0-9]{32}$")


class StructuredLoggingTests(SimpleTestCase):
    def test_json_log_redacts_secrets_tokens_and_personal_data(self):
        correlation_token = set_correlation_id("trace-safe-log-01")
        record = logging.LogRecord(
            "forestiq.test",
            logging.WARNING,
            __file__,
            1,
            "authorization=Bearer jwt-value email=owner@example.test personal=37605030299",
            (),
            None,
        )
        record.password = "not-for-logs"
        record.context = {"api_token": "hidden", "owner": "owner@example.test"}
        record.request = "GET /api/services/owners?token=must-not-appear"
        try:
            payload = json.loads(JsonFormatter().format(record))
        finally:
            reset_correlation_id(correlation_token)

        rendered = json.dumps(payload)
        self.assertEqual(payload["correlation_id"], "trace-safe-log-01")
        self.assertNotIn("jwt-value", rendered)
        self.assertNotIn("owner@example.test", rendered)
        self.assertNotIn("37605030299", rendered)
        self.assertNotIn("not-for-logs", rendered)
        self.assertNotIn("must-not-appear", rendered)
        self.assertEqual(payload["password"], "[REDACTED]")
        self.assertEqual(payload["context"]["api_token"], "[REDACTED]")


class CeleryTracePropagationTests(SimpleTestCase):
    def test_published_task_receives_request_trace_and_worker_cleans_it_up(self):
        request_token = set_correlation_id("trace-request-01")
        headers = {}
        attach_correlation_id_to_task(headers=headers)
        reset_correlation_id(request_token)
        task = SimpleNamespace(name="forestry.tasks.run_cadastre_sync", request=SimpleNamespace(headers=headers))

        bind_task_correlation_id(task_id="celery-01", task=task)
        self.assertEqual(current_correlation_id(), "trace-request-01")
        clear_task_correlation_id(task_id="celery-01", task=task, state="SUCCESS")

        self.assertEqual(current_correlation_id(), "")
        samples = CELERY_TASKS.collect()[0].samples
        self.assertTrue(
            any(
                sample.name == "forestiq_celery_tasks_total"
                and sample.labels == {"task": "cadastre_sync", "state": "SUCCESS"}
                for sample in samples
            )
        )

    def test_inline_task_preserves_active_request_trace_when_no_header_exists(self):
        request_token = set_correlation_id("trace-inline-request-01")
        task = SimpleNamespace(name="forestry.tasks.run_cadastre_sync", request=SimpleNamespace(headers={}))
        try:
            bind_task_correlation_id(task_id="celery-inline-01", task=task)
            self.assertEqual(current_correlation_id(), "trace-inline-request-01")
            clear_task_correlation_id(task_id="celery-inline-01", task=task, state="SUCCESS")
            self.assertEqual(current_correlation_id(), "trace-inline-request-01")
        finally:
            reset_correlation_id(request_token)
