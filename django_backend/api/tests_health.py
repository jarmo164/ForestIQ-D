"""Regression tests for distinct operational health and SLO alert surfaces."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

import yaml
from django.test import SimpleTestCase, override_settings
from django.utils import timezone

from api.health import _integration_payload
from forestry.models import DataSyncRun


class HealthEndpointTests(SimpleTestCase):
    def test_liveness_is_public_and_never_checks_dependencies(self):
        with patch("api.health._database_ready") as database_check, patch("api.health._redis_ready") as redis_check:
            response = self.client.get("/api/health/live")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"status": "OK", "check": "liveness"})
        database_check.assert_not_called()
        redis_check.assert_not_called()

    @patch("api.health._redis_ready", return_value=(True, None))
    @patch("api.health._database_ready", return_value=(True, None))
    def test_readiness_requires_database_and_redis(self, database_check, redis_check):
        response = self.client.get("/api/health/ready")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["dependencies"]["database"]["status"], "OK")
        self.assertEqual(response.data["dependencies"]["redis"]["status"], "OK")
        database_check.assert_called_once()
        redis_check.assert_called_once()

    @patch("api.health._redis_ready", return_value=(False, "unavailable"))
    @patch("api.health._database_ready", return_value=(True, None))
    def test_readiness_returns_503_when_a_dependency_is_unavailable(self, _database_check, _redis_check):
        response = self.client.get("/api/health/ready")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["status"], "ERROR")
        self.assertEqual(response.data["dependencies"]["redis"], {"status": "ERROR", "reason": "unavailable"})


class IntegrationHealthTests(SimpleTestCase):
    @override_settings(FORESTIQ_INTEGRATION_STALE_AFTER_SECONDS=3600)
    def test_recent_success_is_healthy_and_terminal_failure_streak_is_degraded(self):
        recent_success = {
            "source": "celery:metsaregister-cql-delta",
            "status": DataSyncRun.Status.SUCCESS,
            "finished_at": timezone.now() - timedelta(minutes=5),
            "lag_seconds": 120,
        }
        healthy = _integration_payload([recent_success])
        failure = {
            "source": "celery:metsaregister-cql-delta",
            "status": DataSyncRun.Status.FAILED,
            "finished_at": timezone.now(),
            "lag_seconds": None,
        }
        degraded = _integration_payload([failure, recent_success])

        self.assertEqual(healthy["health"], "OK")
        self.assertEqual(healthy["lagSeconds"], 120)
        self.assertEqual(degraded["health"], "DEGRADED")
        self.assertEqual(degraded["failureStreak"], 1)

    @override_settings(FORESTIQ_INTEGRATION_STALE_AFTER_SECONDS=60)
    def test_old_success_is_reported_as_degraded_without_calling_the_provider(self):
        stale = _integration_payload(
            [
                {
                    "source": "celery:parimus-official-notices",
                    "status": DataSyncRun.Status.SUCCESS,
                    "finished_at": timezone.now() - timedelta(minutes=2),
                    "lag_seconds": None,
                }
            ]
        )

        self.assertEqual(stale["source"], "parimus")
        self.assertEqual(stale["health"], "DEGRADED")


class SloAlertRuleTests(SimpleTestCase):
    def test_rule_file_contains_all_required_operational_alerts(self):
        rule_file = Path(__file__).resolve().parents[2] / "observability" / "prometheus" / "forestiq-alerts.yml"
        payload = yaml.safe_load(rule_file.read_text(encoding="utf-8"))
        rules = {rule["alert"]: rule for group in payload["groups"] for rule in group["rules"]}

        self.assertEqual(
            set(rules),
            {
                "ForestIQIntegrationDataStale",
                "ForestIQIntegrationFailureStreak",
                "ForestIQSyncBacklogGrowing",
                "ForestIQApiErrorRatioHigh",
            },
        )
        self.assertIn("forestiq_sync_last_success_timestamp_seconds", rules["ForestIQIntegrationDataStale"]["expr"])
        self.assertIn("forestiq_sync_failure_streak", rules["ForestIQIntegrationFailureStreak"]["expr"])
        self.assertIn("forestiq_sync_backlog_runs", rules["ForestIQSyncBacklogGrowing"]["expr"])
        self.assertIn("forestiq_http_errors_total", rules["ForestIQApiErrorRatioHigh"]["expr"])
