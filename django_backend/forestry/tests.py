"""Tests for the externally sourced forestry data synchronisation layer."""

from datetime import timedelta
import json
from unittest.mock import MagicMock, Mock, patch

import requests

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from django.contrib.gis.geos import MultiPolygon, Polygon
from rest_framework.test import APIClient

from accounts.organization_context import organization_scope
from accounts.models import Organization, User
from api.auth import token_pair
from forestry.models import Cadastre, CadastreNotification, CadastreSubPart, DataSyncRun, ForestRegistryFeature, ImportCheckpoint, Owner, OwnerLog
from operations.models import Deal, DealStage
from forestry.services import import_runner
from forestry.services.external_sync import sync_cadastre_wfs, sync_parimus_inheritance, wfs_features
from forestry.services.metsaregister_full_import import FullImportReport, import_all_metsaregister, import_metsaregister_delta
from forestry.tasks import (
    enqueue_cadastre_sync,
    run_cadastre_sync,
    run_metsaregister_delta_check,
    run_parimus_official_notice_import,
)
from forestry.services.single_flight import SingleFlightLock
from forestry.services.wfs_client import WfsClient, WfsClientError, WfsClientPolicy


def authenticated_client(user: User) -> APIClient:
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_pair(user)['actualToken']['token']}")
    return client


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

        with organization_scope(self.cadastre.organization_id):
            self.assertEqual(sync_cadastre_wfs(self.cadastre.id, organization_id=str(self.cadastre.organization_id)), 1)
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

        with organization_scope(self.cadastre.organization_id):
            self.assertEqual(sync_parimus_inheritance(self.cadastre.id, organization_id=str(self.cadastre.organization_id)), 1)
        signal = self.owner.inheritance_signals.get()
        self.assertEqual(signal.cadastre_id, self.cadastre.id)
        self.assertEqual(signal.source_notice_number, "123456")
        self.assertEqual(get.call_args.kwargs["params"], {"personal_code": self.owner.id})

    @override_settings(PARIMUS_API_URL="https://parimus.example.test", PARIMUS_API_TOKEN="unit-test-token")
    @patch("forestry.services.external_sync.requests.get")
    def test_parimus_source_notice_key_updates_instead_of_creating_duplicates(self, get):
        get.return_value.json.return_value = {
            "results": [
                {
                    "notice_number": "deduplicated-123",
                    "announcement_date": "2026-08-20",
                    "certification_deadline": "2026-10-20",
                    "deceased_name": "Pärandaja",
                    "source_url": "https://example.test/notice/deduplicated-123",
                }
            ]
        }

        with organization_scope(self.cadastre.organization_id):
            sync_parimus_inheritance(self.cadastre.id, organization_id=str(self.cadastre.organization_id))
            sync_parimus_inheritance(self.cadastre.id, organization_id=str(self.cadastre.organization_id))

        self.assertEqual(self.owner.inheritance_signals.filter(source_notice_number="deduplicated-123").count(), 1)
        self.assertEqual(get.call_count, 2)


class SyncEndpointTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin", "Administrator", "very-secure-admin-password")
        self.cadastre = Cadastre.objects.create(id="79501:001:0003")
        self.client = authenticated_client(self.admin)

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

    @override_settings(FORESTIQ_TASKS_INLINE=True)
    def test_correlation_id_is_saved_on_api_sync_audit_run(self):
        redis_client = FakeRedis()
        with (
            patch("forestry.services.single_flight.redis.from_url", return_value=redis_client),
            patch("forestry.tasks.sync_cadastre_wfs", return_value=0),
            patch("forestry.tasks.sync_metsaregister_wfs", return_value=0),
            patch("forestry.tasks.sync_optional_soos_wfs", return_value=0),
            patch("forestry.tasks.sync_parimus_inheritance", return_value=0),
        ):
            response = self.client.post(
                f"/api/services/admin/cadastres/{self.cadastre.id}/sync",
                HTTP_X_CORRELATION_ID="support-trace-100",
            )

        self.assertEqual(response.status_code, 202, response.data)
        self.assertEqual(response.data["correlationId"], "support-trace-100")
        self.assertEqual(DataSyncRun.objects.get(id=response.data["id"]).correlation_id, "support-trace-100")

    def test_non_admin_cannot_submit_a_sync_run(self):
        caller = User.objects.create_user("caller", "Caller", "very-secure-password")
        client = authenticated_client(caller)
        response = client.post(f"/api/services/admin/cadastres/{self.cadastre.id}/sync")
        self.assertEqual(response.status_code, 403)

    def test_worker_cannot_run_another_organizations_audit_row(self):
        other_organization = Organization.objects.create(slug="worker-other", name="Worker other organization")
        other_cadastre = Cadastre.objects.create(id="79501:001:9999", organization=other_organization)
        run = DataSyncRun.objects.create(cadastre=other_cadastre, source="cross-organization-test")

        with self.assertRaises(DataSyncRun.DoesNotExist):
            run_cadastre_sync.run(run.id, str(self.cadastre.organization_id))

        run.refresh_from_db()
        self.assertEqual(run.status, DataSyncRun.Status.QUEUED)


class ImportCommandTests(TestCase):
    def setUp(self):
        self.cadastre = Cadastre.objects.create(id="79501:001:0005")
        self.organization = self.cadastre.organization

    @override_settings(FORESTIQ_CADASTRE_WFS_URL="https://wfs.example.test", FORESTIQ_CADASTRE_WFS_LAYER="cadastre:parcel")
    def test_wfs_command_persists_successful_audit_run(self):
        sync = Mock(return_value=1)
        source = import_runner.SourceDefinition("cadastre", sync, ("FORESTIQ_CADASTRE_WFS_URL", "FORESTIQ_CADASTRE_WFS_LAYER"))
        with patch.dict(import_runner.WFS_SOURCES, {"cadastre": source}, clear=True):
            call_command("import_wfs_sources", "--cadastre", self.cadastre.id, "--source", "cadastre", "--organization", str(self.organization.id))
        sync.assert_called_once_with(self.cadastre.id, organization_id=str(self.organization.id))
        run = DataSyncRun.objects.get(cadastre=self.cadastre)
        self.assertEqual(run.status, DataSyncRun.Status.SUCCEEDED)
        self.assertEqual(run.result, {"cadastre": 1})
        self.assertTrue(run.source.startswith("cli:wfs:"))

    @override_settings(FORESTIQ_CADASTRE_WFS_URL="https://wfs.example.test", FORESTIQ_CADASTRE_WFS_LAYER="cadastre:parcel")
    @patch("forestry.services.import_runner.sync_cadastre_wfs")
    def test_wfs_dry_run_makes_no_requests_or_audit_records(self, sync):
        call_command("import_wfs_sources", "--cadastre", self.cadastre.id, "--source", "cadastre", "--dry-run", "--organization", str(self.organization.id))
        sync.assert_not_called()
        self.assertFalse(DataSyncRun.objects.exists())

    def test_api_command_requires_explicit_source_configuration(self):
        with self.assertRaises(CommandError):
            call_command("import_external_api_sources", "--cadastre", self.cadastre.id, "--source", "forestek", "--dry-run", "--organization", str(self.organization.id))

    @override_settings(FORESTEK_API_URL="https://forestek.example.test", FORESTEK_API_TOKEN="test-token")
    def test_api_command_persists_audited_result(self):
        sync = Mock(return_value=2)
        source = import_runner.SourceDefinition("forestek", sync, ("FORESTEK_API_URL", "FORESTEK_API_TOKEN"))
        with patch.dict(import_runner.API_SOURCES, {"forestek": source}, clear=True):
            call_command("import_external_api_sources", "--cadastre", self.cadastre.id, "--source", "forestek", "--organization", str(self.organization.id))
        sync.assert_called_once_with(self.cadastre.id, organization_id=str(self.organization.id))
        run = DataSyncRun.objects.get(cadastre=self.cadastre)
        self.assertEqual(run.status, DataSyncRun.Status.SUCCEEDED)
        self.assertEqual(run.result, {"forestek": 2})

    @override_settings(FORESTEK_API_URL="https://forestek.example.test", FORESTEK_API_TOKEN="test-token")
    def test_forestek_command_refuses_a_second_successful_initial_import(self):
        DataSyncRun.objects.create(cadastre=self.cadastre, source="cli:api:forestek", status=DataSyncRun.Status.SUCCEEDED)
        with self.assertRaises(CommandError):
            call_command("import_external_api_sources", "--cadastre", self.cadastre.id, "--source", "forestek", "--dry-run", "--organization", str(self.organization.id))


