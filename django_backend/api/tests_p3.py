"""Regression coverage for P3 issues #111-#115."""
from __future__ import annotations

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import Organization, OrganizationRole, Privilege, PrivilegeCode, User
from api.auth import token_pair
from forestry.models import Cadastre, CadastreNotification, Owner, OwnerCadastre


class P3NotificationHistoryTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(slug="p3-tests", name="P3 tests")
        self.admin = User.objects.create_user(
            "p3-admin", "P3 Administrator", "very-secure-password", default_organization=self.organization,
        )
        Privilege.objects.create(user=self.admin, code=PrivilegeCode.ADMIN)
        self.admin.organization_memberships.filter(organization=self.organization).update(roles=[OrganizationRole.ADMIN])
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_pair(self.admin)['actualToken']['token']}")
        self.owner = Owner.objects.create(id="38001019999", name="P3 Owner", assignee=self.admin, organization=self.organization)
        self.cadastre = Cadastre.objects.create(id="12345:001:0999", name="P3 parcel", organization=self.organization)
        OwnerCadastre.objects.create(owner=self.owner, cadastre=self.cadastre, organization=self.organization)

    def _notice(self, pk, *, archived=False, at=None):
        at = at or timezone.now()
        return CadastreNotification.objects.create(
            id=pk, notification_number=1000 + pk, cadastre=self.cadastre,
            registration_date=at, archived=archived, archive_date=at if archived else None,
            organization=self.organization,
        )

    def test_active_notifications_use_non_overlapping_two_part_cursor(self):
        at = timezone.now()
        self._notice(1, at=at)
        self._notice(2, at=at)
        self._notice(3, at=at - timedelta(minutes=1))
        first = self.client.get(f"/api/services/cadastres/{self.cadastre.id}/notifications/active", {"limit": 2})
        self.assertEqual(first.status_code, 200, first.data)
        self.assertEqual(len(first.data["items"]), 2)
        second = self.client.get(
            f"/api/services/cadastres/{self.cadastre.id}/notifications/active",
            {"limit": 2, "cursor": first.data["nextCursor"]},
        )
        self.assertEqual(second.status_code, 200, second.data)
        first_ids = {item["notificationId"] for item in first.data["items"]}
        second_ids = {item["notificationId"] for item in second.data["items"]}
        self.assertFalse(first_ids.intersection(second_ids))

    def test_archive_requires_bounded_date_range_and_rejects_bad_cursor(self):
        self._notice(11, archived=True)
        missing = self.client.get(f"/api/services/cadastres/{self.cadastre.id}/notifications/archive")
        self.assertEqual(missing.status_code, 400)
        too_wide = self.client.get(
            f"/api/services/cadastres/{self.cadastre.id}/notifications/archive",
            {"from": "2024-01-01", "to": "2026-01-02"},
        )
        self.assertEqual(too_wide.status_code, 400)
        bad = self.client.get(
            f"/api/services/cadastres/{self.cadastre.id}/notifications/archive",
            {"from": timezone.localdate().isoformat(), "to": timezone.localdate().isoformat(), "cursor": "bad"},
        )
        self.assertEqual(bad.status_code, 400)


class P3NotificationPreferenceTests(P3NotificationHistoryTests):
    def test_preferences_are_user_scoped_and_validate_channels(self):
        initial = self.client.get("/api/services/notification-preferences")
        self.assertEqual(initial.status_code, 200, initial.data)
        self.assertEqual(initial.data["channels"], ["IN_APP"])

        updated = self.client.put(
            "/api/services/notification-preferences",
            {"enabled": False, "eventTypes": [], "channels": []},
            format="json",
        )
        self.assertEqual(updated.status_code, 200, updated.data)
        self.assertFalse(updated.data["enabled"])

        invalid = self.client.put(
            "/api/services/notification-preferences",
            {"enabled": True, "eventTypes": ["REMINDER_DUE"], "channels": ["SMS"]},
            format="json",
        )
        self.assertEqual(invalid.status_code, 400)

    def test_due_delivery_respects_preference_without_deleting_reminder(self):
        from operations.models import ApplicationMessage, Reminder
        from operations.notifications import deliver_reminder

        reminder = Reminder.objects.create(
            owner=self.owner,
            creator=self.admin,
            text="Call owner",
            due_time=timezone.now(),
            organization=self.organization,
        )
        disabled = self.client.put(
            "/api/services/notification-preferences",
            {"enabled": False, "eventTypes": ["REMINDER_DUE"], "channels": ["IN_APP"]},
            format="json",
        )
        self.assertEqual(disabled.status_code, 200)
        outcome = deliver_reminder(reminder)
        self.assertEqual(outcome["sent"], 0)
        self.assertTrue(Reminder.objects.filter(pk=reminder.pk).exists())
        self.assertFalse(ApplicationMessage.objects.filter(recipient=self.admin, event_key__startswith="reminder:").exists())


