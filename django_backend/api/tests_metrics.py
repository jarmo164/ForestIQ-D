"""Regression tests for the bounded Prometheus metrics endpoint and collectors."""

from __future__ import annotations

import re
from types import SimpleNamespace

from django.test import TestCase, override_settings
from django.urls import ResolverMatch
from django.utils import timezone
from prometheus_client import generate_latest

from forestry.models import DataSyncRun
from config.prometheus import stable_route, stable_source_name, stable_task_name


class PrometheusEndpointTests(TestCase):
    @override_settings(FORESTIQ_METRICS_BEARER_TOKEN="metrics-test-token")
    def test_metrics_endpoint_requires_configured_bearer_token(self):
        denied = self.client.get("/metrics")
        allowed = self.client.get("/metrics", HTTP_AUTHORIZATION="Bearer metrics-test-token")

        self.assertEqual(denied.status_code, 403)
        self.assertEqual(allowed.status_code, 200)
        self.assertIn(b"forestiq_http_requests_total", allowed.content)
        self.assertIn(b"forestiq_celery_tasks_total", allowed.content)

    def test_collector_exports_success_age_failure_streak_backlog_and_cursor_lag(self):
        success = DataSyncRun.objects.create(
            source="celery:metsaregister-cql-delta",
            status=DataSyncRun.Status.SUCCESS,
            finished_at=timezone.now(),
            lag_seconds=120,
        )
        DataSyncRun.objects.create(
            source="celery:metsaregister-cql-delta",
            status=DataSyncRun.Status.FAILED,
            finished_at=timezone.now(),
        )
        DataSyncRun.objects.create(source="celery:metsaregister-cql-delta", status=DataSyncRun.Status.QUEUED)

        payload = generate_latest().decode("utf-8")

        self.assertRegex(payload, r'forestiq_sync_last_success_timestamp_seconds\{source="metsaregister"\} [1-9]')
        self.assertIn('forestiq_sync_failure_streak{source="metsaregister"} 1.0', payload)
        self.assertIn('forestiq_sync_backlog_runs{source="metsaregister"} 1.0', payload)
        self.assertIn('forestiq_sync_cursor_lag_seconds{source="metsaregister"} 120.0', payload)
        self.assertIsNotNone(success.id)


class PrometheusCardinalityTests(TestCase):
    def test_route_source_and_task_labels_exclude_dynamic_identifiers(self):
        request = SimpleNamespace(
            resolver_match=ResolverMatch(
                func=lambda _request: None,
                args=(),
                kwargs={},
                url_name="cadastre-sync",
                app_names=[],
                namespaces=[],
                route="api/services/admin/cadastres/<str:cadastre_id>/sync",
            )
        )

        self.assertEqual(stable_route(request), "api/services/admin/cadastres/<str:cadastre_id>/sync")
        self.assertEqual(stable_source_name("celery:metsaregister-cql-delta"), "metsaregister")
        self.assertEqual(stable_source_name("retry:api:79601:001:9999"), "retry")
        self.assertEqual(stable_task_name("forestry.tasks.run_cadastre_sync"), "cadastre_sync")
        self.assertEqual(stable_task_name("external.task.with.arbitrary.id"), "other")
        self.assertNotRegex(stable_route(request), re.compile(r"79601|9999"))
