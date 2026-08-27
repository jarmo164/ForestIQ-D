"""Deterministic GIS response-time budgets run against the Quality Gate PostGIS service."""

from __future__ import annotations

from math import ceil
from time import perf_counter

from django.conf import settings
from django.core.cache import cache
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from api.auth import token_pair
from forestry.models import Cadastre, CadastreNotification, CadastreSubPart, Owner
from forestry.services.tile_cache import invalidate_vector_tiles
from operations.models import Deal, DealStage


def authenticated_client(user: User) -> APIClient:
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_pair(user)['actualToken']['token']}")
    return client


def p95_milliseconds(samples: list[float]) -> float:
    """Return nearest-rank p95 in milliseconds for a non-empty sample set."""

    ordered = sorted(samples)
    return ordered[ceil(len(ordered) * 0.95) - 1] * 1000


class GisPerformanceBudgetTests(TestCase):
    """Measure stable GIS paths on a fixed spatial corpus, not production data."""

    samples = 15

    def setUp(self):
        self.user = User.objects.create_superuser("gis-budget-admin", "GIS budget administrator", "very-secure-admin-password")
        self.client = authenticated_client(self.user)
        self.cadastres = []
        for index in range(64):
            x = 500000 + (index % 8) * 240
            y = 6500000 + (index // 8) * 240
            boundary = MultiPolygon(
                Polygon(((x, y), (x + 180, y), (x + 180, y + 180), (x, y + 180), (x, y)), srid=3301),
                srid=3301,
            )
            cadastre = Cadastre.objects.create(
                id=f"79501:001:{index + 1000:04d}",
                name=f"Jõudlustesti katastriüksus {index + 1}",
                boundary=boundary,
                area="3.2400",
            )
            CadastreSubPart.objects.create(cadastre=cadastre, sub_part_code=1, boundary=boundary, area="3.2400")
            self.cadastres.append(cadastre)

        self.target = self.cadastres[0]
        owner = Owner.objects.create(id="38101010005", name="Jõudlustesti klient")
        self.target.owners.add(owner)
        active_deal = Deal.objects.create(owner=owner, sale_subject="FOREST", stage=DealStage.EVALUATION)
        active_deal.parcels.add(self.target)
        CadastreNotification.objects.create(id=921001, notification_number=921001, cadastre=self.target, cadastre_subpart_code=1, work_code="RAIE")

    def test_uncached_vector_tile_and_summary_stay_within_fixed_corpus_p95_budget(self):
        """Report and enforce the documented p95 ceiling using real PostGIS SQL."""

        cache.clear()
        tile_path = "/api/services/map/tiles/cadastres/8/140/88.pbf"
        summary_path = f"/api/services/cadastres/{self.target.id}/summary"
        tile_samples: list[float] = []
        summary_samples: list[float] = []

        # One warm-up per path avoids charging Django's import/connection startup to the
        # measured request budget while every measured tile request remains uncached.
        self.client.get(tile_path)
        self.client.get(summary_path)
        for _ in range(self.samples):
            invalidate_vector_tiles(str(self.target.organization_id), ("cadastres",))
            started = perf_counter()
            tile_response = self.client.get(tile_path)
            tile_samples.append(perf_counter() - started)
            self.assertEqual(tile_response.status_code, 200)

            started = perf_counter()
            summary_response = self.client.get(summary_path)
            summary_samples.append(perf_counter() - started)
            self.assertEqual(summary_response.status_code, 200)

        tile_p95 = p95_milliseconds(tile_samples)
        summary_p95 = p95_milliseconds(summary_samples)
        print(
            f"GIS fixed corpus: rows={len(self.cadastres)}, samples={self.samples}, "
            f"tile_p95_ms={tile_p95:.2f}, summary_p95_ms={summary_p95:.2f}, "
            f"budget_ms={settings.FORESTIQ_GIS_PERFORMANCE_P95_MS}"
        )
        self.assertLessEqual(tile_p95, settings.FORESTIQ_GIS_PERFORMANCE_P95_MS)
        self.assertLessEqual(summary_p95, settings.FORESTIQ_GIS_PERFORMANCE_P95_MS)
