"""Tests for the externally sourced forestry data synchronisation layer."""

from datetime import timedelta
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.utils import timezone
from django.contrib.gis.geos import MultiPolygon, Polygon
from rest_framework.test import APIClient

from accounts.models import User
from forestry.models import Cadastre, CadastreNotification, CadastreSubPart, DataSyncRun, ForestRegistryFeature, Owner, OwnerLog
from operations.models import Deal, DealStage
from forestry.services import import_runner
from forestry.services.external_sync import sync_cadastre_wfs, sync_parimus_inheritance
from forestry.services.metsaregister_full_import import FullImportReport, import_metsaregister_delta
from forestry.tasks import run_metsaregister_delta_check


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


class ImportCommandTests(TestCase):
    def setUp(self):
        self.cadastre = Cadastre.objects.create(id="79501:001:0005")

    @override_settings(FORESTIQ_CADASTRE_WFS_URL="https://wfs.example.test", FORESTIQ_CADASTRE_WFS_LAYER="cadastre:parcel")
    def test_wfs_command_persists_successful_audit_run(self):
        sync = Mock(return_value=1)
        source = import_runner.SourceDefinition("cadastre", sync, ("FORESTIQ_CADASTRE_WFS_URL", "FORESTIQ_CADASTRE_WFS_LAYER"))
        with patch.dict(import_runner.WFS_SOURCES, {"cadastre": source}, clear=True):
            call_command("import_wfs_sources", "--cadastre", self.cadastre.id, "--source", "cadastre")
        sync.assert_called_once_with(self.cadastre.id)
        run = DataSyncRun.objects.get(cadastre=self.cadastre)
        self.assertEqual(run.status, DataSyncRun.Status.SUCCEEDED)
        self.assertEqual(run.result, {"cadastre": 1})
        self.assertTrue(run.source.startswith("cli:wfs:"))

    @override_settings(FORESTIQ_CADASTRE_WFS_URL="https://wfs.example.test", FORESTIQ_CADASTRE_WFS_LAYER="cadastre:parcel")
    @patch("forestry.services.import_runner.sync_cadastre_wfs")
    def test_wfs_dry_run_makes_no_requests_or_audit_records(self, sync):
        call_command("import_wfs_sources", "--cadastre", self.cadastre.id, "--source", "cadastre", "--dry-run")
        sync.assert_not_called()
        self.assertFalse(DataSyncRun.objects.exists())

    def test_api_command_requires_explicit_source_configuration(self):
        with self.assertRaises(CommandError):
            call_command("import_external_api_sources", "--cadastre", self.cadastre.id, "--source", "forestek", "--dry-run")

    @override_settings(FORESTEK_API_URL="https://forestek.example.test", FORESTEK_API_TOKEN="test-token")
    def test_api_command_persists_audited_result(self):
        sync = Mock(return_value=2)
        source = import_runner.SourceDefinition("forestek", sync, ("FORESTEK_API_URL", "FORESTEK_API_TOKEN"))
        with patch.dict(import_runner.API_SOURCES, {"forestek": source}, clear=True):
            call_command("import_external_api_sources", "--cadastre", self.cadastre.id, "--source", "forestek")
        sync.assert_called_once_with(self.cadastre.id)
        run = DataSyncRun.objects.get(cadastre=self.cadastre)
        self.assertEqual(run.status, DataSyncRun.Status.SUCCEEDED)
        self.assertEqual(run.result, {"forestek": 2})

    @override_settings(FORESTEK_API_URL="https://forestek.example.test", FORESTEK_API_TOKEN="test-token")
    def test_forestek_command_refuses_a_second_successful_initial_import(self):
        DataSyncRun.objects.create(cadastre=self.cadastre, source="cli:api:forestek", status=DataSyncRun.Status.SUCCEEDED)
        with self.assertRaises(CommandError):
            call_command("import_external_api_sources", "--cadastre", self.cadastre.id, "--source", "forestek", "--dry-run")


