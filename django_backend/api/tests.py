"""Regression tests for critical ForestIQ REST flows."""

import base64
import json
from unittest.mock import Mock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from api.auth import token_pair
from accounts.models import Organization, OrganizationMembership, OrganizationRole, Privilege, PrivilegeCode, User
from forestry.models import Cadastre, DataSyncRun, Owner, OwnerStatus
from operations.models import Contract, Deal, DealOffer, InheritanceCase, Reminder


class RenderCorsTests(TestCase):
    @override_settings(CORS_ALLOWED_ORIGINS=["https://forestiq-d-ui.onrender.com"])
    def test_render_static_client_origin_is_allowed_for_api_preflight(self):
        response = self.client.options(
            "/api/services/status",
            HTTP_ORIGIN="https://forestiq-d-ui.onrender.com",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["access-control-allow-origin"], "https://forestiq-d-ui.onrender.com")


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


class OrganizationIsolationTests(TestCase):
    """AUTH-02 negative API checks for tenant-bounded querysets and JWT claims."""

    def setUp(self):
        self.organization_a = Organization.objects.create(slug="api-org-a", name="API organization A")
        self.organization_b = Organization.objects.create(slug="api-org-b", name="API organization B")
        self.user_a = User.objects.create_user("api-org-a-user", "API organization A user", "very-secure-password", default_organization=self.organization_a)
        Privilege.objects.create(user=self.user_a, code=PrivilegeCode.OWNER_PROFILE)
        self.owner_b = Owner.objects.create(id="39901010001", name="Organization B owner", organization=self.organization_b)

    def test_user_cannot_read_an_owner_from_another_organization(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_pair(self.user_a)['actualToken']['token']}")

        response = client.get(f"/api/services/owners/{self.owner_b.id}")

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Owner.objects.filter(id=self.owner_b.id, organization=self.organization_b).exists())

    def test_jwt_organization_without_membership_is_rejected(self):
        refresh = RefreshToken.for_user(self.user_a)
        access = refresh.access_token
        access["organization_id"] = str(self.organization_b.id)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        response = client.get("/api/services/status")

        self.assertEqual(response.status_code, 401)


class AdminWorkflowTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin", "Administrator", "very-secure-admin-password")
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_pair(self.admin)['actualToken']['token']}")
        OwnerStatus.objects.create(id="ASSIGNED", days_out_of_search=60, color_hex="c5edc8", protected=True)

    def test_admin_can_create_and_assign_owner_status(self):
        owner = Owner.objects.create(id="49001010001", name="Forest owner")
        response = self.client.post(f"/api/services/owners/{owner.id}/change-status", {"code": "ASSIGNED", "version": owner.version}, format="json")
        self.assertEqual(response.status_code, 200)
        owner.refresh_from_db()
        self.assertEqual(owner.status, "ASSIGNED")


class MainParityWorkflowTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("parity-admin", "Parity administrator", "very-secure-admin-password")
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_pair(self.admin)['actualToken']['token']}")
        self.owner = Owner.objects.create(id="48001010001", name="Parity owner", assignee=self.admin)
        self.cadastre = Cadastre.objects.create(id="48001:001:0001", name="Parity parcel")
        self.owner.cadastres.add(self.cadastre)

    def test_deal_can_progress_from_evaluation_to_won_offer(self):
        created = self.client.post(
            f"/api/services/deals/owners/{self.owner.id}",
            {"saleSubject": "FOREST", "parcelIds": [self.cadastre.id], "requestEvaluation": True, "priceExpectation": "10000"},
            format="json",
        )
        self.assertEqual(created.status_code, 201, created.data)
        deal_id = created.data["id"]
        evaluation = self.client.post(f"/api/services/deals/{deal_id}/evaluations", {"status": "APPROVED", "proposedOfferPrice": "10500", "version": created.data["version"]}, format="json")
        self.assertEqual(evaluation.status_code, 200, evaluation.data)
        offer = self.client.post(f"/api/services/deals/{deal_id}/commercial/offers", {"amount": "10500", "terms": "Cash settlement", "version": evaluation.data["version"]}, format="json")
        self.assertEqual(offer.status_code, 201, offer.data)
        offer_id = offer.data["offer"]["id"]
        sent = self.client.post(f"/api/services/deals/{deal_id}/commercial/offers/send", {"offerId": offer_id, "version": offer.data["state"]["version"]}, format="json")
        self.assertEqual(sent.status_code, 200, sent.data)
        won = self.client.post(f"/api/services/deals/{deal_id}/commercial/won", {"acceptedEntryId": offer_id, "note": "Accepted", "version": sent.data["version"]}, format="json")
        self.assertEqual(won.status_code, 200, won.data)
        self.assertEqual(won.data["stage"], "WON")
        self.assertEqual(Deal.objects.get(id=deal_id).offers.get(id=offer_id).status, DealOffer.Status.ACCEPTED)
        draft = self.client.get(f"/api/services/contracts/deals/{deal_id}/draft")
        self.assertEqual(draft.status_code, 200, draft.data)
        contract = self.client.post("/api/services/contracts/generate-from-deal", {"dealId": deal_id, "version": won.data["version"], "contractNumber": "C-2026-001", "buyer": "ForestIQ buyer"}, format="json")
        self.assertEqual(contract.status_code, 201, contract.data)
        self.assertEqual(str(Contract.objects.get(id=contract.data["contractId"]).source_offer_id), offer_id)

    def test_inheritance_case_supports_heir_and_status_workflow(self):
        created = self.client.post(
            f"/api/services/inheritance/owners/{self.owner.id}",
            {"sourceNoticeNumber": "NOTICE-001", "announcementDate": "2026-08-01", "notaryName": "Test notary"},
            format="json",
        )
        self.assertEqual(created.status_code, 201, created.data)
        case_id = created.data["id"]
        heir = self.client.post(f"/api/services/inheritance/cases/{case_id}/heirs", {"displayName": "Test heir", "contactStatus": "TO_CONTACT", "version": created.data["version"]}, format="json")
        self.assertEqual(heir.status_code, 201, heir.data)
        changed = self.client.patch(f"/api/services/inheritance/cases/{case_id}/status", {"status": "IN_PROGRESS", "comment": "Contact started", "version": InheritanceCase.objects.get(id=case_id).version}, format="json")
        self.assertEqual(changed.status_code, 200, changed.data)
        self.assertEqual(changed.data["status"], "IN_PROGRESS")
        self.assertEqual(InheritanceCase.objects.get(id=case_id).heirs.count(), 1)

    def test_owner_import_preview_and_confirmed_commit_are_audited(self):
        content = b"id,name,phone\n37601010000,Imported owner,+3725550000\n37601010001,,+3725550001\n"
        upload = SimpleUploadedFile("owners.csv", content, content_type="text/csv")
        inspect = self.client.post("/api/services/owners/imports/inspect", {"file": upload}, format="multipart")
        self.assertEqual(inspect.status_code, 200, inspect.data)
        preview_file = SimpleUploadedFile("owners.csv", content, content_type="text/csv")
        preview = self.client.post("/api/services/owners/imports/preview", {"file": preview_file, "mapping": json.dumps(inspect.data["suggestedMapping"])}, format="multipart")
        self.assertEqual(preview.status_code, 200, preview.data)
        self.assertEqual(preview.data["readyCount"], 1)
        commit_file = SimpleUploadedFile("owners.csv", content, content_type="text/csv")
        commit = self.client.post("/api/services/owners/imports/commit", {"file": commit_file, "mapping": json.dumps(inspect.data["suggestedMapping"]), "confirmedSha256": preview.data["sha256"]}, format="multipart")
        self.assertEqual(commit.status_code, 201, commit.data)
        self.assertTrue(Owner.objects.filter(id="37601010000").exists())
        self.assertEqual(commit.data["createdCount"], 1)

    def test_sales_callback_creates_a_follow_up_reminder(self):
        response = self.client.post(f"/api/services/sales-workspace/owners/{self.owner.id}/outcome", {"outcome": "CALLBACK"}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIsNotNone(response.data["reminder"])
        self.assertTrue(Reminder.objects.filter(owner=self.owner, text__icontains="callback").exists())

    def test_registry_freshness_endpoint_returns_portfolio_metrics(self):
        response = self.client.get("/api/services/registry/freshness")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["totalCadastres"], 1)

    def test_integration_runs_can_be_listed_from_the_main_contract_path(self):
        DataSyncRun.objects.create(cadastre=self.cadastre, source="cadastre", status=DataSyncRun.Status.SUCCEEDED)
        response = self.client.get("/api/services/admin/integrations/CADASTRE/runs")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["source"], "cadastre")


