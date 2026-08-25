"""Tests for the externally sourced forestry data synchronisation layer."""

from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from django.contrib.gis.geos import MultiPolygon, Polygon
from rest_framework.test import APIClient

from accounts.models import User
from forestry.models import Cadastre, DataSyncRun, Owner
from forestry.services.external_sync import sync_cadastre_wfs, sync_parimus_inheritance


class CadastreWfsTests(TestCase):
    def setUp(self):
        self.cadastre = Cadastre.objects.create(id="79501:001:0001")

    @patch("forestry.services.external_sync.requests.get")
    def test_cadastre_wfs_maps_official_property_fields(self, get):
        response = Mock()
        response.json.return_value = {
            "features": [
                {
                    "properties": {
                        "tunnus": self.cadastre.id,
                        "kinnistu": "12345",
                        "l_aadress": "Männiku küla",
                        "mk_nimi": "Harju maakond",
                        "ov_nimi": "Test vald",
                        "registr": "12345",
                        "siht1": "Maatulundusmaa",
                        "pindala": "12400.5",
                        "mets": "7600.5",
                        "haritav": "2100",
                        "rohumaa": "900",
                        "ouemaa": "300",
                        "muumaa": "1500",
                        "marked": True,
                    },
                    "geometry": {"type": "Polygon", "coordinates": [[[500000, 6500000], [500100, 6500000], [500000, 6500100], [500000, 6500000]]]},
                }
            ]
        }
        get.return_value = response

        self.assertEqual(sync_cadastre_wfs(self.cadastre.id), 1)
        self.cadastre.refresh_from_db()
        self.assertEqual(self.cadastre.name, "")
        self.assertEqual(self.cadastre.registration_number, "12345")
        self.assertEqual(str(self.cadastre.forest_area), "7600.5000")
        self.assertEqual(self.cadastre.centroid["srid"], 3301)
        self.assertIsNotNone(self.cadastre.boundary)
        self.assertEqual(self.cadastre.boundary.srid, 3301)
        self.assertTrue(self.cadastre.marked)


class InheritanceApiTests(TestCase):
    def setUp(self):
        self.owner = Owner.objects.create(id="38101010001", name="Pärandaja")
        self.cadastre = Cadastre.objects.create(id="79501:001:0002")
        self.cadastre.owners.add(self.owner)

    @override_settings(PARIMUS_API_URL="https://parimus.example.test", PARIMUS_API_TOKEN="unit-test-token")
    @patch("forestry.services.external_sync.requests.get")
    def test_parimus_results_are_linked_by_exact_owner_personal_code(self, get):
        response = Mock()
        response.json.return_value = {
            "results": [
                {
                    "notice_number": "123456",
                    "announcement_date": "2026-08-20",
                    "certification_deadline": "2026-10-20",
                    "deceased_name": "Pärandaja",
                    "source_url": "https://example.test/notice/123456",
                    "heirs": [],
                }
            ]
        }
        get.return_value = response

        self.assertEqual(sync_parimus_inheritance(self.cadastre.id), 1)
        signal = self.owner.inheritance_signals.get()
        self.assertEqual(signal.cadastre_id, self.cadastre.id)
        self.assertEqual(signal.source_notice_number, "123456")
        self.assertEqual(get.call_args.kwargs["params"], {"personal_code": self.owner.id})


class SyncEndpointTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin", "Administrator", "very-secure-admin-password")
        self.cadastre = Cadastre.objects.create(id="79501:001:0003")
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    @override_settings(FORESTIQ_TASKS_INLINE=True)
    @patch("forestry.tasks.sync_parimus_inheritance", return_value=0)
    @patch("forestry.tasks.sync_forestek_owner_relations", return_value=0)
    @patch("forestry.tasks.sync_optional_soos_wfs", return_value=0)
    @patch("forestry.tasks.sync_metsaregister_wfs", return_value=0)
    @patch("forestry.tasks.sync_cadastre_wfs", return_value=0)
    def test_admin_can_submit_a_cadastre_sync_run(self, *_mocks):
        response = self.client.post(f"/api/services/admin/cadastres/{self.cadastre.id}/sync")
        self.assertEqual(response.status_code, 202, response.data)
        run = DataSyncRun.objects.get(id=response.data["id"])
        self.assertEqual(run.status, DataSyncRun.Status.SUCCEEDED)
        self.assertEqual(run.requested_by_id, self.admin.id)

    def test_non_admin_cannot_submit_a_sync_run(self):
        caller = User.objects.create_user("caller", "Caller", "very-secure-password")
        client = APIClient()
        client.force_authenticate(caller)
        response = client.post(f"/api/services/admin/cadastres/{self.cadastre.id}/sync")
        self.assertEqual(response.status_code, 403)


class MapFeatureTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("map-admin", "Map administrator", "very-secure-admin-password")
        self.cadastre = Cadastre.objects.create(
            id="79501:001:0004",
            name="Kaardi testüksus",
            boundary=MultiPolygon(Polygon(((500000, 6500000), (500100, 6500000), (500000, 6500100), (500000, 6500000)), srid=3301), srid=3301),
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_map_endpoint_returns_wgs84_geojson(self):
        response = self.client.get("/api/services/map/cadastres")
        self.assertEqual(response.status_code, 200, response.data)
        feature = response.data["features"][0]
        self.assertEqual(feature["id"], self.cadastre.id)
        self.assertEqual(feature["geometry"]["type"], "MultiPolygon")
        self.assertLess(abs(feature["geometry"]["coordinates"][0][0][0][0]), 180)
