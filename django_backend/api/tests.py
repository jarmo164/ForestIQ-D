"""Regression tests for critical ForestIQ REST flows."""

import base64

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Privilege, PrivilegeCode, User
from forestry.models import Owner, OwnerStatus


class ApiAuthenticationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("caller", "Caller One", "very-secure-password")
        Privilege.objects.create(user=self.user, code=PrivilegeCode.ASSIGNED_OWNERS)
        self.client = APIClient()

    def authenticated_client(self) -> APIClient:
        encoded = base64.b64encode(b"caller:very-secure-password").decode("ascii")
        password_response = self.client.post("/api/password-login", HTTP_AUTHORIZATION=f"Basic {encoded}")
        self.assertEqual(password_response.status_code, 200)
        totp_response = self.client.post(
            "/api/services/totp",
            {"code": "000000"},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {password_response.data['token']}",
        )
        self.assertEqual(totp_response.status_code, 200, totp_response.data)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {totp_response.data['actualToken']['token']}")
        return client

    def test_password_and_development_totp_produce_compatible_token_pair(self):
        client = self.authenticated_client()
        response = client.get("/api/services/status")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "OK")

    def test_assigned_owner_user_cannot_read_someone_elses_owner(self):
        other = User.objects.create_user("other", "Other Caller", "another-secure-password")
        owner = Owner.objects.create(id="38101010001", name="Restricted owner", assignee=other)
        response = self.authenticated_client().get(f"/api/services/owners/{owner.id}")
        self.assertEqual(response.status_code, 403)

    def test_assigned_owner_user_can_update_log_for_own_owner(self):
        owner = Owner.objects.create(id="38101010002", name="Accessible owner", assignee=self.user)
        client = self.authenticated_client()
        response = client.post(f"/api/services/owners/{owner.id}/log", {"message": "Called the owner."}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["message"], "Called the owner.")


class AdminWorkflowTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin", "Administrator", "very-secure-admin-password")
        self.client = APIClient()
        self.client.force_authenticate(self.admin)
        OwnerStatus.objects.create(id="ASSIGNED", days_out_of_search=60, color_hex="c5edc8", protected=True)

    def test_admin_can_create_and_assign_owner_status(self):
        owner = Owner.objects.create(id="49001010001", name="Forest owner")
        response = self.client.post(f"/api/services/owners/{owner.id}/change-status", {"code": "ASSIGNED"}, format="json")
        self.assertEqual(response.status_code, 200)
        owner.refresh_from_db()
        self.assertEqual(owner.status, "ASSIGNED")