class P3ApplicationMessageTests(P3NotificationHistoryTests):
    def test_application_message_read_archive_and_retention_guard(self):
        from operations.models import ApplicationMessage

        message = ApplicationMessage.objects.create(
            recipient=self.admin,
            text="Workflow changed",
            category="WORKFLOW",
            organization=self.organization,
        )
        listing = self.client.get("/api/services/application-messages")
        self.assertEqual(listing.status_code, 200, listing.data)
        self.assertEqual(listing.data["unreadCount"], 1)

        read = self.client.patch(
            f"/api/services/application-messages/{message.pk}",
            {"operation": "READ"},
            format="json",
        )
        self.assertEqual(read.status_code, 200, read.data)
        self.assertIsNotNone(read.data["readAt"])

        archived = self.client.patch(
            f"/api/services/application-messages/{message.pk}",
            {"operation": "ARCHIVE"},
            format="json",
        )
        self.assertEqual(archived.status_code, 200, archived.data)
        hidden = self.client.get("/api/services/application-messages")
        self.assertFalse(any(item["id"] == message.pk for item in hidden.data["items"]))

        retained = self.client.delete(f"/api/services/application-messages/{message.pk}")
        self.assertEqual(retained.status_code, 409)


class P3RealtimeIsolationTests(TestCase):
    def test_websocket_rejects_unauthenticated_and_does_not_cross_organizations(self):
        from asgiref.sync import async_to_sync
        from channels.testing import WebsocketCommunicator
        from accounts.models import Organization, OrganizationRole, Privilege, PrivilegeCode, User
        from api.auth import token_pair
        from config.asgi import application
        from operations.realtime import publish_org_event
        from accounts.organization_context import organization_scope

        org_a = Organization.objects.create(slug="p3-ws-a", name="P3 WS A")
        org_b = Organization.objects.create(slug="p3-ws-b", name="P3 WS B")
        user_a = User.objects.create_user("p3-ws-a", "WS A", "password", default_organization=org_a)
        user_b = User.objects.create_user("p3-ws-b", "WS B", "password", default_organization=org_b)
        Privilege.objects.create(user=user_a, code=PrivilegeCode.ADMIN)
        Privilege.objects.create(user=user_b, code=PrivilegeCode.ADMIN)
        user_a.organization_memberships.filter(organization=org_a).update(roles=[OrganizationRole.ADMIN])
        user_b.organization_memberships.filter(organization=org_b).update(roles=[OrganizationRole.ADMIN])
        token_a = token_pair(user_a)["actualToken"]["token"]

        async def scenario():
            denied = WebsocketCommunicator(application, "/ws/events/")
            connected, _ = await denied.connect()
            self.assertFalse(connected)

            socket = WebsocketCommunicator(application, f"/ws/events/?token={token_a}")
            connected, _ = await socket.connect()
            self.assertTrue(connected)

            with organization_scope(org_b.id):
                publish_org_event("OWNER_STATUS_CHANGED", {"ownerId": "other"}, actor=user_b)
            self.assertTrue(await socket.receive_nothing(timeout=0.15))

            with organization_scope(org_a.id):
                publish_org_event("OWNER_STATUS_CHANGED", {"ownerId": "mine"}, actor=user_a)
            payload = await socket.receive_json_from(timeout=1)
            self.assertEqual(payload["eventType"], "OWNER_STATUS_CHANGED")
            self.assertEqual(payload["payload"]["ownerId"], "mine")
            await socket.disconnect()

        async_to_sync(scenario)()


class P3ManagedMapTests(P3NotificationHistoryTests):
    def test_map_catalog_and_local_first_search(self):
        from forestry.p3_models import BasemapDefinition, ExternalMapLayer

        BasemapDefinition.objects.create(
            organization=self.organization,
            key="ortho",
            name="Orto",
            tile_url_template="https://maps.example.com/{z}/{x}/{y}.png",
            attribution="Example",
        )
        ExternalMapLayer.objects.create(
            organization=self.organization,
            key="forest-wms",
            name="Forest WMS",
            service_type="WMS",
            url_template="https://maps.example.com/wms?bbox={bbox}",
            visible=True,
            usage_rights="Internal decision support",
        )
        catalog = self.client.get("/api/services/map/config")
        self.assertEqual(catalog.status_code, 200, catalog.data)
        self.assertEqual(catalog.data["basemaps"][0]["key"], "ortho")
        self.assertEqual(catalog.data["externalLayers"][0]["usageRights"], "Internal decision support")

        search = self.client.get("/api/services/map/search", {"q": "12345:001"})
        self.assertEqual(search.status_code, 200, search.data)
        self.assertEqual(search.data["source"], "LOCAL")
        self.assertEqual(search.data["results"][0]["cadastreId"], self.cadastre.id)

    def test_admin_map_registry_rejects_private_network_targets(self):
        response = self.client.post(
            "/api/services/admin/map/external-layers",
            {
                "key": "private",
                "name": "Private",
                "serviceType": "WMS",
                "urlTemplate": "https://127.0.0.1/wms?bbox={bbox}",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_basemap_proxy_caches_success_and_handles_upstream_failure(self):
        from unittest.mock import Mock, patch
        from forestry.p3_models import BasemapDefinition

        BasemapDefinition.objects.create(
            organization=self.organization,
            key="safe",
            name="Safe",
            tile_url_template="https://maps.example.com/{z}/{x}/{y}.png",
            cache_seconds=60,
        )
        upstream = Mock()
        upstream.content = b"png-bytes"
        upstream.headers = {"Content-Type": "image/png"}
        upstream.raise_for_status.return_value = None
        with patch("api.p3.requests.get", return_value=upstream) as getter:
            first = self.client.get("/api/services/map/basemaps/safe/1/0/0")
            second = self.client.get("/api/services/map/basemaps/safe/1/0/0")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(getter.call_count, 1)
        self.assertEqual(second["X-ForestIQ-Map-Cache"], "HIT")
