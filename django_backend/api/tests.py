"""Regression tests for critical ForestIQ REST flows."""

import base64
import json
import time
from datetime import timedelta
from unittest.mock import Mock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import SimpleTestCase, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from api.auth import token_pair
from api.urls import urlpatterns
from accounts.models import Organization, OrganizationMembership, OrganizationRole, Privilege, PrivilegeCode, User
from forestry.models import Cadastre, DataSyncRun, Owner, OwnerStatus
from operations.models import CompanyProfile, Contract, ContractTemplate, Deal, DealOffer, DealStage, InheritanceCase, Reminder


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


class DashboardStatsTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(slug="dashboard-org", name="Dashboard organization")
        self.other_organization = Organization.objects.create(slug="dashboard-other", name="Other dashboard organization")
        self.admin = User.objects.create_user("dashboard-admin", "Dashboard administrator", "very-secure-admin-password", default_organization=self.organization)
        Privilege.objects.create(user=self.admin, code=PrivilegeCode.ADMIN)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_pair(self.admin)['actualToken']['token']}")
        now = timezone.now()
        self.new_owner = Owner.objects.create(id="11111:001:0001", name="New lead", status="NEW", organization=self.organization)
        self.evaluation_owner = Owner.objects.create(id="11111:001:0002", name="Evaluation lead", status="WAITS_FOR_EVALUATION", organization=self.organization)
        Owner.objects.create(id="11111:001:0003", name="Out of search", status="NEW", organization=self.organization, out_of_admin_search_from=now, out_of_admin_search_to=now + timedelta(days=1))
        Owner.objects.create(id="22222:001:0001", name="Other organization lead", status="NEW", organization=self.other_organization)
        Deal.objects.create(owner=self.new_owner, sale_subject="FOREST", stage=DealStage.NEGOTIATION, offer_valid_until=timezone.localdate() + timedelta(days=2))
        Deal.objects.create(owner=self.evaluation_owner, sale_subject="LAND", stage=DealStage.EVALUATION, offer_valid_until=timezone.localdate() - timedelta(days=1))
        Reminder.objects.create(owner=self.new_owner, creator=self.admin, text="Follow up", due_time=now + timedelta(days=2), organization=self.organization)
        Reminder.objects.create(owner=self.evaluation_owner, creator=self.admin, text="Overdue", due_time=now - timedelta(days=1), organization=self.organization)
        InheritanceCase.objects.create(owner=self.new_owner, status=InheritanceCase.Status.IN_PROGRESS, certification_deadline=timezone.localdate() + timedelta(days=1), organization=self.organization)

    def test_dashboard_stats_is_organization_scoped_and_compact(self):
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get("/api/services/admin/dashboard-stats")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["activeOwners"], 2)
        self.assertEqual(response.data["newLeads"], 1)
        self.assertEqual(response.data["evaluationPending"], 1)
        self.assertEqual(response.data["deadlines"]["overdue"], 2)
        self.assertEqual(response.data["deadlines"]["nextSevenDays"], 3)
        self.assertEqual(response.data["dealStages"][DealStage.NEGOTIATION], 1)
        self.assertEqual(response.data["dealStages"][DealStage.EVALUATION], 1)
        self.assertLessEqual(len(queries), 12, [query["sql"] for query in queries])

    def test_dashboard_stats_fixed_corpus_p95_stays_within_budget(self):
        samples = []
        for _ in range(15):
            started = time.perf_counter()
            response = self.client.get("/api/services/admin/dashboard-stats")
            samples.append((time.perf_counter() - started) * 1000)
            self.assertEqual(response.status_code, 200, response.data)
        p95_ms = sorted(samples)[-1]  # nearest-rank p95 for the fixed 15-request corpus
        print(f"DashboardStats fixed corpus: samples={len(samples)}, p95_ms={p95_ms:.2f}, query_budget=12")
        self.assertLessEqual(p95_ms, 500, f"DashboardStats p95 {p95_ms:.2f}ms exceeded the 500ms budget")


class ContractConfigurationTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(slug="contract-config", name="Contract configuration organization")
        self.other_organization = Organization.objects.create(slug="contract-config-other", name="Other contract configuration organization")
        self.admin = User.objects.create_user("contract-admin", "Contract administrator", "very-secure-admin-password", default_organization=self.organization)
        Privilege.objects.create(user=self.admin, code=PrivilegeCode.ADMIN)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_pair(self.admin)['actualToken']['token']}")

    def test_admin_can_create_update_and_isolate_company_profiles(self):
        created = self.client.post("/api/services/company-profiles", {"legalName": "ForestIQ OÜ", "registryCode": "12345678", "email": "legal@example.test", "website": "https://example.test"}, format="json")
        self.assertEqual(created.status_code, 201, created.data)
        updated = self.client.patch(f"/api/services/company-profiles/{created.data['id']}", {"version": created.data["version"], "legalName": "ForestIQ Legal OÜ"}, format="json")
        self.assertEqual(updated.status_code, 200, updated.data)
        self.assertEqual(updated.data["legalName"], "ForestIQ Legal OÜ")
        self.assertEqual(updated.data["version"], 2)
        foreign = CompanyProfile.objects.create(organization=self.other_organization, legal_name="Other OÜ")
        self.assertEqual(self.client.get(f"/api/services/company-profiles/{foreign.id}").status_code, 404)

    def test_admin_can_revise_html_template_without_losing_prior_version(self):
        profile = CompanyProfile.objects.create(organization=self.organization, legal_name="ForestIQ OÜ")
        created = self.client.post("/api/services/contract-templates", {"companyProfileId": str(profile.id), "templateKey": "forest-sale", "name": "Müügileping", "html": "<h1>Version 1 {{ company.legalName }} {{ deal.id }} {{ deal.ownerName }} {{ deal.saleSubject }}</h1>"}, format="json")
        self.assertEqual(created.status_code, 201, created.data)
        successor = self.client.patch(f"/api/services/contract-templates/{created.data['id']}", {"version": 1, "html": "<h1>Version 2 {{ company.legalName }} {{ deal.id }} {{ deal.ownerName }} {{ deal.saleSubject }}</h1>"}, format="json")
        self.assertEqual(successor.status_code, 201, successor.data)
        self.assertEqual(successor.data["version"], 2)
        original = ContractTemplate.objects.get(id=created.data["id"])
        self.assertFalse(original.is_active)
        self.assertEqual(original.html, "<h1>Version 1 {{ company.legalName }} {{ deal.id }} {{ deal.ownerName }} {{ deal.saleSubject }}</h1>")
        self.assertEqual(successor.data["supersedesId"], created.data["id"])
        active = self.client.get("/api/services/contract-templates?active=true")
        self.assertEqual(active.status_code, 200, active.data)
        self.assertEqual([item["id"] for item in active.data], [successor.data["id"]])


    def test_placeholder_catalog_and_validation_prevent_invalid_activation(self):
        catalog = self.client.get("/api/services/contract-templates/placeholders")
        self.assertEqual(catalog.status_code, 200, catalog.data)
        required = {item["key"] for item in catalog.data["placeholders"] if item["required"]}
        self.assertEqual(required, {"company.legalName", "deal.id", "deal.ownerName", "deal.saleSubject"})
        unknown = self.client.post("/api/services/contract-templates", {"templateKey": "unknown", "name": "Unknown", "html": "{{ company.legalName }} {{ deal.id }} {{ deal.ownerName }} {{ deal.saleSubject }} {{ deal.secret }}"}, format="json")
        self.assertEqual(unknown.status_code, 400, unknown.data)
        self.assertIn("unknown placeholders", unknown.data["detail"])
        incomplete = self.client.post("/api/services/contract-templates", {"templateKey": "incomplete", "name": "Incomplete", "html": "{{ company.legalName }} {{ deal.id }}"}, format="json")
        self.assertEqual(incomplete.status_code, 400, incomplete.data)
        self.assertIn("missing required placeholders", incomplete.data["detail"])

    def test_preview_renders_selected_deal_without_creating_a_contract(self):
        profile = CompanyProfile.objects.create(organization=self.organization, legal_name="ForestIQ & Sons OÜ")
        template = ContractTemplate.objects.create(
            organization=self.organization,
            company_profile=profile,
            template_key="preview",
            name="Preview template",
            html="<p>{{ company.legalName }} / {{ deal.ownerName }} / {{ deal.saleSubject }} / {{ deal.ownerName }}</p>",
            version=1,
            created_by=self.admin,
        )
        owner = Owner.objects.create(id="55555:001:0001", name="Owner <script>", organization=self.organization)
        deal = Deal.objects.create(owner=owner, sale_subject="FOREST", organization=self.organization)
        before_contracts = Contract.objects.count()
        preview = self.client.post(f"/api/services/contract-templates/{template.id}/preview", {"dealId": str(deal.id)}, format="json")
        self.assertEqual(preview.status_code, 200, preview.data)
        self.assertEqual(preview.data["templateId"], str(template.id))
        self.assertIn("ForestIQ &amp; Sons OÜ", preview.data["html"])
        self.assertIn("Owner &lt;script&gt;", preview.data["html"])
        self.assertEqual(preview.data["html"].count("Owner &lt;script&gt;"), 2)
        self.assertEqual(Contract.objects.count(), before_contracts)


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
        template = ContractTemplate.objects.create(
            organization=self.admin.default_organization,
            template_key="forest-sale",
            name="Metsamüügi leping",
            html="<h1>{{ buyer }}</h1>",
            version=1,
            created_by=self.admin,
        )
        contract = self.client.post("/api/services/contracts/generate-from-deal", {"dealId": deal_id, "version": won.data["version"], "contractNumber": "C-2026-001", "buyer": "ForestIQ buyer", "templateId": str(template.id)}, format="json")
        self.assertEqual(contract.status_code, 201, contract.data)
        saved_contract = Contract.objects.get(id=contract.data["contractId"])
        self.assertEqual(str(saved_contract.source_offer_id), offer_id)
        self.assertEqual(saved_contract.template_version, template)
        self.assertEqual(saved_contract.template_snapshot["version"], 1)
        self.assertEqual(saved_contract.template_snapshot["html"], "<h1>{{ buyer }}</h1>")
        detail = self.client.get(f"/api/services/contracts/{contract.data['contractId']}")
        self.assertEqual(detail.status_code, 200, detail.data)
        self.assertEqual(detail.data["template"]["templateId"], str(template.id))
        self.assertEqual(detail.data["template"]["html"], "<h1>{{ buyer }}</h1>")

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
        DataSyncRun.objects.create(cadastre=self.cadastre, source="cadastre", status=DataSyncRun.Status.SUCCESS)
        response = self.client.get("/api/services/admin/integrations/CADASTRE/runs")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["source"], "cadastre")

    def test_scheduled_parimus_notice_run_is_visible_in_integrations_audit(self):
        DataSyncRun.objects.create(source="celery:parimus-official-notices", status=DataSyncRun.Status.SUCCESS, result={"cadastres": 1, "notices": 2})
        response = self.client.get("/api/services/admin/integrations/PARIMUS/runs")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["source"], "celery:parimus-official-notices")
        self.assertEqual(response.data[0]["result"], {"cadastres": 1, "notices": 2})


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