class MetsaregisterFullImportTests(TestCase):
    def setUp(self):
        self.cadastre = Cadastre.objects.create(id="79501:001:0006")
        self.organization = self.cadastre.organization
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

        call_command("import_metsaregister_full", "--page-size", "100", "--organization", str(self.organization.id))

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
        checkpoint = ImportCheckpoint.objects.get(source="metsaregister-full")
        self.assertEqual(checkpoint.last_run_id, run.id)
        self.assertTrue(checkpoint.completed)
        self.assertEqual(checkpoint.cursor, 2)

    @override_settings(FORESTIQ_METSAREGISTER_FULL_WFS_LAYER="metsaregister:eraldis")
    @patch("forestry.services.metsaregister_full_import.requests.get")
    def test_full_import_dry_run_makes_no_wfs_request(self, get):
        call_command("import_metsaregister_full", "--dry-run", "--organization", str(self.organization.id))
        get.assert_not_called()
        self.assertFalse(DataSyncRun.objects.exists())

    @override_settings(
        FORESTIQ_METSAREGISTER_WFS_URL="https://metsaregister.example.test/ows",
        FORESTIQ_METSAREGISTER_FULL_WFS_LAYER="metsaregister:eraldis",
        FORESTIQ_METSAREGISTER_NOTIFICATION_WFS_LAYER="",
        FORESTIQ_METSAREGISTER_FULL_PAGE_SIZE=1,
    )
    def test_interrupted_full_import_resumes_at_the_last_confirmed_page_cursor(self):
        geometry = {"type": "Polygon", "coordinates": [[[500000, 6500000], [500100, 6500000], [500000, 6500100], [500000, 6500000]]]}
        first = {"id": "checkpoint-20", "properties": {"katastri_nr": self.cadastre.id, "eraldis_nr": 20, "pindala": "1.0"}, "geometry": geometry}
        second = {"id": "checkpoint-21", "properties": {"katastri_nr": self.cadastre.id, "eraldis_nr": 21, "pindala": "2.0"}, "geometry": geometry}

        def interrupted_pages(**_kwargs):
            yield [first]
            raise ConnectionError("WFS connection interrupted after the first page")

        with organization_scope(self.organization.id):
            with patch("forestry.services.metsaregister_full_import._pages", side_effect=interrupted_pages):
                with self.assertRaises(ConnectionError):
                    import_all_metsaregister(organization_id=str(self.organization.id), page_size=1, fetch_notifications=False)

        checkpoint = ImportCheckpoint.objects.get(source="metsaregister-full")
        self.assertEqual(checkpoint.cursor, 1)
        self.assertEqual(checkpoint.pages_completed, 1)
        self.assertEqual(checkpoint.rows_completed, 1)
        self.assertFalse(checkpoint.completed)

        def resumed_pages(**kwargs):
            self.assertEqual(kwargs["start_index"], 1)
            yield [second]

        with organization_scope(self.organization.id):
            with patch("forestry.services.metsaregister_full_import._pages", side_effect=resumed_pages):
                report = import_all_metsaregister(organization_id=str(self.organization.id), page_size=1, fetch_notifications=False)

        checkpoint.refresh_from_db()
        self.assertEqual(report.resumed_from, 1)
        self.assertEqual(report.checkpoint_cursor, 2)
        self.assertTrue(checkpoint.completed)
        self.assertEqual(checkpoint.cursor, 2)
        self.assertEqual(CadastreSubPart.objects.filter(cadastre=self.cadastre, sub_part_code__in=(20, 21)).count(), 2)

    @override_settings(
        FORESTIQ_METSAREGISTER_WFS_URL="https://metsaregister.example.test/ows",
        FORESTIQ_METSAREGISTER_FULL_WFS_LAYER="metsaregister:eraldis",
        FORESTIQ_METSAREGISTER_NOTIFICATION_WFS_LAYER="",
        FORESTIQ_METSAREGISTER_FULL_PAGE_SIZE=1,
    )
    def test_unconfirmed_page_replay_is_idempotent(self):
        geometry = {"type": "Polygon", "coordinates": [[[500000, 6500000], [500100, 6500000], [500000, 6500100], [500000, 6500000]]]}
        feature = {"id": "checkpoint-replay-22", "properties": {"katastri_nr": self.cadastre.id, "eraldis_nr": 22, "pindala": "3.0"}, "geometry": geometry}

        def one_page(**_kwargs):
            yield [feature]

        with organization_scope(self.organization.id):
            with (
                patch("forestry.services.metsaregister_full_import._pages", side_effect=one_page),
                patch("forestry.services.metsaregister_full_import._confirm_checkpoint_page", side_effect=RuntimeError("checkpoint storage interrupted")),
            ):
                with self.assertRaises(RuntimeError):
                    import_all_metsaregister(organization_id=str(self.organization.id), page_size=1, fetch_notifications=False)

        checkpoint = ImportCheckpoint.objects.get(source="metsaregister-full")
        self.assertEqual(checkpoint.cursor, 0)
        self.assertFalse(checkpoint.completed)

        with organization_scope(self.organization.id):
            with patch("forestry.services.metsaregister_full_import._pages", side_effect=one_page):
                import_all_metsaregister(organization_id=str(self.organization.id), page_size=1, fetch_notifications=False)

        checkpoint.refresh_from_db()
        self.assertTrue(checkpoint.completed)
        self.assertEqual(checkpoint.cursor, 1)
        self.assertEqual(CadastreSubPart.objects.filter(cadastre=self.cadastre, sub_part_code=22).count(), 1)
        self.assertEqual(ForestRegistryFeature.objects.filter(source_id="checkpoint-replay-22").count(), 1)

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

        with organization_scope(self.organization.id):
            report = import_metsaregister_delta(organization_id=str(self.organization.id), since=since, page_size=100)

        self.assertEqual(report.new_subparts, 1)
        self.assertTrue(CadastreSubPart.objects.filter(cadastre=self.cadastre, sub_part_code=13).exists())
        params = get.call_args.kwargs["params"]
        self.assertIn("registreerimise_kp >=", params["CQL_FILTER"])
        self.assertNotIn("eraldis_nr=10", params["CQL_FILTER"])

    @patch("forestry.tasks.import_metsaregister_delta", return_value=FullImportReport(features=1, new_subparts=1, notifications=2))
    def test_celery_delta_task_creates_audited_run(self, import_delta):
        result = run_metsaregister_delta_check.run(str(self.organization.id))
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
        self.client = authenticated_client(self.user)

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
        self.assertIn("DEAL", [item["kind"] for item in response.data["activities"]])
        self.assertEqual(response.data["notifications"][0]["notificationNumber"], 7002)
        self.assertEqual(response.data["registryFeatures"][0]["title"], "Eraldis 12")

    def test_map_layers_accept_viewport_and_enforce_bounded_feature_limit(self):
        response = self.client.get("/api/services/map/cadastres?bbox=24,58,26,60&limit=1")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertLessEqual(len(response.data["features"]), 1)
        response = self.client.get("/api/services/map/layers/subparts?bbox=24,58,26,60&limit=1")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertLessEqual(len(response.data["features"]), 1)
        invalid = self.client.get("/api/services/map/cadastres?bbox=invalid")
        self.assertEqual(invalid.status_code, 400)

    @patch("api.views.connection")
    def test_mvt_endpoint_requires_postgis_and_valid_tile_coordinates(self, database):
        database.vendor = "sqlite"
        unavailable = self.client.get("/api/services/map/tiles/cadastres/8/140/88.pbf")
        self.assertEqual(unavailable.status_code, 501)
        invalid = self.client.get("/api/services/map/tiles/cadastres/2/4/0.pbf")
        self.assertEqual(invalid.status_code, 400)

    @patch("api.views._map_vector_tile_bytes", return_value=b"mvt-bytes")
    @patch("api.views.connection")
    def test_mvt_endpoint_returns_vector_tile_content_type(self, database, build_tile):
        database.vendor = "postgresql"
        response = self.client.get("/api/services/map/tiles/cadastres/8/140/88.pbf?activeDeal=true")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/vnd.mapbox-vector-tile")
        self.assertEqual(response.content, b"mvt-bytes")
        self.assertEqual(build_tile.call_args.args[-4:], ("cadastres", 8, 140, 88))

    @patch("api.views.connection")
    def test_mvt_sql_uses_postgis_tile_functions_and_organization_scoped_queryset(self, database):
        from api.views import _map_vector_tile_bytes

        cursor = MagicMock()
        cursor.fetchone.return_value = (b"mvt-bytes",)
        database.cursor.return_value.__enter__.return_value = cursor
        with organization_scope(self.cadastre.organization_id):
            tile = _map_vector_tile_bytes(
                Cadastre.objects.exclude(boundary__isnull=True),
                ("id", "name", "county", "municipality", "area"),
                "boundary",
                "cadastres",
                8,
                140,
                88,
            )
        self.assertEqual(tile, b"mvt-bytes")
        sql, params = cursor.execute.call_args.args
        self.assertIn("ST_TileEnvelope", sql)
        self.assertIn("ST_AsMVTGeom", sql)
        self.assertIn("ST_AsMVT", sql)
        self.assertIn(self.cadastre.organization_id, params)
        self.assertEqual(params[-4:], [8, 140, 88, "cadastres"])

    def test_map_filters_match_customer_active_deal_and_recent_activity(self):
        owner = Owner.objects.create(id="38101010003", name="Filtriklient")
        self.cadastre.owners.add(owner)
        CadastreSubPart.objects.create(cadastre=self.cadastre, sub_part_code=13, boundary=self.cadastre.boundary)
        won = Deal.objects.create(owner=owner, sale_subject="FOREST", stage=DealStage.WON)
        won.parcels.add(self.cadastre)
        active = Deal.objects.create(owner=owner, sale_subject="LAND", stage=DealStage.NEGOTIATION)
        active.parcels.add(self.cadastre)
        OwnerLog.objects.create(owner=owner, creator=self.user, message="Kaardifiltri tegevus")

        customer = self.client.get("/api/services/map/cadastres?customer=true")
        active_response = self.client.get("/api/services/map/layers/subparts?activeDeal=true")
        recent = self.client.get("/api/services/map/cadastres?activityDays=30&dealStage=NEGOTIATION")

        self.assertEqual(customer.status_code, 200, customer.data)
        self.assertIn(self.cadastre.id, [feature["properties"]["id"] for feature in customer.data["features"]])
        self.assertEqual(active_response.status_code, 200, active_response.data)
        self.assertTrue(active_response.data["features"])
        self.assertEqual(recent.status_code, 200, recent.data)
        self.assertIn(self.cadastre.id, [feature["properties"]["id"] for feature in recent.data["features"]])


