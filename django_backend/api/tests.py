"""Regression tests for critical ForestIQ REST flows."""

import base64
import json

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Privilege, PrivilegeCode, User
from forestry.models import Cadastre, DataSyncRun, Owner, OwnerStatus
from operations.models import Contract, Deal, DealOffer, InheritanceCase, Reminder


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


class MainParityWorkflowTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("parity-admin", "Parity administrator", "very-secure-admin-password")
        self.client = APIClient()
        self.client.force_authenticate(self.admin)
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
        evaluation = self.client.post(f"/api/services/deals/{deal_id}/evaluations", {"status": "APPROVED", "proposedOfferPrice": "10500"}, format="json")
        self.assertEqual(evaluation.status_code, 200, evaluation.data)
        offer = self.client.post(f"/api/services/deals/{deal_id}/commercial/offers", {"amount": "10500", "terms": "Cash settlement"}, format="json")
        self.assertEqual(offer.status_code, 201, offer.data)
        offer_id = offer.data["offer"]["id"]
        self.assertEqual(self.client.post(f"/api/services/deals/{deal_id}/commercial/offers/send", {"offerId": offer_id}, format="json").status_code, 200)
        won = self.client.post(f"/api/services/deals/{deal_id}/commercial/won", {"acceptedEntryId": offer_id, "note": "Accepted"}, format="json")
        self.assertEqual(won.status_code, 200, won.data)
        self.assertEqual(won.data["stage"], "WON")
        self.assertEqual(Deal.objects.get(id=deal_id).offers.get(id=offer_id).status, DealOffer.Status.ACCEPTED)
        draft = self.client.get(f"/api/services/contracts/deals/{deal_id}/draft")
        self.assertEqual(draft.status_code, 200, draft.data)
        contract = self.client.post("/api/services/contracts/generate-from-deal", {"dealId": deal_id, "contractNumber": "C-2026-001", "buyer": "ForestIQ buyer"}, format="json")
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
        heir = self.client.post(f"/api/services/inheritance/cases/{case_id}/heirs", {"displayName": "Test heir", "contactStatus": "TO_CONTACT"}, format="json")
        self.assertEqual(heir.status_code, 201, heir.data)
        changed = self.client.patch(f"/api/services/inheritance/cases/{case_id}/status", {"status": "IN_PROGRESS", "comment": "Contact started"}, format="json")
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