class MembershipRoleAuthorizationTests(TestCase):
    """AUTH-03: roles must apply within the active membership, not globally."""

    def setUp(self):
        self.organization = Organization.objects.create(slug="role-org", name="Role authorization organization")
        self.viewer = User.objects.create_user("role-viewer", "Role Viewer", "very-secure-password", default_organization=self.organization)
        self.caller = User.objects.create_user("role-caller", "Role Caller", "very-secure-password", default_organization=self.organization)
        self.manager = User.objects.create_user("role-manager", "Role Manager", "very-secure-password", default_organization=self.organization)
        self.assigned_owner = Owner.objects.create(id="50001010001", name="Assigned owner", assignee=self.caller, organization=self.organization)
        self.other_owner = Owner.objects.create(id="50001010002", name="Other owner", assignee=self.manager, organization=self.organization)

        self._set_roles(self.viewer, [OrganizationRole.MEMBER, OrganizationRole.VIEWER])
        self._set_roles(self.caller, [OrganizationRole.MEMBER, OrganizationRole.CALLER])
        self._set_roles(self.manager, [OrganizationRole.MEMBER, OrganizationRole.CRM_MANAGER])

    def _set_roles(self, user, roles):
        membership = OrganizationMembership.objects.get(user=user, organization=self.organization)
        membership.set_roles(roles, oidc_managed=True)
        return membership

    def _client_for(self, user):
        membership = OrganizationMembership.objects.get(user=user, organization=self.organization)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_pair(user, membership)['actualToken']['token']}")
        return client

    def test_viewer_has_member_read_endpoint_but_not_owner_workflow_access(self):
        client = self._client_for(self.viewer)

        self.assertEqual(client.get("/api/services/status").status_code, 200)
        self.assertEqual(client.get("/api/services/owners").status_code, 403)

    def test_caller_can_read_only_its_assigned_owner_data(self):
        client = self._client_for(self.caller)

        self.assertEqual(client.get(f"/api/services/owners/{self.assigned_owner.id}").status_code, 200)
        self.assertEqual(client.get(f"/api/services/owners/{self.other_owner.id}").status_code, 403)

    def test_crm_manager_can_read_organization_owner_data(self):
        response = self._client_for(self.manager).get(f"/api/services/owners/{self.other_owner.id}")

        self.assertEqual(response.status_code, 200, response.data)

    def test_internal_token_contains_membership_roles_and_privileges(self):
        membership = OrganizationMembership.objects.get(user=self.manager, organization=self.organization)
        access_token = token_pair(self.manager, membership)["actualToken"]["token"]
        payload = json.loads(base64.urlsafe_b64decode(access_token.split(".")[1] + "=="))

        self.assertIn(OrganizationRole.CRM_MANAGER, payload["roles"])
        self.assertIn(PrivilegeCode.OWNER_PROFILE, payload["privileges"])
        self.assertEqual(payload["organization_id"], str(self.organization.id))


class ProductionLocalLoginTests(TestCase):
    @override_settings(FORESTIQ_DEVMODE=False)
    def test_password_login_is_rejected_when_local_login_is_disabled(self):
        user = User.objects.create_user("production-local", "Production Local", "very-secure-password")
        encoded = base64.b64encode(f"{user.id}:very-secure-password".encode("ascii")).decode("ascii")

        response = self.client.post("/api/password-login", HTTP_AUTHORIZATION=f"Basic {encoded}")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["detail"], "Local development login is disabled.")

    @override_settings(KEYCLOAK_OIDC_ENABLED=False, FORESTIQ_DEVMODE=False)
    def test_oidc_configuration_does_not_expose_secrets_when_disabled(self):
        response = self.client.get("/api/oidc/config")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"enabled": False, "localLoginEnabled": False})


