"""P0 coverage for resumable Metsaregister full import orchestration."""
from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import Organization
from accounts.organization_context import organization_scope
from forestry.models import DataSyncRun, ForestRegistryFeature, ImportCheckpoint
from forestry.services.metsaregister_full_import import import_all_metsaregister
from forestry.tasks import reconcile_stale_sync_runs


def _feature(identifier: str, cadastre_id: str, subpart: int) -> dict:
    base = 6580000 + subpart * 10
    return {
        "id": identifier,
        "properties": {
            "id": identifier,
            "katastri_nr": cadastre_id,
            "eraldis_nr": str(subpart),
            "pindala": "1.25",
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [650000, base],
                [650010, base],
                [650010, base + 10],
                [650000, base + 10],
                [650000, base],
            ]],
        },
    }


@override_settings(
    FORESTIQ_METSAREGISTER_WFS_URL="https://example.test/wfs",
    FORESTIQ_METSAREGISTER_FULL_WFS_LAYER="metsaregister:eraldis",
    FORESTIQ_METSAREGISTER_FULL_PAGE_SIZE=2,
    FORESTIQ_METSAREGISTER_NOTIFICATION_WFS_LAYER="",
)
class P0ResumableFullImportTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(slug="p0-full-import", name="P0 full import")

    def test_full_import_confirms_one_chunk_and_resumes_from_checkpoint(self):
        # The second call must request the next WFS page, not replay the finished chunk.
        seen_start_indexes: list[int] = []

        def fake_pages(*, layer, page_size, cql_filter=None, start_index=0):
            seen_start_indexes.append(start_index)
            if start_index == 0:
                yield [
                    _feature("a", "78401:101:0001", 1),
                    _feature("b", "78401:101:0002", 2),
                ]
            elif start_index == 2:
                yield [_feature("c", "78401:101:0003", 3)]

        with organization_scope(self.organization.id):
            run = DataSyncRun.objects.create(source="celery:metsaregister-full")
            with patch("forestry.services.metsaregister_full_import._pages", side_effect=fake_pages):
                first = import_all_metsaregister(organization_id=str(self.organization.id), run=run, max_pages=1)
                second = import_all_metsaregister(organization_id=str(self.organization.id), run=run, max_pages=10)

            self.assertFalse(first.completed)
            self.assertEqual(first.checkpoint_cursor, 2)
            self.assertTrue(second.completed)
            self.assertEqual(second.resumed_from, 2)
            self.assertEqual(second.checkpoint_cursor, 3)
            self.assertEqual(seen_start_indexes, [0, 2])
            self.assertEqual(ForestRegistryFeature.objects.count(), 3)
            checkpoint = ImportCheckpoint.objects.get(source="metsaregister-full")
            self.assertTrue(checkpoint.completed)
            self.assertEqual(checkpoint.rows_completed, 3)

    def test_stale_running_sync_run_is_failed_before_retry(self):
        with organization_scope(self.organization.id):
            stale = DataSyncRun.objects.create(
                source="celery:metsaregister-full",
                status=DataSyncRun.Status.RUNNING,
                started_at=timezone.now() - timedelta(hours=2),
                cursor={"heartbeatAt": (timezone.now() - timedelta(hours=2)).isoformat()},
            )
            fresh = DataSyncRun.objects.create(
                source="celery:metsaregister-full",
                status=DataSyncRun.Status.RUNNING,
                started_at=timezone.now(),
            )
            recovered = reconcile_stale_sync_runs(source="celery:metsaregister-full", older_than_seconds=60)

            stale.refresh_from_db()
            fresh.refresh_from_db()
            self.assertEqual(recovered, 1)
            self.assertEqual(stale.status, DataSyncRun.Status.FAILED)
            self.assertIn("staleRecovered", stale.result)
            self.assertEqual(fresh.status, DataSyncRun.Status.RUNNING)