"""P0 regression coverage for production-safety issues."""
from __future__ import annotations

from unittest.mock import patch

from django.test import TestCase

from accounts.models import Organization
from accounts.organization_context import organization_scope
from forestry.models import Cadastre, ForestRegistryFeature, Owner
from api.serializers import cadastre_summary, owner_summary
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



class P0TenantExternalIdentityTests(TestCase):
    """The same registry identity may exist independently in multiple organizations."""

    def setUp(self):
        self.first = Organization.objects.create(slug="identity-a", name="Identity tenant A")
        self.second = Organization.objects.create(slug="identity-b", name="Identity tenant B")

    def test_same_public_owner_and_cadastre_ids_are_isolated_per_tenant(self):
        cadastre_external_id = "79501:001:9999"
        owner_external_id = "38101019999"

        with organization_scope(self.first.id):
            cadastre_a = Cadastre.objects.create(id=cadastre_external_id, name="Tenant A parcel")
            owner_a = Owner.objects.create(id=owner_external_id, name="Tenant A owner")
            cadastre_a.owners.add(owner_a)
            ForestRegistryFeature.objects.create(
                cadastre=cadastre_a,
                source_layer="identity:test",
                source_id="same-source",
                title="A",
            )

        with organization_scope(self.second.id):
            cadastre_b = Cadastre.objects.create(id=cadastre_external_id, name="Tenant B parcel")
            owner_b = Owner.objects.create(id=owner_external_id, name="Tenant B owner")
            cadastre_b.owners.add(owner_b)
            ForestRegistryFeature.objects.create(
                cadastre=cadastre_b,
                source_layer="identity:test",
                source_id="same-source",
                title="B",
            )

        self.assertEqual(cadastre_a.public_id, cadastre_external_id)
        self.assertEqual(cadastre_b.public_id, cadastre_external_id)
        self.assertNotEqual(cadastre_a.pk, cadastre_b.pk)
        self.assertEqual(owner_a.public_id, owner_external_id)
        self.assertEqual(owner_b.public_id, owner_external_id)
        self.assertNotEqual(owner_a.pk, owner_b.pk)
        self.assertEqual(Cadastre.all_objects.filter(external_id=cadastre_external_id).count(), 2)
        self.assertEqual(Owner.all_objects.filter(external_id=owner_external_id).count(), 2)

        with organization_scope(self.first.id):
            self.assertEqual(Cadastre.objects.get(id=cadastre_external_id).pk, cadastre_a.pk)
            self.assertEqual(Owner.objects.get(id=owner_external_id).pk, owner_a.pk)
            self.assertEqual(ForestRegistryFeature.objects.get(source_id="same-source").title, "A")
            self.assertEqual(cadastre_summary(cadastre_a)["id"], cadastre_external_id)
            self.assertEqual(owner_summary(owner_a)["id"], owner_external_id)

        with organization_scope(self.second.id):
            self.assertEqual(Cadastre.objects.get(id=cadastre_external_id).pk, cadastre_b.pk)
            self.assertEqual(Owner.objects.get(id=owner_external_id).pk, owner_b.pk)
            self.assertEqual(ForestRegistryFeature.objects.get(source_id="same-source").title, "B")
            self.assertEqual(cadastre_summary(cadastre_b)["id"], cadastre_external_id)
            self.assertEqual(owner_summary(owner_b)["id"], owner_external_id)

    def test_explicit_external_id_lookup_does_not_cross_organization_boundary(self):
        external_id = "79501:001:9998"
        with organization_scope(self.first.id):
            first = Cadastre.objects.create(id=external_id, name="First")
        with organization_scope(self.second.id):
            second = Cadastre.objects.create(id=external_id, name="Second")

        with organization_scope(self.first.id):
            self.assertEqual(Cadastre.objects.get(external_id=external_id).pk, first.pk)
            self.assertFalse(Cadastre.objects.filter(pk=second.pk).exists())

        with organization_scope(self.second.id):
            self.assertEqual(Cadastre.objects.get(external_id=external_id).pk, second.pk)
            self.assertFalse(Cadastre.objects.filter(pk=first.pk).exists())