class OidcExchangeEndpointTests(TestCase):
    @patch("api.auth.exchange_authorization_code")
    def test_exchange_returns_internal_token_with_keycloak_auth_source(self, mocked_exchange):
        organization = Organization.objects.create(slug="oidc-api-org", name="OIDC API organization")
        user = User.objects.create_user("oidc-api-user", "OIDC API user", "very-secure-password", default_organization=organization)
        membership = OrganizationMembership.objects.get(user=user, organization=organization)
        membership.set_roles([OrganizationRole.MEMBER, OrganizationRole.EVALUATOR], oidc_managed=True)
        mocked_exchange.return_value = (user, membership)

        response = self.client.post(
            "/api/oidc/exchange",
            {"code": "provider-code", "codeVerifier": "pkce-verifier", "redirectUri": "https://app.example/login", "nonce": "nonce"},
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        mocked_exchange.assert_called_once()
        payload = json.loads(base64.urlsafe_b64decode(response.data["actualToken"]["token"].split(".")[1] + "=="))
        self.assertEqual(payload["auth_source"], "keycloak")
        self.assertIn(OrganizationRole.EVALUATOR, payload["roles"])
        self.assertIn(PrivilegeCode.EVALUATION, payload["privileges"])


class OptimisticLockingTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("lock-admin", "Lock administrator", "very-secure-password")
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_pair(self.admin)['actualToken']['token']}")
        OwnerStatus.objects.create(id="LOCKED", days_out_of_search=30, color_hex="7eaf86", protected=False)
        self.owner = Owner.objects.create(id="77001010001", name="Concurrent owner", assignee=self.admin)

    def test_owner_rejects_a_stale_snapshot_without_losing_first_write(self):
        initial_version = self.owner.version
        first = self.client.post(
            f"/api/services/owners/{self.owner.id}/change-status",
            {"code": "LOCKED", "version": initial_version},
            format="json",
        )
        self.assertEqual(first.status_code, 200, first.data)
        stale = self.client.post(
            f"/api/services/owners/{self.owner.id}/change-status",
            {"code": "LOCKED", "version": initial_version},
            format="json",
        )
        self.assertEqual(stale.status_code, 409, stale.data)
        self.assertEqual(stale.data["code"], "version_conflict")
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.status, "LOCKED")
        self.assertEqual(self.owner.version, initial_version + 1)

    def test_deal_rejects_a_stale_evaluation_submission(self):
        deal = Deal.objects.create(owner=self.owner, sale_subject="FOREST", stage="EVALUATION", evaluator=self.admin)
        initial_version = deal.version
        first = self.client.post(
            f"/api/services/deals/{deal.id}/evaluations",
            {"status": "SUBMITTED", "version": initial_version},
            format="json",
        )
        self.assertEqual(first.status_code, 200, first.data)
        stale = self.client.post(
            f"/api/services/deals/{deal.id}/evaluations",
            {"status": "APPROVED", "proposedOfferPrice": "9000", "version": initial_version},
            format="json",
        )
        self.assertEqual(stale.status_code, 409, stale.data)
        deal.refresh_from_db()
        self.assertEqual(deal.evaluation_status, "SUBMITTED")
        self.assertEqual(deal.version, initial_version + 1)

    def test_inheritance_case_rejects_a_stale_status_change(self):
        inheritance_case = InheritanceCase.objects.create(owner=self.owner)
        initial_version = inheritance_case.version
        first = self.client.patch(
            f"/api/services/inheritance/cases/{inheritance_case.id}/status",
            {"status": "IN_PROGRESS", "version": initial_version},
            format="json",
        )
        self.assertEqual(first.status_code, 200, first.data)
        stale = self.client.patch(
            f"/api/services/inheritance/cases/{inheritance_case.id}/status",
            {"status": "CLOSED", "version": initial_version},
            format="json",
        )
        self.assertEqual(stale.status_code, 409, stale.data)
        inheritance_case.refresh_from_db()
        self.assertEqual(inheritance_case.status, "IN_PROGRESS")
        self.assertEqual(inheritance_case.version, initial_version + 1)

    def test_contract_rejects_a_stale_update_before_writing_history(self):
        contract = Contract.objects.create(id="LOCK-CONTRACT-001")
        payload = {
            "id": contract.id,
            "contractNumber": "LOCK-2026-001",
            "sellers": [],
            "buyer": {"name": "ForestIQ buyer"},
            "details": {"cadastres": []},
        }
        first = self.client.post("/api/services/contracts", {**payload, "version": contract.version}, format="json")
        self.assertEqual(first.status_code, 201, first.data)
        stale = self.client.post("/api/services/contracts", {**payload, "version": contract.version}, format="json")
        self.assertEqual(stale.status_code, 409, stale.data)
        contract.refresh_from_db()
        self.assertEqual(contract.version, 2)

    def test_version_is_required_for_critical_aggregate_changes(self):
        response = self.client.post(
            f"/api/services/owners/{self.owner.id}/change-status",
            {"code": "LOCKED"},
            format="json",
        )
        self.assertEqual(response.status_code, 428, response.data)
        self.assertEqual(response.data["code"], "version_required")