class FakeRedis:
    """Minimal Redis replacement for deterministic single-flight lock tests."""

    def __init__(self):
        self.values = {}
        self.ttls = {}

    def set(self, key, value, nx=False, ex=None):
        if nx and key in self.values:
            return None
        self.values[key] = value
        self.ttls[key] = ex
        return True

    def get(self, key):
        return self.values.get(key)

    def eval(self, script, _number_of_keys, key, *args):
        if len(args) == 1:
            if self.values.get(key) == args[0]:
                del self.values[key]
                self.ttls.pop(key, None)
                return 1
            return 0
        expected, replacement, ttl_seconds = args
        current = self.values.get(key)
        if current == expected or current is None:
            self.values[key] = replacement
            self.ttls[key] = int(ttl_seconds)
            return 1
        return 0

    def expire(self, key):
        self.values.pop(key, None)
        self.ttls.pop(key, None)


class SingleFlightLockTests(SimpleTestCase):
    @patch("forestry.services.single_flight.redis.from_url")
    def test_lock_has_ttl_releases_only_its_owner_and_recovers_after_expiry(self, redis_from_url):
        redis_client = FakeRedis()
        redis_from_url.return_value = redis_client
        first = SingleFlightLock.for_sync("cadastre-sync", "org-1", "79501:001:0001")
        second = SingleFlightLock.for_sync("cadastre-sync", "org-1", "79501:001:0001")

        self.assertTrue(first.acquire())
        self.assertEqual(redis_client.ttls[first.key], 900)
        self.assertFalse(second.acquire())
        second.release()
        self.assertEqual(redis_client.get(first.key), first.token)

        redis_client.expire(first.key)
        self.assertTrue(second.acquire())
        first.release()
        self.assertEqual(redis_client.get(second.key), second.token)

    @patch("forestry.services.single_flight.redis.from_url")
    def test_queued_dispatch_token_can_be_claimed_by_only_one_worker(self, redis_from_url):
        redis_client = FakeRedis()
        redis_from_url.return_value = redis_client
        dispatcher = SingleFlightLock.for_sync("cadastre-sync", "org-1", "79501:001:0001")
        first_worker = SingleFlightLock.for_sync("cadastre-sync", "org-1", "79501:001:0001")
        second_worker = SingleFlightLock.for_sync("cadastre-sync", "org-1", "79501:001:0001")

        self.assertTrue(dispatcher.acquire())
        first_worker.token = dispatcher.token
        second_worker.token = dispatcher.token
        self.assertTrue(first_worker.claim_queued_or_recover())
        self.assertFalse(second_worker.claim_queued_or_recover())
        self.assertTrue(redis_client.get(first_worker.key).startswith("running:"))

    @patch("forestry.tasks.import_metsaregister_delta")
    @patch("forestry.services.single_flight.redis.from_url")
    def test_delta_task_returns_already_running_without_writes(self, redis_from_url, import_delta):
        redis_client = FakeRedis()
        redis_from_url.return_value = redis_client
        existing = SingleFlightLock.for_sync("metsaregister-delta", "org-1")
        self.assertTrue(existing.acquire())

        result = run_metsaregister_delta_check.run("org-1")

        self.assertEqual(result, {"status": "already_running"})
        import_delta.assert_not_called()


class SingleFlightDispatchTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("single-flight-admin", "Single flight administrator", "very-secure-admin-password")
        self.cadastre = Cadastre.objects.create(id="79501:001:0007")
        self.client = authenticated_client(self.admin)

    @override_settings(FORESTIQ_TASKS_INLINE=False)
    def test_competing_dispatch_returns_existing_run_and_ttl_allows_recovery(self):
        redis_client = FakeRedis()
        with patch("forestry.services.single_flight.redis.from_url", return_value=redis_client), patch("forestry.tasks.run_cadastre_sync.delay") as delay:
            delay.return_value.id = "celery-single-flight-1"
            first = enqueue_cadastre_sync(self.cadastre.id, organization_id=str(self.cadastre.organization_id), source="api")
            second = enqueue_cadastre_sync(self.cadastre.id, organization_id=str(self.cadastre.organization_id), source="daily")

            self.assertFalse(first.already_running)
            self.assertTrue(second.already_running)
            self.assertEqual(second.run.id, first.run.id)
            self.assertEqual(DataSyncRun.objects.count(), 1)
            delay.assert_called_once()

            redis_client.expire(SingleFlightLock.for_sync("cadastre-sync", str(self.cadastre.organization_id), self.cadastre.id).key)
            recovered = enqueue_cadastre_sync(self.cadastre.id, organization_id=str(self.cadastre.organization_id), source="recovery")

        self.assertFalse(recovered.already_running)
        self.assertEqual(recovered.run.id, first.run.id)
        self.assertEqual(DataSyncRun.objects.count(), 1)
        self.assertEqual(delay.call_count, 2)

    @override_settings(FORESTIQ_TASKS_INLINE=False)
    def test_api_returns_already_running_instead_of_creating_a_duplicate_run(self):
        redis_client = FakeRedis()
        url = f"/api/services/admin/cadastres/{self.cadastre.id}/sync"
        with patch("forestry.services.single_flight.redis.from_url", return_value=redis_client), patch("forestry.tasks.run_cadastre_sync.delay") as delay:
            delay.return_value.id = "celery-single-flight-2"
            first = self.client.post(url)
            second = self.client.post(url)

        self.assertEqual(first.status_code, 202, first.data)
        self.assertEqual(second.status_code, 409, second.data)
        self.assertEqual(second.data["code"], "already_running")
        self.assertEqual(second.data["run"]["id"], first.data["id"])
        self.assertEqual(DataSyncRun.objects.count(), 1)


