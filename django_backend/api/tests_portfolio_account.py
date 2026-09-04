from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import OrganizationMembership, OrganizationRole, User
from api.auth import token_pair
from forestry.models import DataSyncRun


def authenticated_client(user: User) -> APIClient:
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_pair(user)['actualToken']['token']}")
    return client


class PortfolioCompatibilityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("portfolio-admin", "Portfolio administrator", "very-secure-admin-password")
        self.client = authenticated_client(self.user)

    def test_status_ignores_forestek_one_time_runs(self):
        DataSyncRun.objects.create(source="forestek:initial", status=DataSyncRun.Status.SUCCESS, rows_processed=999)
        metsis = DataSyncRun.objects.create(
            source="metsis:portfolio",
            status=DataSyncRun.Status.PARTIAL,
            rows_processed=37,
            cursor={"index": 40, "total": 50},
            error_message="one parcel failed",
        )

        response = self.client.get("/api/services/metsis-portfolio/status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["mode"], "RECURRING_PORTFOLIO_SYNC")
        self.assertEqual(response.data["latestRun"]["id"], metsis.id)
        self.assertEqual(response.data["rowCount"], 37)
        self.assertEqual(response.data["cursor"], {"index": 40, "total": 50})
        self.assertEqual(response.data["lastError"]["error"], "one parcel failed")

    @patch("api.portfolio.dispatch_metsis_portfolio_sync")
    def test_sync_is_audited_and_permission_protected(self, dispatch):
        run = DataSyncRun.objects.create(source="metsis:portfolio")
        dispatch.return_value = SimpleNamespace(run=run, already_running=False)

        response = self.client.post("/api/services/metsis-portfolio/sync", {}, format="json")

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data["run"]["id"], run.id)
        dispatch.assert_called_once()


class AccountWorkspaceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("account-admin", "Account administrator", "very-secure-admin-password")
        membership = OrganizationMembership.objects.get(user=self.user, organization=self.user.default_organization)
        membership.set_roles([OrganizationRole.ADMIN])
        self.client = authenticated_client(self.user)

    def test_account_profile_is_structured_for_ui(self):
        response = self.client.get("/api/services/account")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["id"], self.user.id)
        self.assertEqual(response.data["organization"]["id"], str(self.user.default_organization_id))
        self.assertIn(OrganizationRole.ADMIN, response.data["roles"])
        self.assertIn("ADMIN", response.data["privileges"])
        self.assertIn("security", response.data)
