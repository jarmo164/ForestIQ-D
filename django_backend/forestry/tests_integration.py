"""Integration tests that must run against the Quality Gate PostGIS and Redis services."""

from __future__ import annotations

from uuid import uuid4

from celery.contrib.testing.worker import start_worker
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.test import SimpleTestCase, TestCase

from config.celery import app
from forestry.models import Cadastre
from forestry.services.single_flight import SingleFlightLock


@app.task(name="forestiq.tests.integration_echo")
def integration_echo(value: str) -> str:
    """Minimal task used to verify broker-to-worker-to-result-backend delivery."""

    return value


class PostGISSpatialIntegrationTests(TestCase):
    def test_boundary_intersection_uses_the_postgis_geometry_backend(self):
        boundary = MultiPolygon(
            Polygon(((500000, 6400000), (500100, 6400000), (500100, 6400100), (500000, 6400100), (500000, 6400000))),
            srid=3301,
        )
        Cadastre.objects.create(id="QA02:POSTGIS:001", boundary=boundary)
        probe = Polygon(((500050, 6400050), (500150, 6400050), (500150, 6400150), (500050, 6400150), (500050, 6400050)), srid=3301)

        matches = Cadastre.objects.filter(boundary__intersects=probe).values_list("id", flat=True)

        self.assertEqual(list(matches), ["QA02:POSTGIS:001"])


class RedisSingleFlightIntegrationTests(SimpleTestCase):
    def test_redis_enforces_one_token_owned_sync_lock_at_a_time(self):
        scope = f"qa02-{uuid4().hex}"
        first = SingleFlightLock.for_sync("qa02-integration", "quality-gate", scope)
        second = SingleFlightLock.for_sync("qa02-integration", "quality-gate", scope)

        self.assertTrue(first.acquire())
        self.assertFalse(second.acquire())
        self.assertEqual(first.client.get(first.key), first.token)
        first.release()
        self.assertTrue(second.acquire())
        second.release()


class CeleryRedisIntegrationTests(SimpleTestCase):
    def test_real_celery_worker_round_trip_uses_redis_broker_and_result_backend(self):
        value = f"qa02-{uuid4().hex}"

        with start_worker(app, pool="solo", concurrency=1, perform_ping_check=False, loglevel="WARNING"):
            result = integration_echo.delay(value)
            self.assertEqual(result.get(timeout=15), value)