class WfsClientTests(SimpleTestCase):
    @staticmethod
    def _response(status_code: int, payload: dict[str, object], *, content: bytes | None = None, retry_after: str = "") -> Mock:
        response = Mock()
        response.status_code = status_code
        response.headers = {"Retry-After": retry_after} if retry_after else {}
        response.content = content if content is not None else json.dumps(payload).encode()
        response.json.return_value = payload
        if status_code >= 400:
            response.raise_for_status.side_effect = requests.HTTPError(f"HTTP {status_code}")
        return response

    @staticmethod
    def _policy(**overrides) -> WfsClientPolicy:
        values = {
            "max_features": 10,
            "max_payload_bytes": 1024,
            "max_retries": 2,
            "retry_backoff_seconds": 1,
            "min_request_interval_seconds": 0,
        }
        values.update(overrides)
        return WfsClientPolicy(**values)

    def test_retries_rate_limit_server_errors_and_temporary_network_failure(self):
        response = self._response(200, {"features": [{"id": "one"}]})
        request_get = Mock(
            side_effect=[
                self._response(429, {"features": []}, retry_after="3"),
                self._response(503, {"features": []}),
                requests.ConnectionError("temporary socket failure"),
                response,
            ]
        )
        sleep = Mock()
        client = WfsClient(policy=self._policy(max_retries=3), request_get=request_get, sleep=sleep)

        features = client.feature_page(base_url="https://wfs.example.test", layer="registry:layer", page_size=10)

        self.assertEqual(features, [{"id": "one"}])
        self.assertEqual(request_get.call_count, 4)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [3.0, 2.0, 4.0])

    @override_settings(FORESTIQ_WFS_PAGE_SIZE=2, FORESTIQ_WFS_MAX_FEATURES=10)
    @patch("forestry.services.external_sync.requests.get")
    def test_existing_wfs_adapter_uses_the_shared_paginated_client(self, request_get):
        request_get.side_effect = [
            self._response(200, {"features": [{"id": "one"}, {"id": "two"}]}),
            self._response(200, {"features": [{"id": "three"}]}),
        ]

        features = wfs_features(
            "https://wfs.example.test",
            "registry:layer",
            field="katastri_nr",
            value="79501:001:0001",
        )

        self.assertEqual([feature["id"] for feature in features], ["one", "two", "three"])
        self.assertEqual([call.kwargs["params"]["startIndex"] for call in request_get.call_args_list], [0, 2])

    def test_iterates_wfs_pages_with_consecutive_start_indexes(self):
        request_get = Mock(
            side_effect=[
                self._response(200, {"features": [{"id": "one"}, {"id": "two"}]}),
                self._response(200, {"features": [{"id": "three"}, {"id": "four"}]}),
                self._response(200, {"features": [{"id": "five"}]}),
            ]
        )
        client = WfsClient(policy=self._policy(), request_get=request_get)

        pages = list(client.iter_feature_pages(base_url="https://wfs.example.test", layer="registry:layer", page_size=2))

        self.assertEqual([[feature["id"] for feature in page] for page in pages], [["one", "two"], ["three", "four"], ["five"]])
        self.assertEqual([call.kwargs["params"]["startIndex"] for call in request_get.call_args_list], [0, 2, 4])

    def test_iterates_wfs_pages_from_a_saved_cursor(self):
        request_get = Mock(
            side_effect=[
                self._response(200, {"features": [{"id": "resumed-three"}, {"id": "resumed-four"}]}),
                self._response(200, {"features": []}),
            ]
        )
        client = WfsClient(policy=self._policy(), request_get=request_get)

        pages = list(
            client.iter_feature_pages(
                base_url="https://wfs.example.test",
                layer="registry:layer",
                page_size=2,
                start_index=2,
            )
        )

        self.assertEqual([[feature["id"] for feature in page] for page in pages], [["resumed-three", "resumed-four"]])
        self.assertEqual([call.kwargs["params"]["startIndex"] for call in request_get.call_args_list], [2, 4])

    def test_rejects_oversized_and_malformed_feature_collections(self):
        client = WfsClient(
            policy=self._policy(max_payload_bytes=8),
            request_get=Mock(return_value=self._response(200, {"features": []}, content=b"too-large-payload")),
        )
        with self.assertRaisesRegex(WfsClientError, "payload policy"):
            client.feature_page(base_url="https://wfs.example.test", layer="registry:layer", page_size=1)

        malformed = WfsClient(
            policy=self._policy(),
            request_get=Mock(return_value=self._response(200, {"features": ["not-an-object"]})),
        )
        with self.assertRaisesRegex(WfsClientError, "malformed feature collection"):
            malformed.feature_page(base_url="https://wfs.example.test", layer="registry:layer", page_size=1)

        bad_request_get = Mock(return_value=self._response(400, {"features": []}))
        bad_request = WfsClient(policy=self._policy(max_retries=3), request_get=bad_request_get)
        with self.assertRaisesRegex(WfsClientError, "without retry"):
            bad_request.feature_page(base_url="https://wfs.example.test", layer="registry:layer", page_size=1)
        bad_request_get.assert_called_once()