class ObjectAuthorizationMatrixTests(TestCase):
    """API-04: role and tenant tests for every protected endpoint family."""

    def setUp(self):
        self.organization = Organization.objects.create(slug="matrix-org", name="Authorization matrix organization")
        self.other_organization = Organization.objects.create(slug="matrix-other-org", name="Other authorization organization")
        self.admin = User.objects.create_user("matrix-admin", "Matrix administrator", "very-secure-password", default_organization=self.organization)
        self.manager = User.objects.create_user("matrix-manager", "Matrix CRM manager", "very-secure-password", default_organization=self.organization)
        self.evaluator = User.objects.create_user("matrix-evaluator", "Matrix evaluator", "very-secure-password", default_organization=self.organization)
        self.caller = User.objects.create_user("matrix-caller", "Matrix caller", "very-secure-password", default_organization=self.organization)
        self.viewer = User.objects.create_user("matrix-viewer", "Matrix viewer", "very-secure-password", default_organization=self.organization)
        self.roles = {
            "admin": (self.admin, [OrganizationRole.MEMBER, OrganizationRole.ADMIN]),
            "manager": (self.manager, [OrganizationRole.MEMBER, OrganizationRole.CRM_MANAGER]),
            "evaluator": (self.evaluator, [OrganizationRole.MEMBER, OrganizationRole.EVALUATOR]),
            "caller": (self.caller, [OrganizationRole.MEMBER, OrganizationRole.CALLER]),
            "viewer": (self.viewer, [OrganizationRole.MEMBER, OrganizationRole.VIEWER]),
        }
        for user, roles in self.roles.values():
            OrganizationMembership.objects.get(user=user, organization=self.organization).set_roles(roles, oidc_managed=True)

        OwnerStatus.objects.create(id="MATRIX_CONTACTED", days_out_of_search=30, color_hex="4f8c6b", protected=False, organization=self.organization)
        self.caller_owner = Owner.objects.create(id="61001010001", name="Caller-owned matrix record", assignee=self.caller, organization=self.organization)
        self.manager_owner = Owner.objects.create(id="61001010002", name="CRM matrix record", assignee=self.manager, organization=self.organization)
        self.other_owner = Owner.objects.create(id="62001010001", name="Other-tenant matrix record", organization=self.other_organization)
        self.deal = Deal.objects.create(owner=self.manager_owner, sale_subject="FOREST", stage="EVALUATION", evaluator=self.evaluator, organization=self.organization)
        self.unassigned_evaluator_deal = Deal.objects.create(owner=self.manager_owner, sale_subject="FOREST", stage="EVALUATION", evaluator=self.manager, organization=self.organization)
        self.other_deal = Deal.objects.create(owner=self.other_owner, sale_subject="FOREST", stage="EVALUATION", organization=self.other_organization)

    def _client_for(self, role: str) -> APIClient:
        user, _ = self.roles[role]
        membership = OrganizationMembership.objects.get(user=user, organization=self.organization)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_pair(user, membership)['actualToken']['token']}")
        return client

    def _assert_role_statuses(self, method: str, path: str, expected: dict[str, int], payload=None):
        for role, expected_status in expected.items():
            with self.subTest(role=role, method=method, path=path):
                response = getattr(self._client_for(role), method)(path, payload, format="json") if payload is not None else getattr(self._client_for(role), method)(path)
                self.assertEqual(response.status_code, expected_status, response.data)

    def test_role_matrix_for_general_crm_evaluation_and_admin_endpoint_families(self):
        all_roles = {role: 200 for role in self.roles}
        self._assert_role_statuses("get", "/api/services/status", all_roles)
        self._assert_role_statuses(
            "get",
            "/api/services/owners",
            {"admin": 200, "manager": 200, "evaluator": 403, "caller": 200, "viewer": 403},
        )
        self._assert_role_statuses(
            "get",
            "/api/services/deals/evaluation-queue",
            {"admin": 200, "manager": 403, "evaluator": 200, "caller": 403, "viewer": 403},
        )
        self._assert_role_statuses(
            "get",
            "/api/services/admin/integrations",
            {"admin": 200, "manager": 403, "evaluator": 403, "caller": 403, "viewer": 403},
        )

    def test_owner_object_scope_matrix_covers_assigned_crm_and_cross_tenant_records(self):
        caller_path = f"/api/services/owners/{self.caller_owner.id}"
        manager_path = f"/api/services/owners/{self.manager_owner.id}"
        other_path = f"/api/services/owners/{self.other_owner.id}"
        self._assert_role_statuses(
            "get",
            caller_path,
            {"admin": 200, "manager": 200, "evaluator": 403, "caller": 200, "viewer": 403},
        )
        self._assert_role_statuses(
            "get",
            manager_path,
            {"admin": 200, "manager": 200, "evaluator": 403, "caller": 403, "viewer": 403},
        )
        self._assert_role_statuses(
            "get",
            other_path,
            {"admin": 404, "manager": 404, "evaluator": 403, "caller": 404, "viewer": 403},
        )

    def test_mutation_matrix_allows_admin_manager_and_assigned_caller_only(self):
        caller_response = self._client_for("caller").post(
            f"/api/services/owners/{self.caller_owner.id}/change-status",
            {"code": "MATRIX_CONTACTED", "version": self.caller_owner.version},
            format="json",
        )
        self.assertEqual(caller_response.status_code, 200, caller_response.data)
        caller_denied = self._client_for("caller").post(
            f"/api/services/owners/{self.manager_owner.id}/change-status",
            {"code": "MATRIX_CONTACTED", "version": self.manager_owner.version},
            format="json",
        )
        self.assertEqual(caller_denied.status_code, 403, caller_denied.data)
        manager_response = self._client_for("manager").post(
            f"/api/services/owners/{self.manager_owner.id}/change-status",
            {"code": "MATRIX_CONTACTED", "version": self.manager_owner.version},
            format="json",
        )
        self.assertEqual(manager_response.status_code, 200, manager_response.data)
        admin_response = self._client_for("admin").post(
            f"/api/services/owners/{self.caller_owner.id}/change-status",
            {"code": "MATRIX_CONTACTED", "version": caller_response.data["version"]},
            format="json",
        )
        self.assertEqual(admin_response.status_code, 200, admin_response.data)
        for role in ("evaluator", "viewer"):
            response = self._client_for(role).post(
                f"/api/services/owners/{self.caller_owner.id}/change-status",
                {"code": "MATRIX_CONTACTED", "version": admin_response.data["version"]},
                format="json",
            )
            self.assertEqual(response.status_code, 403, response.data)

    def test_evaluator_can_mutate_only_assigned_deal_and_cross_tenant_deals_are_hidden(self):
        evaluation = self._client_for("evaluator").post(
            f"/api/services/deals/{self.deal.id}/evaluations",
            {"status": "SUBMITTED", "version": self.deal.version},
            format="json",
        )
        self.assertEqual(evaluation.status_code, 200, evaluation.data)
        self.assertEqual(evaluation.data["evaluationStatus"], "SUBMITTED")
        evaluator_denied = self._client_for("evaluator").post(
            f"/api/services/deals/{self.unassigned_evaluator_deal.id}/evaluations",
            {"status": "SUBMITTED", "version": self.unassigned_evaluator_deal.version},
            format="json",
        )
        self.assertEqual(evaluator_denied.status_code, 403, evaluator_denied.data)
        for role in ("manager", "caller", "viewer"):
            response = self._client_for(role).post(
                f"/api/services/deals/{self.deal.id}/evaluations",
                {"status": "SUBMITTED", "version": evaluation.data["version"]},
                format="json",
            )
            self.assertEqual(response.status_code, 403, response.data)
        for role in ("admin", "evaluator"):
            response = self._client_for(role).post(
                f"/api/services/deals/{self.other_deal.id}/evaluations",
                {"status": "SUBMITTED", "version": self.other_deal.version},
                format="json",
            )
            self.assertEqual(response.status_code, 404, response.data)

    def test_explicit_role_matrix_contains_every_approved_role(self):
        self.assertEqual(set(self.roles), {"admin", "manager", "evaluator", "caller", "viewer"})
        self.assertEqual(OrganizationMembership.objects.filter(organization=self.organization).count(), 5)


class EndpointAuthorizationInventoryTests(SimpleTestCase):
    """API-04 guardrail: every service route must declare an authorization policy."""

    def test_every_service_endpoint_declares_a_non_public_permission_class(self):
        public_auth_routes = {"services/totp", "services/token-refresh"}
        unprotected_routes = []
        for pattern in urlpatterns:
            route = str(pattern.pattern)
            if not route.startswith("services/") or route in public_auth_routes:
                continue
            view_class = getattr(pattern.callback, "cls", None)
            permission_classes = getattr(view_class, "permission_classes", ())
            if not permission_classes or AllowAny in permission_classes:
                unprotected_routes.append(route)
        self.assertEqual(unprotected_routes, [])
