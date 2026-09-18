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