class ScheduledParimusNoticeImportTests(TestCase):
    def setUp(self):
        self.cadastre = Cadastre.objects.create(id="79501:001:0028")
        self.organization = self.cadastre.organization

    @override_settings(PARIMUS_API_URL="https://parimus.example.test", PARIMUS_API_TOKEN="unit-test-token")
    def test_periodic_notice_import_creates_an_audited_organization_run(self):
        redis_client = FakeRedis()
        with (
            patch("forestry.services.single_flight.redis.from_url", return_value=redis_client),
            patch("forestry.tasks.sync_parimus_inheritance", return_value=2) as sync,
        ):
            result = run_parimus_official_notice_import.run(str(self.organization.id))

        self.assertEqual(result, {"cadastres": 1, "notices": 2})
        sync.assert_called_once_with(self.cadastre.id, organization_id=str(self.organization.id))
        run = DataSyncRun.objects.get(source="celery:parimus-official-notices")
        self.assertEqual(run.status, DataSyncRun.Status.SUCCEEDED)
        self.assertEqual(run.result, result)
        self.assertIsNone(run.cadastre)

    def test_concurrent_periodic_notice_import_is_skipped_by_single_flight_lock(self):
        redis_client = FakeRedis()
        with patch("forestry.services.single_flight.redis.from_url", return_value=redis_client):
            existing = SingleFlightLock.for_sync("parimus-official-notices", str(self.organization.id))
            self.assertTrue(existing.acquire())
            result = run_parimus_official_notice_import.run(str(self.organization.id))

        self.assertEqual(result, {"status": "already_running"})
        self.assertFalse(DataSyncRun.objects.filter(source="celery:parimus-official-notices").exists())

    def test_beat_schedule_registers_the_periodic_notice_import(self):
        from django.conf import settings

        schedule = settings.CELERY_BEAT_SCHEDULE["forestiq-parimus-official-notices"]
        self.assertEqual(schedule["task"], "forestry.tasks.enqueue_all_organizations_parimus_official_notice_import")
        self.assertGreater(schedule["schedule"], 0)
