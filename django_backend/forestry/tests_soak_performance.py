"""WFS/Celery soak and GIS load budgets for the PostGIS/Redis quality environment."""

from __future__ import annotations

import os
import tracemalloc
from math import ceil
from time import perf_counter, sleep
from unittest.mock import patch

from django.contrib.gis.geos import MultiPolygon, Polygon
from django.db import connection
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from api.auth import token_pair
from forestry.models import Cadastre, DataSyncRun
from forestry.services.single_flight import SingleFlightLock
from forestry.tasks import enqueue_cadastre_sync


def percentile_ms(samples: list[float], percentile: float) -> float:
    ordered = sorted(samples)
    return ordered[max(ceil(len(ordered) * percentile) - 1, 0)] * 1000


def postgres_connection_count() -> int:
    if connection.vendor != "postgresql":
        return 0
    with connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()")
        return int(cursor.fetchone()[0])


def authenticated_client(user: User) -> APIClient:
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_pair(user)['actualToken']['token']}")
    return client


class WfsCelerySoakTests(TestCase):
    """Exercise repeated WFS work, a failed retry cycle and overlapping scheduling."""

    def setUp(self):
        self.user = User.objects.create_superuser("soak-admin", "Soak administrator", "very-secure-admin-password")
        self.organization_id = str(self.user.default_organization_id)
        self.cadastre = Cadastre.objects.create(id="SOAK:001", name="Soak parcel")

    @patch("forestry.tasks.sync_cadastre_wfs")
    def test_long_import_failure_retry_and_overlap_are_bounded(self, sync_cadastre_wfs):
        iterations = int(os.getenv("FORESTIQ_SOAK_WFS_ITERATIONS", "50"))
        max_seconds = float(os.getenv("FORESTIQ_SOAK_WFS_MAX_SECONDS", "5"))
        calls = 0

        def repeated_import(*_args, **_kwargs):
            nonlocal calls
            calls += 1
            sleep(0.005)
            if calls == 1:
                raise ConnectionError("simulated transient WFS failure")
            return {"rows": 10, "cursor": calls}

        sync_cadastre_wfs.side_effect = repeated_import
        started = perf_counter()
        first = enqueue_cadastre_sync(
            self.cadastre.id,
            organization_id=self.organization_id,
            requested_by_id=self.user.id,
            source="soak:wfs",
            inline=True,
            source_names=("cadastre_wfs",),
        )
        self.assertEqual(first.run.status, DataSyncRun.Status.FAILED)

        retry = enqueue_cadastre_sync(
            self.cadastre.id,
            organization_id=self.organization_id,
            requested_by_id=self.user.id,
            source="soak:wfs:retry",
            inline=True,
            source_names=("cadastre_wfs",),
        )
        self.assertEqual(retry.run.status, DataSyncRun.Status.SUCCESS)

        for _ in range(max(iterations - 2, 0)):
            retry = enqueue_cadastre_sync(
                self.cadastre.id,
                organization_id=self.organization_id,
                requested_by_id=self.user.id,
                source="soak:wfs:repeat",
                inline=True,
                source_names=("cadastre_wfs",),
            )
            self.assertEqual(retry.run.status, DataSyncRun.Status.SUCCESS)

        elapsed = perf_counter() - started
        self.assertLessEqual(elapsed, max_seconds)

        queued = DataSyncRun.objects.create(cadastre=self.cadastre, source="soak:overlap")
        lock = SingleFlightLock.for_sync("cadastre-sync", self.organization_id, self.cadastre.id)
        self.assertTrue(lock.acquire())
        try:
            overlap = enqueue_cadastre_sync(
                self.cadastre.id,
                organization_id=self.organization_id,
                requested_by_id=self.user.id,
                source="soak:overlap",
                inline=False,
            )
            self.assertTrue(overlap.already_running)
            self.assertEqual(overlap.run.id, queued.id)
        finally:
            lock.release()


class GisLoadProfileTests(TestCase):
    """Measure MVT + GeoJSON p95/p99, Python memory and PostgreSQL connection growth."""

    def setUp(self):
        self.user = User.objects.create_superuser("load-admin", "Load administrator", "very-secure-admin-password")
        self.client = authenticated_client(self.user)
        for index in range(96):
            x = 500000 + (index % 12) * 220
            y = 6500000 + (index // 12) * 220
            boundary = MultiPolygon(
                Polygon(((x, y), (x + 180, y), (x + 180, y + 180), (x, y + 180), (x, y)), srid=3301),
                srid=3301,
            )
            Cadastre.objects.create(id=f"SOAK:MAP:{index:04d}", name=f"Load parcel {index}", boundary=boundary)

    def test_mvt_and_geojson_stay_inside_load_budget(self):
        samples = int(os.getenv("FORESTIQ_SOAK_HTTP_SAMPLES", "30"))
        p95_budget = float(os.getenv("FORESTIQ_SOAK_P95_MS", "750"))
        p99_budget = float(os.getenv("FORESTIQ_SOAK_P99_MS", "1200"))
        memory_budget_mb = float(os.getenv("FORESTIQ_SOAK_MEMORY_MB", "128"))
        connection_growth_budget = int(os.getenv("FORESTIQ_SOAK_DB_CONNECTION_GROWTH", "2"))
        paths = (
            "/api/services/map/cadastres",
            "/api/services/map/tiles/cadastres/8/140/88.pbf",
        )

        for path in paths:
            self.assertEqual(self.client.get(path).status_code, 200)

        before_connections = postgres_connection_count()
        tracemalloc.start()
        latencies: dict[str, list[float]] = {path: [] for path in paths}
        for _ in range(samples):
            for path in paths:
                started = perf_counter()
                response = self.client.get(path)
                latencies[path].append(perf_counter() - started)
                self.assertEqual(response.status_code, 200)
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        after_connections = postgres_connection_count()

        peak_mb = peak_bytes / (1024 * 1024)
        connection_growth = max(after_connections - before_connections, 0)
        print(
            "SOAK load profile: "
            + ", ".join(
                f"{path}:p95={percentile_ms(values, .95):.2f}ms,p99={percentile_ms(values, .99):.2f}ms"
                for path, values in latencies.items()
            )
            + f", peak_python_mb={peak_mb:.2f}, db_connection_growth={connection_growth}"
        )
        for path, values in latencies.items():
            self.assertLessEqual(percentile_ms(values, 0.95), p95_budget, f"{path} exceeded p95 budget")
            self.assertLessEqual(percentile_ms(values, 0.99), p99_budget, f"{path} exceeded p99 budget")
        self.assertLessEqual(peak_mb, memory_budget_mb, "Python allocation peak exceeded memory budget")
        self.assertLessEqual(connection_growth, connection_growth_budget, "PostgreSQL connection growth exceeded budget")