class MetsaregisterFullImportTests(TestCase):
    def setUp(self):
        self.cadastre = Cadastre.objects.create(id="79501:001:0006")
        CadastreSubPart.objects.create(cadastre=self.cadastre, sub_part_code=10)

    @override_settings(
        FORESTIQ_METSAREGISTER_WFS_URL="https://metsaregister.example.test/ows",
        FORESTIQ_METSAREGISTER_FULL_WFS_LAYER="metsaregister:eraldis",
        FORESTIQ_METSAREGISTER_NOTIFICATION_WFS_LAYER="metsaregister:teatis",
        FORESTIQ_METSAREGISTER_FULL_PAGE_SIZE=100,
    )
    @patch("forestry.services.metsaregister_full_import.requests.get")
    def test_full_import_fetches_notifications_only_for_new_subparts(self, get):
        geometry = {"type": "Polygon", "coordinates": [[[500000, 6500000], [500100, 6500000], [500000, 6500100], [500000, 6500000]]]}
        allocations = Mock()
        allocations.json.return_value = {"features": [
            {"id": "existing-10", "properties": {"katastri_nr": self.cadastre.id, "eraldis_nr": 10, "pindala": "1.2"}, "geometry": geometry},
            {"id": "new-11", "properties": {"katastri_nr": self.cadastre.id, "eraldis_nr": 11, "pindala": "2.4"}, "geometry": geometry},
        ]}
        notifications = Mock()
        notifications.json.return_value = {"features": [{"id": "9001", "properties": {"teatise_nr": "7001", "eraldis_nr": 11, "raie_liik": "RAIE", "pindala": "2.4"}, "geometry": geometry}]}
        get.side_effect = [allocations, notifications]

        call_command("import_metsaregister_full", "--page-size", "100")

        self.assertTrue(CadastreSubPart.objects.filter(cadastre=self.cadastre, sub_part_code=11).exists())
        self.assertEqual(CadastreNotification.objects.filter(cadastre=self.cadastre, cadastre_subpart_code=11).count(), 1)
        self.assertEqual(get.call_count, 2)
        notification_params = get.call_args_list[1].kwargs["params"]
        self.assertIn("eraldis_nr=11", notification_params["CQL_FILTER"])
        self.assertNotIn("eraldis_nr=10", notification_params["CQL_FILTER"])
        run = DataSyncRun.objects.get(source="cli:metsaregister-full")
        self.assertEqual(run.status, DataSyncRun.Status.SUCCEEDED)
        self.assertEqual(run.result["new_subparts"], 1)
        self.assertEqual(run.result["notifications"], 1)

    @override_settings(FORESTIQ_METSAREGISTER_FULL_WFS_LAYER="metsaregister:eraldis")
    @patch("forestry.services.metsaregister_full_import.requests.get")
    def test_full_import_dry_run_makes_no_wfs_request(self, get):
        call_command("import_metsaregister_full", "--dry-run")
        get.assert_not_called()
        self.assertFalse(DataSyncRun.objects.exists())

    @override_settings(
        FORESTIQ_METSAREGISTER_WFS_URL="https://metsaregister.example.test/ows",
        FORESTIQ_METSAREGISTER_FULL_WFS_LAYER="metsaregister:eraldis",
        FORESTIQ_METSAREGISTER_NOTIFICATION_WFS_LAYER="",
        FORESTIQ_METSAREGISTER_DELTA_FIELD="registreerimise_kp",
        FORESTIQ_METSAREGISTER_FULL_PAGE_SIZE=100,
    )
    @patch("forestry.services.metsaregister_full_import.requests.get")
    def test_delta_import_uses_timestamp_cql_and_persists_only_new_subpart(self, get):
        geometry = {"type": "Polygon", "coordinates": [[[500000, 6500000], [500100, 6500000], [500000, 6500100], [500000, 6500000]]]}
        response = Mock()
        response.json.return_value = {"features": [{"id": "new-13", "properties": {"katastri_nr": self.cadastre.id, "eraldis_nr": 13, "pindala": "1.0", "registreerimise_kp": "2026-08-26T12:00:00Z"}, "geometry": geometry}]}
        get.return_value = response
        since = timezone.now() - timedelta(hours=1)

        report = import_metsaregister_delta(since=since, page_size=100)

        self.assertEqual(report.new_subparts, 1)
        self.assertTrue(CadastreSubPart.objects.filter(cadastre=self.cadastre, sub_part_code=13).exists())
        params = get.call_args.kwargs["params"]
        self.assertIn("registreerimise_kp >=", params["CQL_FILTER"])
        self.assertNotIn("eraldis_nr=10", params["CQL_FILTER"])

    @patch("forestry.tasks.import_metsaregister_delta", return_value=FullImportReport(features=1, new_subparts=1, notifications=2))
    def test_celery_delta_task_creates_audited_run(self, import_delta):
        result = run_metsaregister_delta_check.run()
        run = DataSyncRun.objects.get(source="celery:metsaregister-cql-delta")
        self.assertEqual(run.status, DataSyncRun.Status.SUCCEEDED)
        self.assertEqual(result["new_subparts"], 1)
        self.assertEqual(result["notifications"], 2)
        self.assertIn("since", result)
        self.assertTrue(import_delta.called)


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

    def test_geodjango_map_layers_return_subparts_registry_and_notification_marker(self):
        boundary = MultiPolygon(Polygon(((500000, 6500000), (500100, 6500000), (500000, 6500100), (500000, 6500000)), srid=3301), srid=3301)
        CadastreSubPart.objects.create(cadastre=self.cadastre, sub_part_code=12, tree_type_code="KU", boundary=boundary)
        ForestRegistryFeature.objects.create(source_layer="metsaregister:eraldis", source_id="layer-12", cadastre=self.cadastre, subpart_code=12, title="Eraldis 12", spatial_geometry=boundary)
        CadastreNotification.objects.create(id=12001, notification_number=7001, cadastre=self.cadastre, cadastre_subpart_code=12, work_code="RAIE")
        for layer, expected_type in [("subparts", "MultiPolygon"), ("new-subparts", "MultiPolygon"), ("registry", "MultiPolygon"), ("notifications", "Point")]:
            response = self.client.get(f"/api/services/map/layers/{layer}")
            self.assertEqual(response.status_code, 200, response.data)
            self.assertEqual(len(response.data["features"]), 1)
            self.assertEqual(response.data["features"][0]["geometry"]["type"], expected_type)
            self.assertEqual(response.data["features"][0]["properties"]["cadastreId"], self.cadastre.id)
        notification = self.client.get("/api/services/map/layers/notifications").data["features"][0]["properties"]
        subpart = self.client.get("/api/services/map/layers/new-subparts").data["features"][0]["properties"]
        self.assertEqual(notification["treeType"], "KU")
        self.assertIn("discoveredAt", notification)
        self.assertIn("discoveredAt", subpart)

    def test_cadastre_workspace_aggregates_accessible_owner_customer_and_registry_data(self):
        owner = Owner.objects.create(id="38101010002", name="Kaardi klient", phone="5550100", email="client@example.test", status="CUSTOMER")
        self.cadastre.owners.add(owner)
        OwnerLog.objects.create(owner=owner, creator=self.user, message="Esimene kontakt kaardilt")
        deal = Deal.objects.create(owner=owner, sale_subject="FOREST", stage=DealStage.WON)
        deal.parcels.add(self.cadastre)
        CadastreNotification.objects.create(id=12002, notification_number=7002, cadastre=self.cadastre, cadastre_subpart_code=12, work_code="RAIE")
        ForestRegistryFeature.objects.create(source_layer="metsaregister:eraldis", source_id="workspace-12", cadastre=self.cadastre, subpart_code=12, title="Eraldis 12")

        response = self.client.get(f"/api/services/cadastres/{self.cadastre.id}/workspace")

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["cadastre"]["id"], self.cadastre.id)
        self.assertEqual(response.data["owners"][0]["name"], owner.name)
        self.assertTrue(response.data["owners"][0]["customerRelationship"]["isCustomer"])
        self.assertEqual(response.data["activities"][0]["kind"], "DEAL")
        self.assertEqual(response.data["notifications"][0]["notificationNumber"], 7002)
        self.assertEqual(response.data["registryFeatures"][0]["title"], "Eraldis 12")
