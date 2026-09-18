"""P0 regression coverage for production-safety issues."""
from __future__ import annotations

from unittest.mock import patch

from django.test import TestCase

from accounts.models import Organization
from accounts.organization_context import organization_scope
from forestry.models import Cadastre, ForestRegistryFeature
from forestry.p3_models import WfsGenerationFeature, WfsLayerManifest
from forestry.services.wfs_generations import deep_verify, publish_generation, rollback_generation, stage_generation


class P0WfsGenerationOrganizationStampingTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(slug="p0-tenant", name="P0 tenant")
        self.other_organization = Organization.objects.create(slug="p0-other", name="P0 other")
        with organization_scope(self.organization.id):
            self.cadastre = Cadastre.objects.create(
                id="12345:001:0001",
                name="P0 parcel",
                organization=self.organization,
            )
            self.manifest = WfsLayerManifest.objects.create(
                organization=self.organization,
                key="p0-layer",
                source_layer="metsaregister:p0",
                retention_generations=1,
            )

    def _feature(self, source_id: str, title: str):
        return {
            "id": source_id,
            "properties": {"id": source_id, "title": title, "pindala": "1.25"},
            "geometry": {"type": "Point", "coordinates": [25.5, 58.7]},
        }

    def test_bulk_created_wfs_generation_features_keep_manifest_organization_through_publish_and_rollback(self):
        with organization_scope(self.organization.id):
            with patch("forestry.services.wfs_generations.wfs_features", return_value=[self._feature("source-1", "First")]):
                first = stage_generation(self.manifest)
            self.assertEqual(first.organization_id, self.organization.id)
            self.assertEqual(first.feature_count, 1)
            self.assertEqual(first.features.count(), 1)
            staged_feature = first.features.get()
            self.assertEqual(staged_feature.organization_id, self.organization.id)
            self.assertEqual(WfsGenerationFeature.all_objects.get(pk=staged_feature.pk).organization_id, self.organization.id)

            publish_generation(first)
            self.assertTrue(deep_verify(self.manifest)["ok"])
            self.assertTrue(ForestRegistryFeature.objects.filter(source_layer=self.manifest.source_layer, source_id="source-1").exists())

            with patch("forestry.services.wfs_generations.wfs_features", return_value=[self._feature("source-2", "Second")]):
                second = stage_generation(self.manifest)
            self.assertEqual(second.features.get().organization_id, self.organization.id)
            publish_generation(second)
            self.assertFalse(ForestRegistryFeature.objects.filter(source_id="source-1").exists())
            self.assertTrue(ForestRegistryFeature.objects.filter(source_id="source-2").exists())

            first.refresh_from_db()
            rollback_generation(first)
            self.assertTrue(ForestRegistryFeature.objects.filter(source_id="source-1").exists())
            self.assertFalse(ForestRegistryFeature.objects.filter(source_id="source-2").exists())

        with organization_scope(self.other_organization.id):
            self.assertFalse(WfsGenerationFeature.objects.filter(id=staged_feature.id).exists())
            self.assertFalse(ForestRegistryFeature.objects.filter(source_layer=self.manifest.source_layer).exists())
